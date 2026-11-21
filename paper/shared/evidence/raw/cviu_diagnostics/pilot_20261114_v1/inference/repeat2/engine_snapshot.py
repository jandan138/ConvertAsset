#!/usr/bin/env python3
"""Run real VLM predictions for GRScenes grounding records.

This script is the model-backed counterpart to
`generate_projection_center_baseline_predictions.py`. It reads projected
scoring records, calls an explicit VLM backend, and writes `predictions.jsonl`
records that can be consumed by `score_grounding.py`.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import mimetypes
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from urllib import error, parse, request


PROJECT_ROOT = Path(__file__).resolve().parents[5]
RAW_DIR = PROJECT_ROOT / "paper/shared/evidence/raw/grscene_vlm_grounding"
DEFAULT_PROJECTION_REPORT = RAW_DIR / "target_projection_qa_report.json"
DEFAULT_OUTPUT = RAW_DIR / "predictions.jsonl"
MODEL_CLAIM_BOUNDARY = "model_prediction_scores_require_model_provenance_review"


class VLMEngine(Protocol):
    def generate(self, messages: list[dict[str, Any]]) -> str: ...


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return "unknown"


def _git_status_porcelain() -> list[str]:
    try:
        tracked_output = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        untracked_output = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(PROJECT_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ["unknown"]
    lines = [line for line in tracked_output.splitlines() if line]
    untracked_count = len([line for line in untracked_output.splitlines() if line])
    if untracked_count:
        lines.append(f"?? {untracked_count} untracked files omitted from provenance")
    return lines


def _finite_point(values: Any) -> list[float] | None:
    if not isinstance(values, list | tuple) or len(values) != 2:
        return None
    try:
        point = [float(values[0]), float(values[1])]
    except (TypeError, ValueError):
        return None
    if any(not math.isfinite(value) for value in point):
        return None
    return point


S2_INTERACTION_ACTIONS = {
    "backpack": "open the backpack to fetch an item",
    "bottle": "pick up the bottle",
    "clock": "read the time from the clock",
    "cup": "grasp the cup",
    "faucet": "turn on the faucet",
    "picture": "straighten the picture frame",
    "pillow": "move the pillow",
    "plate": "clear the plate",
}
DEFAULT_S2_ACTION = "interact with the {category}"


def build_prompt(
    record: dict[str, Any],
    *,
    coordinate_frame: str = "normalized_1000",
    response_format: str = "json",
    prompt_type: str = "s1_point",
) -> str:
    image = record.get("image") or {}
    target = record.get("target") or {}
    category = str(target.get("category") or "target object")
    width = image.get("width", "unknown")
    height = image.get("height", "unknown")
    if coordinate_frame == "pixel":
        coordinate_instruction = (
            "The point should be near the visual center of the target object in raw pixel coordinates. "
            "Use x from the left image edge and y from the top image edge."
        )
    elif coordinate_frame == "normalized_1000":
        coordinate_instruction = (
            "The point should be near the visual center of the target object in a normalized 0-1000 coordinate frame. "
            "In this frame, x=0 is the left image edge, x=1000 is the right image edge, "
            "y=0 is the top image edge, and y=1000 is the bottom image edge."
        )
    else:
        raise ValueError(f"Unsupported coordinate_frame: {coordinate_frame}")
    if response_format == "json":
        response_instruction = (
            "Return only a JSON object with this exact shape:\n"
            '{"point_xy": [x, y], "answer": "target category"}\n'
        )
    elif response_format == "structured_text":
        response_instruction = (
            "Return exactly two plain-text lines and no code block:\n"
            "Point: x, y\n"
            "Answer: target category\n"
        )
    else:
        raise ValueError(f"Unsupported response_format: {response_format}")
    if prompt_type == "s1_point":
        task_instruction = (
            "You are evaluating a rendered indoor scene. Locate the target object.\n"
            f"Target category: {category}\n"
        )
    elif prompt_type == "s2_interaction":
        action = S2_INTERACTION_ACTIONS.get(category.lower(), DEFAULT_S2_ACTION.format(category=category))
        task_instruction = (
            "You are evaluating a rendered indoor scene for a household robot.\n"
            f"The robot must {action}. Point to the object it should interact with.\n"
            f"Target category: {category}\n"
        )
    else:
        raise ValueError(f"Unsupported prompt_type: {prompt_type}")
    return (
        f"{task_instruction}"
        f"Image size: {width} x {height} pixels.\n"
        f"{response_instruction}"
        f"{coordinate_instruction} "
        "Do not include markdown, explanation, or extra keys."
    )


def build_messages(record: dict[str, Any], prompt: str) -> list[dict[str, Any]]:
    image = record.get("image") or {}
    image_path = image.get("path")
    if not image_path:
        raise ValueError(f"record missing image.path: {record.get('sample_id')}")
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image": str(image_path)},
            ],
        }
    ]


_STRUCTURED_NUMBER_LINE = re.compile(
    r"(?im)^\s*(?:Point\s*:\s*)?\[?\s*"
    r"(-?\d+(?:\.\d+)?)\s*,\s*"
    r"(-?\d+(?:\.\d+)?)"
    r"(?:\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?))?"
    r"\s*\]?\s*$"
)


def _point_from_structured_number_match(match: re.Match[str]) -> list[float] | None:
    values = [group for group in match.groups() if group is not None]
    if len(values) == 2:
        return _finite_point(values)
    if len(values) == 4:
        box = _finite_point(
            [
                (float(values[0]) + float(values[2])) / 2.0,
                (float(values[1]) + float(values[3])) / 2.0,
            ]
        )
        return box
    return None


def _structured_answer_candidate(line: str) -> str | None:
    cleaned = line.strip().strip("`").strip()
    if not cleaned or "addcriterion" in cleaned.lower():
        return None
    if _STRUCTURED_NUMBER_LINE.match(cleaned):
        return None
    if re.search(r"[A-Za-z]", cleaned) is None:
        return None
    return cleaned


_MOLMO_POINT_TAG = re.compile(
    r'<points?\s+[^>]*?x\s*=\s*"?(-?\d+(?:\.\d+)?)"?\s+y\s*=\s*"?(-?\d+(?:\.\d+)?)"?[^>]*?/?>',
    re.IGNORECASE,
)


def _molmo_point_fallback(text: str) -> list[float] | None:
    """Extract Molmo-style <point x y> tags (0-100 frame) into 0-1000 floats."""
    match = _MOLMO_POINT_TAG.search(text)
    if not match:
        return None
    point = _finite_point([float(match.group(1)) * 10.0, float(match.group(2)) * 10.0])
    return point


def _parse_structured_prediction_text(text: str) -> dict[str, Any]:
    point = None
    answer = None
    point_match = _STRUCTURED_NUMBER_LINE.search(text)
    if point_match:
        point = _point_from_structured_number_match(point_match)
    if point is None:
        point = _molmo_point_fallback(text)
    answer_match = re.search(r"(?im)^\s*Answer\s*:\s*(.+?)\s*$", text)
    if answer_match:
        answer = _structured_answer_candidate(answer_match.group(1))
    if not answer:
        for line in text.splitlines():
            candidate = _structured_answer_candidate(line)
            if candidate:
                answer = candidate
                break
    return {
        "parse_status": "parsed" if point is not None or answer else "parse_failed",
        "point_xy": point,
        "answer": answer or None,
    }


def parse_prediction_text(text: str, *, response_format: str = "json") -> dict[str, Any]:
    if response_format == "structured_text":
        return _parse_structured_prediction_text(text)
    if response_format != "json":
        raise ValueError(f"Unsupported response_format: {response_format}")

    parsed_obj = None
    for match in re.finditer(r"\{[\s\S]*?\}", text):
        try:
            candidate = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            parsed_obj = candidate
            break
    if parsed_obj is None:
        return {"parse_status": "parse_failed", "point_xy": None, "answer": None}

    point = _finite_point(parsed_obj.get("point_xy"))
    answer = parsed_obj.get("answer")
    if answer is not None:
        answer = str(answer).strip()
    return {
        "parse_status": "parsed" if point is not None or answer else "parsed_empty",
        "point_xy": point,
        "answer": answer or None,
    }


def _image_with_hash(record: dict[str, Any]) -> dict[str, Any]:
    image = dict(record.get("image") or {})
    path = image.get("path")
    if path and Path(path).exists():
        image["hash_sha256"] = _sha256_file(Path(path))
    else:
        image["hash_sha256"] = None
    return image


def run_predictions(
    records: list[dict[str, Any]],
    engine: VLMEngine,
    *,
    backend: str,
    model_checkpoint: str,
    temperature: float,
    max_new_tokens: int,
    coordinate_frame: str = "normalized_1000",
    response_format: str = "json",
    prompt_type: str = "s1_point",
) -> list[dict[str, Any]]:
    rows = []
    for record in records:
        prompt = build_prompt(
            record,
            coordinate_frame=coordinate_frame,
            response_format=response_format,
            prompt_type=prompt_type,
        )
        messages = build_messages(record, prompt)
        raw_text = engine.generate(messages)
        parsed = parse_prediction_text(raw_text, response_format=response_format)
        row = dict(record)
        row["claim_boundary"] = MODEL_CLAIM_BOUNDARY
        row["image"] = _image_with_hash(record)
        row["prompt"] = {
            "type": prompt_type,
            "coordinate_frame": coordinate_frame,
            "response_format": response_format,
            "text": prompt,
        }
        row["prediction"] = {
            "backend": backend,
            "coordinate_frame_requested": coordinate_frame,
            "point_xy": parsed["point_xy"],
            "answer": parsed["answer"],
            "parse_status": parsed["parse_status"],
            "raw_text": raw_text,
        }
        row["model_checkpoint"] = model_checkpoint
        row["decoding"] = {"temperature": temperature, "max_new_tokens": max_new_tokens}
        row["prediction_generated_at_utc"] = _utc_now()
        rows.append(row)
    return rows


def write_predictions(
    rows: list[dict[str, Any]],
    out: Path,
    *,
    projection_report: Path,
    backend: str,
    model_checkpoint: str,
    coordinate_frame: str = "normalized_1000",
    response_format: str = "json",
    prompt_type: str = "s1_point",
    argv: list[str] | None = None,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    script_path = Path(__file__).resolve()
    metadata = {
        "schema_version": 1,
        "status": "vlm_predictions",
        "prediction_count": len(rows),
        "backend": backend,
        "model_checkpoint": model_checkpoint,
        "coordinate_frame": coordinate_frame,
        "response_format": response_format,
        "prompt_type": prompt_type,
        "claim_boundary": MODEL_CLAIM_BOUNDARY,
        "generated_at_utc": _utc_now(),
        "input_projection_report": {
            "path": str(projection_report),
            "hash_sha256": _sha256_file(projection_report),
        },
        "output_jsonl": {"path": str(out), "hash_sha256": _sha256_file(out)},
        "runner_provenance": {
            "command": [sys.executable, str(script_path), *(argv if argv is not None else sys.argv[1:])],
            "script_path": str(script_path),
            "script_hash_sha256": _sha256_file(script_path),
            "git_commit": _git_commit(),
            "git_status_porcelain": _git_status_porcelain(),
        },
    }
    out.with_suffix(out.suffix + ".metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


class OpenAICompatibleEngine:
    def __init__(
        self,
        *,
        model: str,
        api_base_url: str,
        api_key_env: str,
        temperature: float,
        max_new_tokens: int,
        timeout_seconds: int = 120,
        max_retries: int = 2,
    ):
        self.model = model
        self.api_base_url = self._validate_api_base_url(api_base_url)
        self.api_key_env = api_key_env
        self.api_key = os.environ.get(api_key_env)
        if not self.api_key:
            raise ValueError(f"Environment variable {api_key_env} is not set")
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def _validate_api_base_url(self, api_base_url: str) -> str:
        parsed = parse.urlparse(api_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("api_base_url must be a valid http(s) URL")
        return api_base_url.rstrip("/")

    def _encode_image_as_data_url(self, image_path: str) -> str:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        encoded = base64.b64encode(Path(image_path).read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _payload(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        converted_messages = []
        for message in messages:
            content = []
            for item in message.get("content", []):
                if item.get("type") == "text":
                    content.append({"type": "text", "text": item["text"]})
                elif item.get("type") == "image_url":
                    source = item.get("image") or (item.get("image_url") or {}).get("url")
                    if not source:
                        raise ValueError("image_url item missing image source")
                    content.append({"type": "image_url", "image_url": {"url": self._encode_image_as_data_url(source)}})
            converted_messages.append({"role": message["role"], "content": content})
        return {
            "model": self.model,
            "messages": converted_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_new_tokens,
        }

    def _extract_text(self, response: dict[str, Any]) -> str:
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Malformed chat completion response: {response!r}") from exc
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                    text_parts.append(item["text"])
            if text_parts:
                return "".join(text_parts)
        raise RuntimeError(f"Malformed chat completion response: {response!r}")

    def _request_once(self, req: request.Request) -> dict[str, Any]:
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def generate(self, messages: list[dict[str, Any]]) -> str:
        body = json.dumps(self._payload(messages)).encode("utf-8")
        req = request.Request(
            f"{self.api_base_url}/v1/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._request_once(req)
                return self._extract_text(response)
            except error.HTTPError as exc:
                last_error = exc
                transient = exc.code == 429 or 500 <= exc.code < 600
                if transient and attempt < self.max_retries:
                    time.sleep(0.2)
                    continue
                body_text = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"API request failed with HTTP {exc.code}: {body_text}") from exc
            except error.URLError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(0.2)
                    continue
        raise RuntimeError(f"API request failed: {last_error}") from last_error


class LocalHFQwenEngine:
    def __init__(
        self,
        *,
        model_path: str,
        temperature: float,
        max_new_tokens: int,
        dtype: str = "bfloat16",
        attn_implementation: str = "eager",
        device_map: str = "auto",
    ):
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype=getattr(torch, dtype),
            attn_implementation=attn_implementation,
            device_map=device_map,
            trust_remote_code=True,
        )
        self.processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

    def generate(self, messages: list[dict[str, Any]]) -> str:
        from qwen_vl_utils import process_vision_info

        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = inputs.to(self.model.device)
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            do_sample=self.temperature != 0.0,
        )
        generated_ids_trimmed = [
            out_ids[len(in_ids) :]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        return self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]


class LocalHFGenericEngine:
    """Generic local HF multimodal backend (Qwen3-VL, InternVL, etc.).

    Uses AutoProcessor + AutoModelForImageTextToText so newer VLM families work
    without a dedicated engine class. Images are passed as file paths through
    the chat template and loaded with PIL before the processor call.
    """

    def __init__(
        self,
        *,
        model_path: str,
        temperature: float,
        max_new_tokens: int,
        dtype: str = "bfloat16",
        attn_implementation: str = "eager",
        device_map: str = "auto",
        model_class: str | None = None,
    ):
        import torch
        import transformers

        if model_class:
            cls = getattr(transformers, model_class, None)
            if cls is None:
                raise ValueError(f"transformers has no class {model_class}; installed={transformers.__version__}")
        else:
            cls = getattr(transformers, "AutoModelForImageTextToText", None)
        if cls is None:
            raise ValueError("No multimodal auto model class available")
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.model = cls.from_pretrained(
            model_path,
            torch_dtype=getattr(torch, dtype),
            attn_implementation=attn_implementation,
            device_map=device_map,
            trust_remote_code=True,
        )
        self.processor = transformers.AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

    def generate(self, messages: list[dict[str, Any]]) -> str:
        from PIL import Image

        converted = []
        image_paths: list[str] = []
        for message in messages:
            content = []
            for item in message.get("content", []):
                if item.get("type") == "text":
                    content.append({"type": "text", "text": item["text"]})
                elif item.get("type") == "image_url":
                    source = item.get("image") or (item.get("image_url") or {}).get("url")
                    if not source:
                        raise ValueError("image_url item missing image source")
                    content.append({"type": "image", "image": source})
                    image_paths.append(str(source))
            converted.append({"role": message["role"], "content": content})
        text = self.processor.apply_chat_template(converted, tokenize=False, add_generation_prompt=True)
        images = [Image.open(path).convert("RGB") for path in image_paths]
        inputs = self.processor(
            text=[text],
            images=images or None,
            padding=True,
            return_tensors="pt",
        )
        target_device = getattr(self.model, "device", None)
        if target_device is not None and hasattr(inputs, "to"):
            inputs = inputs.to(target_device)
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            do_sample=self.temperature != 0.0,
        )
        input_ids = inputs["input_ids"]
        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(input_ids, generated_ids)
        ]
        return self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]


class LocalInternVLChatEngine:
    """InternVLChatModel (trust_remote_code) backend.

    transformers 5.x compat shims required for the InternVL3 remote code:
    1. The vendored `modeling_intern_vit.py` computes drop-path rates with
       `torch.linspace(...).item()` which breaks under meta-tensor init; the
       local HF-cache blob must be patched to numpy once (see experiment
       records 2026-09-13).
    2. The remote class does not initialize the `all_tied_weights_keys`
       attribute that transformers 5.x touches after loading; patched here via
       an __init__ wrapper.
    Images are resized to a single 448x448 tile (no dynamic tiling) with
    ImageNet normalization, matching the InternVL default chat path.
    """

    IMAGENET_MEAN = (0.485, 0.456, 0.406)
    IMAGENET_STD = (0.229, 0.224, 0.225)

    def __init__(
        self,
        *,
        model_path: str,
        temperature: float,
        max_new_tokens: int,
        dtype: str = "bfloat16",
        device: str = "cuda",
        input_size: int = 448,
    ):
        import torch
        from transformers import AutoModel, AutoTokenizer
        from transformers.dynamic_module_utils import get_class_from_dynamic_module

        cls = get_class_from_dynamic_module("modeling_internvl_chat.InternVLChatModel", model_path)
        orig_init = cls.__init__

        def _init_compat(instance, config, *a, **k):
            orig_init(instance, config, *a, **k)
            if not hasattr(instance, "all_tied_weights_keys"):
                instance.all_tied_weights_keys = {}

        cls.__init__ = _init_compat
        self.model = AutoModel.from_pretrained(
            model_path,
            torch_dtype=getattr(torch, dtype),
            trust_remote_code=True,
            low_cpu_mem_usage=False,
        ).to(device)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.input_size = input_size

    def _load_pixel_values(self, image_path: str):
        import torch
        import torchvision.transforms as T
        from PIL import Image

        img = Image.open(image_path).convert("RGB").resize((self.input_size, self.input_size))
        transform = T.Compose(
            [T.ToTensor(), T.Normalize(mean=self.IMAGENET_MEAN, std=self.IMAGENET_STD)]
        )
        return transform(img).unsqueeze(0).to(torch.bfloat16).cuda()

    def generate(self, messages: list[dict[str, Any]]) -> str:
        text_parts: list[str] = []
        image_paths: list[str] = []
        for message in messages:
            for item in message.get("content", []):
                if item.get("type") == "text":
                    text_parts.append(item["text"])
                elif item.get("type") == "image_url":
                    source = item.get("image") or (item.get("image_url") or {}).get("url")
                    if not source:
                        raise ValueError("image_url item missing image source")
                    image_paths.append(str(source))
        if len(image_paths) != 1:
            raise ValueError(f"LocalInternVLChatEngine expects exactly one image, got {len(image_paths)}")
        pixel_values = self._load_pixel_values(image_paths[0])
        generation_config = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": self.temperature != 0.0,
        }
        if self.temperature != 0.0:
            generation_config["temperature"] = self.temperature
        return self.model.chat(
            self.tokenizer,
            pixel_values,
            "\n".join(text_parts),
            generation_config,
        )


class LocalMolmoEngine:
    """Molmo-7B (Ai2) backend via trust_remote_code generate_from_batch.

    Molmo natively emits <point x=".." y=".."/> tags on a 0-100 normalized
    frame; `_molmo_point_fallback` in the parser rescales them to 0-1000.
    """

    def __init__(
        self,
        *,
        model_path: str,
        temperature: float,
        max_new_tokens: int,
        dtype: str = "bfloat16",
        device_map: str = "auto",
    ):
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor
        from transformers.dynamic_module_utils import get_class_from_dynamic_module

        cls = get_class_from_dynamic_module("modeling_molmo.MolmoForCausalLM", model_path)
        orig_init = cls.__init__

        def _init_compat(instance, config, *a, **k):
            orig_init(instance, config, *a, **k)
            if not hasattr(instance, "all_tied_weights_keys"):
                instance.all_tied_weights_keys = {}

        cls.__init__ = _init_compat
        orig_tie = cls.tie_weights

        def _tie_compat(instance, *a, **k):
            k.pop("missing_keys", None)
            k.pop("recompute_mapping", None)
            return orig_tie(instance, *a, **k)

        cls.tie_weights = _tie_compat
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=getattr(torch, dtype),
            device_map=device_map,
            trust_remote_code=True,
        )
        self.processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

    def generate(self, messages: list[dict[str, Any]]) -> str:
        from PIL import Image
        from transformers import GenerationConfig

        text_parts: list[str] = []
        image_paths: list[str] = []
        for message in messages:
            for item in message.get("content", []):
                if item.get("type") == "text":
                    text_parts.append(item["text"])
                elif item.get("type") == "image_url":
                    source = item.get("image") or (item.get("image_url") or {}).get("url")
                    if not source:
                        raise ValueError("image_url item missing image source")
                    image_paths.append(str(source))
        images = [Image.open(path).convert("RGB") for path in image_paths]
        inputs = self.processor.process(images=images, text="\n".join(text_parts))
        model_dtype = getattr(self.model, "dtype", None)
        converted_inputs = {}
        for key, value in inputs.items():
            tensor = value
            if hasattr(tensor, "to"):
                if model_dtype is not None and getattr(tensor, "is_floating_point", lambda: False)():
                    tensor = tensor.to(self.model.device, model_dtype)
                else:
                    tensor = tensor.to(self.model.device)
            converted_inputs[key] = tensor.unsqueeze(0) if hasattr(tensor, "unsqueeze") else tensor
        inputs = converted_inputs
        generation_config = GenerationConfig(
            max_new_tokens=self.max_new_tokens,
            stop_strings="<|endoftext|>",
            do_sample=self.temperature != 0.0,
            temperature=self.temperature if self.temperature != 0.0 else None,
            use_cache=True,
        )
        output = self.model.generate_from_batch(
            inputs,
            generation_config,
            tokenizer=self.processor.tokenizer,
        )
        generated = output[0, inputs["input_ids"].size(1):]
        return self.processor.tokenizer.decode(generated, skip_special_tokens=True)


class LocalGemma4Engine:
    def __init__(
        self,
        *,
        model_path: str,
        temperature: float,
        max_new_tokens: int,
        dtype: str = "bfloat16",
        attn_implementation: str = "eager",
        device_map: str = "auto",
    ):
        self._prepare_unsloth_runtime(model_path)
        import torch
        import transformers

        model_class = getattr(transformers, "AutoModelForImageTextToText", None) or getattr(
            transformers, "Gemma4ForConditionalGeneration", None
        )
        if model_class is None:
            version = getattr(transformers, "__version__", "unknown")
            raise ValueError(f"Gemma4 backend requires multimodal Gemma4 transformers support; installed={version}")
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.model = model_class.from_pretrained(
            model_path,
            torch_dtype=getattr(torch, dtype),
            attn_implementation=attn_implementation,
            device_map=device_map,
            trust_remote_code=True,
        )
        self.processor = transformers.AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

    @staticmethod
    def _requires_unsloth_runtime(model_path: str) -> bool:
        model_name = str(model_path)
        if "unsloth" in model_name.lower():
            return True
        config_path = Path(model_path).resolve() / "config.json"
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        if config.get("unsloth_fixed") is True:
            return True
        quantization_config = config.get("quantization_config")
        if not isinstance(quantization_config, dict):
            return False
        quant_method = str(quantization_config.get("quant_method", "")).lower()
        load_in_4bit = bool(quantization_config.get("load_in_4bit") or quantization_config.get("_load_in_4bit"))
        return quant_method == "bitsandbytes" and load_in_4bit

    def _prepare_unsloth_runtime(self, model_path: str) -> None:
        if not self._requires_unsloth_runtime(model_path):
            return
        os.environ.setdefault("UNSLOTH_COMPILE_LOCATION", "/tmp/convertasset_vlm_unsloth_cache")
        try:
            import unsloth  # noqa: F401
        except ImportError as exc:
            raise ValueError("Gemma4 Unsloth checkpoint requires unsloth in the active Python environment") from exc

    def _convert_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        converted = []
        for message in messages:
            content = []
            for item in message.get("content", []):
                if item.get("type") == "text":
                    content.append({"type": "text", "text": item["text"]})
                elif item.get("type") == "image_url":
                    source = item.get("image") or (item.get("image_url") or {}).get("url")
                    if not source:
                        raise ValueError("image_url item missing image source")
                    content.append({"type": "image", "image": source})
            converted.append({"role": message["role"], "content": content})
        return converted

    def generate(self, messages: list[dict[str, Any]]) -> str:
        inputs = self.processor.apply_chat_template(
            self._convert_messages(messages),
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            add_generation_prompt=True,
        )
        target_device = getattr(self.model, "device", None)
        if target_device is not None and hasattr(inputs, "to"):
            inputs = inputs.to(target_device)
        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
            do_sample=self.temperature != 0.0,
        )
        generated_ids_trimmed = [
            out_ids[len(in_ids) :]
            for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)
        ]
        return self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]


def build_engine(args: argparse.Namespace) -> VLMEngine:
    if args.model_backend == "openai_compatible":
        if not args.api_base_url or not args.api_key_env:
            raise ValueError("--api-base-url and --api-key-env are required for openai_compatible")
        return OpenAICompatibleEngine(
            model=args.model_path,
            api_base_url=args.api_base_url,
            api_key_env=args.api_key_env,
            temperature=args.temperature,
            max_new_tokens=args.max_new_tokens,
            timeout_seconds=args.api_timeout_seconds,
            max_retries=args.api_max_retries,
        )
    if args.model_backend == "local_hf_qwen":
        return LocalHFQwenEngine(
            model_path=args.model_path,
            temperature=args.temperature,
            max_new_tokens=args.max_new_tokens,
            dtype=args.dtype,
            attn_implementation=args.attn_implementation,
            device_map=args.device_map,
        )
    if args.model_backend == "local_hf_generic":
        return LocalHFGenericEngine(
            model_path=args.model_path,
            temperature=args.temperature,
            max_new_tokens=args.max_new_tokens,
            dtype=args.dtype,
            attn_implementation=args.attn_implementation,
            device_map=args.device_map,
            model_class=args.model_class,
        )
    if args.model_backend == "local_internvl_chat":
        return LocalInternVLChatEngine(
            model_path=args.model_path,
            temperature=args.temperature,
            max_new_tokens=args.max_new_tokens,
            dtype=args.dtype,
        )
    if args.model_backend == "local_molmo":
        return LocalMolmoEngine(
            model_path=args.model_path,
            temperature=args.temperature,
            max_new_tokens=args.max_new_tokens,
            dtype=args.dtype,
            device_map=args.device_map,
        )
    if args.model_backend == "local_gemma4_multimodal":
        return LocalGemma4Engine(
            model_path=args.model_path,
            temperature=args.temperature,
            max_new_tokens=args.max_new_tokens,
            dtype=args.dtype,
            attn_implementation=args.attn_implementation,
            device_map=args.device_map,
        )
    raise ValueError(f"Unsupported model backend: {args.model_backend}")


def _selected_records(report: dict[str, Any], *, limit: int | None, sample_ids: list[str] | None) -> list[dict[str, Any]]:
    records = list(report.get("scoring_records", []))
    if sample_ids:
        wanted = set(sample_ids)
        records = [record for record in records if record.get("sample_id") in wanted]
    if limit is not None:
        records = records[:limit]
    return records


def _canonical_predictions_paths(projection_report: Path) -> set[Path]:
    return {
        projection_report.parent / "predictions.jsonl",
        projection_report.parent / "stress_predictions.jsonl",
    }


def _is_canonical_predictions_path(out: Path, projection_report: Path) -> bool:
    out_resolved = out.resolve()
    return any(out_resolved == path.resolve() for path in _canonical_predictions_paths(projection_report))


def _metadata_sidecar_path(out: Path) -> Path:
    return out.with_suffix(out.suffix + ".metadata.json")


def validate_run_plan(
    records: list[dict[str, Any]],
    *,
    out: Path,
    projection_report: Path,
    limit: int | None,
    sample_ids: list[str] | None,
    force: bool,
    available_sample_ids: set[str] | None = None,
) -> dict[str, Any]:
    blockers = []
    missing_images = []
    missing_sample_ids: list[str] = []
    if not records:
        blockers.append("empty_record_selection")
    if limit is not None and limit < 0:
        blockers.append("negative_limit")
    if sample_ids and available_sample_ids is not None:
        missing_sample_ids = sorted(set(sample_ids) - available_sample_ids)
        if missing_sample_ids:
            blockers.append("requested_sample_ids_missing")
    for record in records:
        image = record.get("image") if isinstance(record.get("image"), dict) else {}
        image_path = image.get("path")
        if not image_path or not Path(image_path).exists():
            missing_images.append({"sample_id": record.get("sample_id"), "path": image_path})
    if missing_images:
        blockers.append("missing_image_files")
    if (limit is not None or sample_ids) and _is_canonical_predictions_path(out, projection_report) and not force:
        blockers.append("limited_run_requires_noncanonical_output_or_force")
    if out.exists() and not force:
        blockers.append("output_exists_requires_force")
    if _metadata_sidecar_path(out).exists() and not force:
        blockers.append("output_metadata_exists_requires_force")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "record_count": len(records),
        "missing_images": missing_images,
        "missing_sample_ids": missing_sample_ids,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--projection-report", type=Path, default=DEFAULT_PROJECTION_REPORT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model-backend", choices=["openai_compatible", "local_hf_qwen", "local_gemma4_multimodal", "local_hf_generic", "local_internvl_chat", "local_molmo"])
    parser.add_argument("--model-class", help="Optional transformers class name for local_hf_generic (e.g. Qwen3VLForConditionalGeneration).")
    parser.add_argument("--model-path", help="Local model path or API model name.")
    parser.add_argument("--api-base-url")
    parser.add_argument("--api-key-env")
    parser.add_argument("--api-timeout-seconds", type=int, default=120)
    parser.add_argument("--api-max-retries", type=int, default=2)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, help="Optional RNG seed for sampling runs (torch/random).")
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--coordinate-frame", choices=["normalized_1000", "pixel"], default="normalized_1000")
    parser.add_argument("--response-format", choices=["json", "structured_text"], default="json")
    parser.add_argument("--prompt-type", choices=["s1_point", "s2_interaction"], default="s1_point")
    parser.add_argument("--dtype", default="bfloat16")
    parser.add_argument("--attn-implementation", default="eager")
    parser.add_argument("--device-map", default="auto")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--sample-id", action="append", dest="sample_ids")
    parser.add_argument("--force", action="store_true", help="Allow overwriting existing output or writing limited probes to canonical predictions.jsonl.")
    parser.add_argument("--validate-only", action="store_true", help="Validate record selection, image paths, and output collision checks without loading a model.")
    args = parser.parse_args(argv)

    if not args.validate_only:
        if not args.model_backend:
            parser.error("--model-backend is required unless --validate-only is set")
        if not args.model_path:
            parser.error("--model-path is required unless --validate-only is set")

    projection_report = _load_json(args.projection_report)
    all_records = list(projection_report.get("scoring_records", []))
    records = _selected_records(projection_report, limit=args.limit, sample_ids=args.sample_ids)
    validation = validate_run_plan(
        records,
        out=args.out,
        projection_report=args.projection_report,
        limit=args.limit,
        sample_ids=args.sample_ids,
        force=args.force,
        available_sample_ids={str(record.get("sample_id")) for record in all_records if record.get("sample_id")},
    )
    if not validation["ok"]:
        raise SystemExit(f"Blocked VLM prediction run: {json.dumps(validation, sort_keys=True)}")
    if args.validate_only:
        print(f"Validated VLM prediction run: {json.dumps(validation, sort_keys=True)}")
        return 0
    if args.seed is not None:
        import random

        import torch

        random.seed(args.seed)
        torch.manual_seed(args.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(args.seed)
    engine = build_engine(args)
    rows = run_predictions(
        records,
        engine,
        backend=args.model_backend,
        model_checkpoint=args.model_path,
        temperature=args.temperature,
        max_new_tokens=args.max_new_tokens,
        coordinate_frame=args.coordinate_frame,
        response_format=args.response_format,
        prompt_type=args.prompt_type,
    )
    write_predictions(
        rows,
        args.out,
        projection_report=args.projection_report,
        backend=args.model_backend,
        model_checkpoint=args.model_path,
        coordinate_frame=args.coordinate_frame,
        response_format=args.response_format,
        prompt_type=args.prompt_type,
        argv=argv,
    )
    print(f"Wrote {args.out} predictions={len(rows)} backend={args.model_backend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
