#!/usr/bin/env python3
"""Resumable BF16 GPU VLM inference suite for CVIU v3 experiments."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import random
from pathlib import Path
import shutil
import sys
import time
from typing import Any

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v3_common import (  # noqa: E402
    parse_point_by_mode,
    repo_root_from_script,
    resolve_asset_path,
    score_normalized_point,
    sha256_file,
)


@dataclass(frozen=True)
class ModelSpec:
    key: str
    hf_repo: str
    family: str
    default_parser: str
    backend_kind: str  # "chat" or "molmo"
    min_vram_gb: int = 16


MODEL_SPECS: dict[str, ModelSpec] = {
    "qwen3_vl_2b": ModelSpec(
        key="qwen3_vl_2b",
        hf_repo="Qwen/Qwen3-VL-2B-Instruct",
        family="Qwen3-VL",
        default_parser="flex_1000",
        backend_kind="chat",
        min_vram_gb=8,
    ),
    "qwen3_vl_8b": ModelSpec(
        key="qwen3_vl_8b",
        hf_repo="Qwen/Qwen3-VL-8B-Instruct",
        family="Qwen3-VL",
        default_parser="strict",
        backend_kind="chat",
        min_vram_gb=18,
    ),
    "internvl3_5_8b": ModelSpec(
        key="internvl3_5_8b",
        hf_repo="OpenGVLab/InternVL3_5-8B-HF",
        family="InternVL3.5",
        default_parser="strict",
        backend_kind="chat",
        min_vram_gb=18,
    ),
    "internvl3_5_14b": ModelSpec(
        key="internvl3_5_14b",
        hf_repo="OpenGVLab/InternVL3_5-14B-HF",
        family="InternVL3.5",
        default_parser="strict",
        backend_kind="chat",
        min_vram_gb=30,
    ),
    "internvl3_5_38b": ModelSpec(
        key="internvl3_5_38b",
        hf_repo="OpenGVLab/InternVL3_5-38B-HF",
        family="InternVL3.5",
        default_parser="strict",
        backend_kind="chat",
        min_vram_gb=78,
    ),
    "pixtral_12b": ModelSpec(
        key="pixtral_12b",
        hf_repo="mistral-community/pixtral-12b",
        family="Pixtral",
        default_parser="relaxed_xy",
        backend_kind="chat",
        min_vram_gb=26,
    ),
    "llava_next_mistral_7b": ModelSpec(
        key="llava_next_mistral_7b",
        hf_repo="llava-hf/llava-v1.6-mistral-7b-hf",
        family="LLaVA-NeXT-Mistral",
        default_parser="unit_float_xy",
        backend_kind="chat",
        min_vram_gb=16,
    ),
    "molmo2_8b": ModelSpec(
        key="molmo2_8b",
        hf_repo="allenai/Molmo2-8B",
        family="Molmo2",
        default_parser="molmo2_1000",
        backend_kind="molmo2",
        min_vram_gb=18,
    ),
    "molmo_7b_o": ModelSpec(
        key="molmo_7b_o",
        hf_repo="allenai/Molmo-7B-O-0924",
        family="Molmo",
        default_parser="molmo_0_100",
        backend_kind="molmo",
        min_vram_gb=16,
    ),
}


def build_prompt(query: str, model_spec: ModelSpec) -> str:
    if model_spec.backend_kind == "molmo2":
        return (
            f"{query} Use normalized 0-1000 coordinates: (0,0) top left, (1000,1000) bottom right. "
            'Return either one line \'Point: x, y\' or <points coords="1 x y"/>.'
        )
    if model_spec.backend_kind == "molmo":
        return (
            f"{query} Use normalized 0-1000 coordinates: (0,0) top left, (1000,1000) bottom right. "
            "Return either one line 'Point: x, y' or a <point x=\"...\" y=\"...\"/> tag."
        )
    return (
        f"{query} Use normalized 0-1000 coordinates: (0,0) top left, (1000,1000) bottom right. "
        "Return exactly one line: Point: x, y"
    )


def _record_key(row: dict[str, Any]) -> tuple[str, str, int, int]:
    return (
        str(row["pair_id"]),
        str(row["condition"]),
        int(row.get("repeat", 0)),
        int(row.get("draw_idx", 0)),
    )


def evaluate_raw_response(raw: str, mask: np.ndarray, parser_mode: str) -> dict[str, Any]:
    point = parse_point_by_mode(raw, parser_mode=parser_mode)
    valid, hit, bbox_hit = score_normalized_point(point, mask)
    return {
        "point_normalized": point,
        "valid_point": valid,
        "hit": hit,
        "visible_bbox_hit": bbox_hit,
        "target_visible": bool(mask.any()),
    }


def _load_strict_bf16_model(spec: ModelSpec, model_path: Path | None = None) -> tuple[Any, Any, dict[str, Any]]:
    import torch
    import transformers

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required for strict BF16 VLM evaluation")

    n_gpus = torch.cuda.device_count()
    total_vram_gb = sum(torch.cuda.get_device_properties(i).total_memory for i in range(n_gpus)) / (1024.0 ** 3)
    load_source = str(model_path.resolve()) if model_path is not None else spec.hf_repo
    trust_remote = spec.backend_kind == "molmo"
    config = transformers.AutoConfig.from_pretrained(load_source, trust_remote_code=trust_remote)
    if getattr(config, "quantization_config", None):
        raise ValueError(f"Quantized checkpoint forbidden: {spec.hf_repo}")

    if spec.backend_kind == "molmo2":
        cand_names = ["Molmo2ForConditionalGeneration", "AutoModelForImageTextToText"]
    elif spec.backend_kind == "molmo":
        cand_names = ["AutoModelForImageTextToText", "AutoModelForVision2Seq", "AutoModelForCausalLM"]
    else:
        cand_names = [
            "AutoModelForImageTextToText",
            "LlavaNextForConditionalGeneration",
            "LlavaForConditionalGeneration",
            "AutoModelForVision2Seq",
            "AutoModelForCausalLM",
        ]
    model_cls_candidates = [getattr(transformers, n) for n in cand_names if hasattr(transformers, n)]

    attn_used = "sdpa"
    model = None
    last_err: Exception | None = None
    for cls in model_cls_candidates:
        for attn_impl in ("sdpa", "eager"):
            try:
                try:
                    model = cls.from_pretrained(
                        load_source,
                        dtype=torch.bfloat16,
                        attn_implementation=attn_impl,
                        device_map="auto",
                        trust_remote_code=trust_remote,
                    ).eval()
                except TypeError:
                    model = cls.from_pretrained(
                        load_source,
                        torch_dtype=torch.bfloat16,
                        attn_implementation=attn_impl,
                        device_map="auto",
                        trust_remote_code=trust_remote,
                    ).eval()
                attn_used = attn_impl
                break
            except Exception as exc:
                last_err = exc
        if model is not None:
            break

    if model is None:
        raise RuntimeError(f"Failed to load model {spec.hf_repo} ({load_source}): {last_err}")

    device_map = getattr(model, "hf_device_map", {})
    param_devices = sorted({str(p.device) for p in model.parameters()})
    param_dtypes = sorted({str(p.dtype) for p in model.parameters() if p.is_floating_point()})
    if not param_devices or any(not d.startswith("cuda:") for d in param_devices):
        raise ValueError(f"Model parameters must reside entirely on CUDA GPUs, got: {param_devices}")
    if any(str(v) in ("cpu", "disk", "meta") for v in device_map.values()):
        raise ValueError(f"CPU/disk/meta offload forbidden, got hf_device_map={device_map}")
    if param_dtypes != ["torch.bfloat16"]:
        raise ValueError(f"Expected strict torch.bfloat16 parameters, got: {param_dtypes}")

    processor = transformers.AutoProcessor.from_pretrained(load_source, trust_remote_code=trust_remote)
    placement = {
        "gpu_count": n_gpus,
        "total_vram_gb": round(total_vram_gb, 2),
        "device_map": device_map,
        "parameter_devices": param_devices,
        "parameter_dtypes": param_dtypes,
        "attn_implementation": attn_used,
        "torch": torch.__version__,
        "transformers": transformers.__version__,
    }
    return model, processor, placement


def _generate_one(
    *,
    model: Any,
    processor: Any,
    spec: ModelSpec,
    image_path: Path,
    prompt: str,
    max_new_tokens: int,
    temperature: float,
    top_p: float,
) -> tuple[str, Any]:
    import torch

    with Image.open(image_path) as im_raw:
        im = im_raw.convert("RGB")

    if spec.backend_kind == "molmo":
        import transformers

        inputs = processor.process(images=[im], text=prompt)
        inputs = {
            k: (v.to(model.device).unsqueeze(0) if k == "images" else v.to(model.device))
            if isinstance(v, torch.Tensor)
            else v
            for k, v in inputs.items()
        }
        for k, v in list(inputs.items()):
            if isinstance(v, torch.Tensor) and torch.is_floating_point(v):
                inputs[k] = v.to(dtype=torch.bfloat16)
        gen_cfg = transformers.GenerationConfig(
            max_new_tokens=max_new_tokens,
            stop_strings=["<|endoftext|>"],
            do_sample=(temperature > 0.0),
            **({"temperature": temperature, "top_p": top_p} if temperature > 0.0 else {}),
        )
        with torch.inference_mode():
            out = model.generate_from_batch(inputs, generation_config=gen_cfg, tokenizer=processor.tokenizer)
        gen_tokens = out[0, inputs["input_ids"].size(1) :]
        raw = processor.tokenizer.decode(gen_tokens, skip_special_tokens=True)
        return raw, None

    if spec.backend_kind == "molmo2":
        messages_m2 = [
            {
                "role": "user",
                "content": [{"type": "image", "image": im}, {"type": "text", "text": prompt}],
            }
        ]
        try:
            inputs = processor.apply_chat_template(
                messages_m2,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            )
        except Exception:
            messages_alt = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image"}]}]
            text = processor.apply_chat_template(messages_alt, tokenize=False, add_generation_prompt=True)
            inputs = processor(text=[text], images=[im], padding=True, return_tensors="pt")
        inputs = {
            k: (
                v.to(device=model.device, dtype=torch.bfloat16)
                if isinstance(v, torch.Tensor) and torch.is_floating_point(v)
                else (v.to(model.device) if isinstance(v, torch.Tensor) else v)
            )
            for k, v in inputs.items()
        }
        gen_kwargs_m2: dict[str, Any] = {"max_new_tokens": max_new_tokens}
        if temperature > 0.0:
            gen_kwargs_m2.update({"do_sample": True, "temperature": temperature, "top_p": top_p})
        else:
            gen_kwargs_m2["do_sample"] = False
        with torch.inference_mode():
            generated = model.generate(**inputs, **gen_kwargs_m2)
        trimmed = generated[:, inputs["input_ids"].shape[1] :]
        raw = processor.tokenizer.decode(trimmed[0], skip_special_tokens=True)
        return raw, None

    messages = [
        {
            "role": "user",
            "content": [{"type": "image", "image": str(image_path)}, {"type": "text", "text": prompt}],
        }
    ]
    if spec.key.startswith("llava") or spec.key.startswith("pixtral"):
        messages_fallback = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
    else:
        messages_fallback = [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image"}]}]
    try:
        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    except Exception:
        text = processor.apply_chat_template(messages_fallback, tokenize=False, add_generation_prompt=True)

    inputs = processor(text=[text], images=[im], padding=True, return_tensors="pt").to(model.device)
    if not spec.key.startswith("qwen3"):
        for k, v in list(inputs.items()):
            if isinstance(v, torch.Tensor) and torch.is_floating_point(v):
                inputs[k] = v.to(dtype=torch.bfloat16)

    gen_kwargs: dict[str, Any] = {"max_new_tokens": max_new_tokens}
    if temperature > 0.0:
        gen_kwargs.update({"do_sample": True, "temperature": temperature, "top_p": top_p})
    else:
        gen_kwargs.update({"do_sample": False})
        if spec.key.startswith("qwen3"):
            gen_kwargs["temperature"] = 0.0

    with torch.inference_mode():
        generated = model.generate(**inputs, **gen_kwargs)
    trimmed = generated[:, inputs["input_ids"].shape[1] :]
    raw = processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
    grid = inputs["image_grid_thw"].tolist() if "image_grid_thw" in inputs else None
    return raw, grid


def _prepare_jobs(
    *,
    task: str,
    manifest_path: Path,
    protocol_path: Path,
    repeat: int,
    num_draws: int,
    assets_root: Path | None,
) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest["records"]
    if task == "control-repeat" or task == "stochastic-control":
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        ctrl_scenes = set(protocol["render_noise_control_scene_ids"])
        rows = [r for r in rows if r["scene_id"] in ctrl_scenes]

    jobs: list[dict[str, Any]] = []
    draws = range(num_draws) if task == "stochastic-control" else (0,)
    for d in draws:
        for r in rows:
            rep = 0 if task == "stochastic-control" else repeat
            jobs.append(
                {
                    "record": r,
                    "repeat": rep,
                    "draw_idx": d,
                    "img_path": resolve_asset_path(r["image"]["path"], assets_root),
                    "mask_path": resolve_asset_path(r["mask"]["path"], assets_root),
                }
            )
    return jobs


def _qualify_pilot(
    *,
    raw_records: list[dict[str, Any]],
    spec: ModelSpec,
    assets_root: Path | None,
    out_dir: Path,
) -> dict[str, Any]:
    candidate_modes = ["strict", "relaxed_xy"]
    if spec.backend_kind == "molmo":
        candidate_modes.append("molmo_0_100")
    elif spec.backend_kind == "molmo2":
        candidate_modes.append("molmo2_1000")
    elif spec.default_parser in ("unit_float_xy", "flex_1000"):
        candidate_modes.append(spec.default_parser)

    mode_stats: dict[str, dict[str, Any]] = {}
    for pmode in candidate_modes:
        valid_count = 0
        hit_count = 0
        for rec in raw_records:
            mask = np.load(resolve_asset_path(rec["mask"]["path"], assets_root), allow_pickle=False)
            scored = evaluate_raw_response(rec["raw_response"], mask, pmode)
            valid_count += int(scored["valid_point"])
            hit_count += int(scored["hit"])
        n = len(raw_records)
        mode_stats[pmode] = {
            "valid_count": valid_count,
            "total": n,
            "valid_rate": (valid_count / n) if n else 0.0,
            "hit_count": hit_count,
            "hit_rate": (hit_count / n) if n else 0.0,
        }

    selected_mode = None
    search_order = [spec.default_parser] + [m for m in candidate_modes if m != spec.default_parser]
    for pmode in search_order:
        if pmode in mode_stats and mode_stats[pmode]["valid_rate"] >= 0.90:
            selected_mode = pmode
            break
    if selected_mode is None:
        selected_mode = max(candidate_modes, key=lambda m: mode_stats[m]["valid_rate"])

    passed = mode_stats[selected_mode]["valid_rate"] >= 0.90
    summary = {
        "model_key": spec.key,
        "hf_repo": spec.hf_repo,
        "family": spec.family,
        "passed_90pct_gate": passed,
        "selected_parser_mode": selected_mode,
        "mode_stats": mode_stats,
    }
    (out_dir / f"pilot_qualification_{spec.key}.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    root = repo_root_from_script(Path(__file__))
    raw_v1 = root / "paper/shared/evidence/raw/cviu_formal/v1"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        choices=["pilot-qualify", "formal-primary", "control-repeat", "control-rerender", "stochastic-control", "counterfactual"],
        required=True,
    )
    parser.add_argument("--model-key", choices=sorted(MODEL_SPECS), required=True)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--cf-cache-dir", type=Path, default=None)
    parser.add_argument("--protocol", type=Path, default=raw_v1 / "protocol.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeat", type=int, default=0)
    parser.add_argument("--num-draws", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--max-new-tokens", type=int, default=128)
    parser.add_argument("--parser-mode", choices=["strict", "relaxed_xy", "molmo_0_100", "molmo2_1000", "unit_float_xy", "flex_1000"], default=None)
    parser.add_argument("--assets-root", type=Path, default=None)
    parser.add_argument("--model-path", type=Path, default=None)
    args = parser.parse_args()

    spec = MODEL_SPECS[args.model_key]
    assets_root = args.assets_root.resolve() if args.assets_root else None
    if args.manifest is None:
        if args.task == "pilot-qualify":
            manifest_path = root / "paper/shared/evidence/raw/cviu_diagnostics/pilot_20261114_v1/manifest.json"
        elif args.task == "control-rerender":
            manifest_path = raw_v1 / "render_control_manifest.json"
        elif args.task == "counterfactual":
            if args.cf_cache_dir is None:
                raise ValueError("--manifest or --cf-cache-dir is required for --task counterfactual")
            cf_dir = args.cf_cache_dir.resolve()
            cf_manifest = cf_dir / "counterfactual_manifest.json"
            if not cf_manifest.is_file():
                import build_counterfactual_inputs  # noqa: E402

                build_counterfactual_inputs.build_counterfactual_dataset(
                    manifest_path=(raw_v1 / "manifest.json").resolve(),
                    out_dir=cf_dir,
                    assets_root=assets_root,
                    skip_hash_check=False,
                )
            manifest_path = cf_manifest
        else:
            manifest_path = raw_v1 / "manifest.json"
    else:
        manifest_path = args.manifest
    manifest_path = manifest_path.resolve()
    protocol_path = args.protocol.resolve()

    if args.task == "stochastic-control" and args.temperature <= 0.0:
        args.temperature = 0.2

    parser_mode = args.parser_mode or ("strict" if spec.default_parser == "strict" else spec.default_parser)
    pilot_qual_path = args.out.parent / f"pilot_qualification_{spec.key}.json"
    if args.parser_mode is None and args.task != "pilot-qualify" and pilot_qual_path.is_file():
        qual_meta = json.loads(pilot_qual_path.read_text(encoding="utf-8"))
        if qual_meta.get("passed_90pct_gate"):
            parser_mode = qual_meta["selected_parser_mode"]

    jobs = _prepare_jobs(
        task=args.task,
        manifest_path=manifest_path,
        protocol_path=protocol_path,
        repeat=args.repeat,
        num_draws=args.num_draws,
        assets_root=assets_root,
    )

    args.out.mkdir(parents=True, exist_ok=True)
    pred_path = args.out / "predictions.jsonl"
    completed: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    if pred_path.is_file():
        valid_lines: list[str] = []
        for line in pred_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("status") == "ok":
                completed[_record_key(row)] = row
                valid_lines.append(json.dumps(row))
        if valid_lines:
            pred_path.write_text("\n".join(valid_lines) + "\n", encoding="utf-8")
        else:
            pred_path.unlink(missing_ok=True)

    pending = [
        j
        for j in jobs
        if (str(j["record"]["pair_id"]), str(j["record"]["condition"]), int(j["repeat"]), int(j["draw_idx"]))
        not in completed
    ]
    print(
        f"[v3_suite] task={args.task} model={spec.key} ({spec.hf_repo}) parser={parser_mode} "
        f"total={len(jobs)} resumed={len(completed)} remaining={len(pending)}",
        flush=True,
    )

    import torch

    placement: dict[str, Any] = {}
    errors = 0
    if pending:
        model, processor, placement = _load_strict_bf16_model(spec, model_path=args.model_path)
        shutil.copy2(__file__, args.out / "runner_snapshot.py")
        metadata = {
            "task": args.task,
            "model_key": spec.key,
            "hf_repo": spec.hf_repo,
            "family": spec.family,
            "parser_mode": parser_mode,
            "manifest_path": str(manifest_path),
            "manifest_sha256": sha256_file(manifest_path),
            "repeat": args.repeat,
            "num_draws": args.num_draws if args.task == "stochastic-control" else 1,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "max_new_tokens": args.max_new_tokens,
            "dtype": "bfloat16",
            "placement": placement,
        }
        (args.out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

        with pred_path.open("a", encoding="utf-8") as fh:
            for idx, job in enumerate(pending, start=1):
                rec = job["record"]
                draw_idx = int(job["draw_idx"])
                rep = int(job["repeat"])
                seed = (20261120 + draw_idx) if args.task == "stochastic-control" else (20261114 + rep)
                random.seed(seed)
                np.random.seed(seed)
                torch.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)

                prompt = build_prompt(rec["query"], spec)
                t0 = time.monotonic()
                out_row: dict[str, Any] = {
                    **rec,
                    "task": args.task,
                    "model_key": spec.key,
                    "hf_repo": spec.hf_repo,
                    "family": spec.family,
                    "parser_mode": parser_mode,
                    "repeat": rep,
                    "draw_idx": draw_idx,
                    "seed": seed,
                    "prompt": prompt,
                }
                try:
                    raw, grid = _generate_one(
                        model=model,
                        processor=processor,
                        spec=spec,
                        image_path=job["img_path"],
                        prompt=prompt,
                        max_new_tokens=args.max_new_tokens,
                        temperature=args.temperature,
                        top_p=args.top_p,
                    )
                    mask = np.load(job["mask_path"], allow_pickle=False)
                    scored = evaluate_raw_response(raw, mask, parser_mode)
                    out_row.update(
                        status="ok",
                        raw_response=raw,
                        image_grid_thw=grid,
                        **scored,
                    )
                except Exception as exc:
                    errors += 1
                    out_row.update(status="runtime_error", error=repr(exc), hit=None)
                out_row["elapsed_seconds"] = round(time.monotonic() - t0, 4)
                fh.write(json.dumps(out_row) + "\n")
                fh.flush()
                if idx % 60 == 0 or idx == len(pending):
                    print(f"  [{spec.key}/{args.task}] {idx}/{len(pending)} done (errors={errors})", flush=True)

    all_ok_rows = [
        json.loads(line)
        for line in pred_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("status") == "ok"
    ]
    if args.task == "pilot-qualify":
        qual = _qualify_pilot(raw_records=all_ok_rows, spec=spec, assets_root=assets_root, out_dir=args.out.parent)
        print(f"[pilot-qualify] {spec.key}: {json.dumps(qual)}", flush=True)
        if not qual["passed_90pct_gate"]:
            raise SystemExit(2)

    completion = {
        "task": args.task,
        "model_key": spec.key,
        "expected_records": len(jobs),
        "completed_ok": len(all_ok_rows),
        "runtime_errors": errors,
        "status": "complete" if (errors == 0 and len(all_ok_rows) == len(jobs)) else "incomplete",
    }
    (args.out / "completion.json").write_text(json.dumps(completion, indent=2) + "\n", encoding="utf-8")
    if completion["status"] != "complete":
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

