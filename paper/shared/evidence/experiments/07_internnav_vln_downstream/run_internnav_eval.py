#!/usr/bin/env python3
"""Run InternNav eval with the external runtime deps prepared for this experiment."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path


DEFAULT_INTERNNAV_ROOT = Path("/cpfs/user/zhuzihou/dev/InternNav")
DEFAULT_RUNTIME_DEPS_ROOT = Path("/cpfs/user/zhuzihou/assets/internnav_vln_runtime_deps_20260523")
NEXTDIT_CHECKPOINT_FFN_MULTIPLIER = 2 / 3


def runtime_pythonpath_entries(runtime_deps_root: Path, internnav_root: Path) -> list[str]:
    return [
        str(runtime_deps_root / "python_target"),
        str(runtime_deps_root / "internutopia_probe"),
        str(internnav_root),
    ]


def build_runtime_env(
    *,
    runtime_deps_root: Path,
    internnav_root: Path,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    env = dict(os.environ if base_env is None else base_env)
    entries = runtime_pythonpath_entries(runtime_deps_root, internnav_root)
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        entries.append(existing_pythonpath)
    env["PYTHONPATH"] = ":".join(entries)
    env["HF_HOME"] = str(runtime_deps_root / "hf_cache")
    env["HF_HUB_DISABLE_XET"] = "1"
    return env


def configure_current_process(runtime_deps_root: Path, internnav_root: Path) -> None:
    env = build_runtime_env(runtime_deps_root=runtime_deps_root, internnav_root=internnav_root)
    os.environ.update(env)
    for entry in reversed(runtime_pythonpath_entries(runtime_deps_root, internnav_root)):
        if entry not in sys.path:
            sys.path.insert(0, entry)


def flash_attention_available() -> bool:
    return importlib.util.find_spec("flash_attn") is not None


def patch_pkg_resources_packaging() -> None:
    import packaging
    import pkg_resources

    if not hasattr(pkg_resources, "packaging"):
        pkg_resources.packaging = packaging


def select_attn_implementation(
    *,
    requested: str | None,
    fallback: str,
    flash_attention_available: bool,
) -> str | None:
    if requested == "flash_attention_2" and not flash_attention_available:
        return fallback
    return requested


def patch_internvla_attention_fallback(fallback: str) -> None:
    from internnav.model.basemodel.internvla_n1.internvla_n1 import InternVLAN1ForCausalLM

    if getattr(InternVLAN1ForCausalLM, "_convertasset_attn_fallback_patched", False):
        return

    original_from_pretrained = InternVLAN1ForCausalLM.from_pretrained

    def patched_from_pretrained(cls, *args, **kwargs):
        requested = kwargs.get("attn_implementation")
        selected = select_attn_implementation(
            requested=requested,
            fallback=fallback,
            flash_attention_available=flash_attention_available(),
        )
        if selected != requested:
            print(
                f"ConvertAsset InternNav wrapper: using attn_implementation={selected!r} "
                f"instead of {requested!r} because flash_attn is unavailable.",
                file=sys.stderr,
            )
            kwargs["attn_implementation"] = selected
        return original_from_pretrained(*args, **kwargs)

    InternVLAN1ForCausalLM.from_pretrained = classmethod(patched_from_pretrained)
    InternVLAN1ForCausalLM._convertasset_attn_fallback_patched = True


def set_gradient_checkpointing_compat(
    model,
    *,
    enable: bool = True,
    gradient_checkpointing_func=None,
) -> None:
    modules = model.modules() if hasattr(model, "modules") else [model]
    for module in modules:
        if hasattr(module, "gradient_checkpointing"):
            module.gradient_checkpointing = enable


def patch_lumina_gradient_checkpointing() -> None:
    from internnav.model.basemodel.internvla_n1.nextdit_traj import LuminaNextDiT2DModel

    if getattr(LuminaNextDiT2DModel, "_convertasset_gradient_checkpointing_patched", False):
        return

    def patched_set_gradient_checkpointing(
        self,
        enable: bool = True,
        gradient_checkpointing_func=None,
    ) -> None:
        set_gradient_checkpointing_compat(
            self,
            enable=enable,
            gradient_checkpointing_func=gradient_checkpointing_func,
        )

    LuminaNextDiT2DModel._set_gradient_checkpointing = patched_set_gradient_checkpointing
    LuminaNextDiT2DModel._convertasset_gradient_checkpointing_patched = True


def patch_nextdit_config_default_ffn_multiplier(config_cls=None) -> None:
    if config_cls is None:
        from internnav.model.basemodel.internvla_n1.nextdit_crossattn_traj import NextDiTCrossAttnConfig

        config_cls = NextDiTCrossAttnConfig

    if getattr(config_cls, "_convertasset_ffn_multiplier_patched", False):
        return

    original_init = config_cls.__init__

    def patched_init(self, *args, **kwargs):
        kwargs.setdefault("ffn_dim_multiplier", NEXTDIT_CHECKPOINT_FFN_MULTIPLIER)
        return original_init(self, *args, **kwargs)

    config_cls.__init__ = patched_init
    config_cls._convertasset_ffn_multiplier_patched = True


def preload_internvla_policy() -> None:
    import transformers.utils.import_utils as import_utils

    patch_pkg_resources_packaging()
    # InternNav does not use sklearn generation helpers, and Isaac's bundled
    # sklearn/scipy stack can conflict with the runtime NumPy pin after Kit starts.
    import_utils._sklearn_available = False
    patch_nextdit_config_default_ffn_multiplier()
    from internnav.model.basemodel.internvla_n1.internvla_n1_policy import InternVLAN1Net  # noqa: F401

    patch_internvla_attention_fallback(os.environ.get("INTERNVLA_ATTN_FALLBACK", "sdpa"))
    patch_lumina_gradient_checkpointing()


def run_eval(config_path: Path, runtime_deps_root: Path, internnav_root: Path) -> int:
    configure_current_process(runtime_deps_root, internnav_root)
    os.chdir(internnav_root)
    preload_internvla_policy()
    from scripts.eval.eval import main as internnav_main

    sys.argv = ["scripts/eval/eval.py", "--config", str(config_path)]
    internnav_main()
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="InternNav eval config path.")
    parser.add_argument("--internnav-root", default=DEFAULT_INTERNNAV_ROOT, type=Path)
    parser.add_argument("--runtime-deps-root", default=DEFAULT_RUNTIME_DEPS_ROOT, type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Print wrapper configuration without running eval.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "config_path": str(args.config),
                    "internnav_root": str(args.internnav_root),
                    "runtime_deps_root": str(args.runtime_deps_root),
                    "pythonpath_entries": runtime_pythonpath_entries(args.runtime_deps_root, args.internnav_root),
                    "preload_internvla_policy": True,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    return run_eval(args.config, args.runtime_deps_root, args.internnav_root)


if __name__ == "__main__":
    raise SystemExit(main())
