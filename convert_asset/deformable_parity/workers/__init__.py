"""Subprocess dispatch helpers for isolated 4-engine deformable workers (M1)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


_WORKERS_DIR = Path(__file__).resolve().parent


def resolve_engine_python(engine_id: str) -> tuple[list[str], dict[str, str]]:
    """Resolve the command prefix and sanitized env vars for an isolated engine worker."""
    env = dict(os.environ)
    repo_root = str(_WORKERS_DIR.parents[2])
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{existing_pp}" if existing_pp else repo_root

    if sys.platform.startswith("win"):
        conda_root = Path.home() / "Miniconda3" / "envs"
        if engine_id == "genesis":
            exe = env.get("CONVERT_ASSET_GENESIS_PYTHON") or str(
                conda_root / "sim-genesis-py312" / "python.exe"
            )
            return [exe], env
        if engine_id == "mujoco4":
            exe = env.get("CONVERT_ASSET_MUJOCO4_PYTHON") or str(
                conda_root / "sim-mujoco4-py312" / "python.exe"
            )
            return [exe], env
        if engine_id == "newton18":
            exe = env.get("CONVERT_ASSET_NEWTON18_PYTHON") or str(
                conda_root / "sim-newton18-py312" / "python.exe"
            )
            return [exe], env
        if engine_id == "isaac_physx":
            bat = env.get("CONVERT_ASSET_ISAAC_PYTHON") or r"I:\isaacsim\6.0.1\python.bat"
            portable_data = Path(r"I:\isaacsim-data\6.0.1")
            if portable_data.is_dir():
                env.setdefault("ISAACSIM_PORTABLE_ROOT", str(portable_data))
                tmp_dir = portable_data / "temp"
                tmp_dir.mkdir(parents=True, exist_ok=True)
                env.setdefault("TEMP", str(tmp_dir))
                env.setdefault("TMP", str(tmp_dir))
            return [bat], env
    else:
        conda_roots = [Path("/root/miniconda3/envs"), Path.home() / "conda-envs", Path.home() / "miniconda3/envs"]

        def _find_linux_py(env_name: str, env_var: str) -> str:
            override = env.get(env_var)
            if override:
                return override
            for root in conda_roots:
                cand = root / env_name / "bin" / "python"
                if cand.is_file():
                    return str(cand)
            return str(conda_roots[0] / env_name / "bin" / "python")

        if engine_id == "genesis":
            return [_find_linux_py("sim-genesis-py312", "CONVERT_ASSET_GENESIS_PYTHON")], env
        if engine_id == "mujoco4":
            return [_find_linux_py("sim-mujoco4-py312", "CONVERT_ASSET_MUJOCO4_PYTHON")], env
        if engine_id == "newton18":
            return [_find_linux_py("sim-newton18-py312", "CONVERT_ASSET_NEWTON18_PYTHON")], env
        if engine_id == "isaac_physx":
            sh = env.get("CONVERT_ASSET_ISAAC_PYTHON") or "/root/IsaacSim/_build/linux-x86_64/release/python.sh"
            return [sh], env

    raise ValueError(f"Unsupported engine_id: {engine_id!r}")


def worker_script_path(engine_id: str) -> Path:
    """Return the worker CLI script path for the given engine_id."""
    mapping = {
        "genesis": _WORKERS_DIR / "genesis_worker.py",
        "mujoco4": _WORKERS_DIR / "mujoco4_worker.py",
        "newton18": _WORKERS_DIR / "newton18_worker.py",
        "isaac_physx": _WORKERS_DIR / "isaac_worker.py",
    }
    if engine_id not in mapping:
        raise ValueError(f"Unsupported engine_id: {engine_id!r}")
    return mapping[engine_id]


def run_worker_request(
    engine_id: str,
    request: dict[str, Any],
    work_dir: Path,
    *,
    tag: str = "run",
    timeout_s: float = 360.0,
) -> dict[str, Any]:
    """Serialize ``request`` JSON, invoke isolated worker subprocess, and return parsed response."""
    work_dir.mkdir(parents=True, exist_ok=True)
    req_path = work_dir / f"{engine_id}_{tag}_request.json"
    resp_path = work_dir / f"{engine_id}_{tag}_response.json"
    log_path = work_dir / f"{engine_id}_{tag}.log"

    req_path.write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    cmd_prefix, env = resolve_engine_python(engine_id)
    script = worker_script_path(engine_id)
    cmd = [*cmd_prefix, str(script), "--request", str(req_path), "--response", str(resp_path)]

    proc = subprocess.run(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_s,
    )
    log_path.write_text(proc.stdout or "", encoding="utf-8")
    if proc.returncode != 0 or not resp_path.is_file():
        tail = "\n".join((proc.stdout or "").splitlines()[-40:])
        raise RuntimeError(
            f"{engine_id} worker failed (rc={proc.returncode}, resp_exists={resp_path.is_file()}).\n"
            f"Command: {cmd}\nLog tail:\n{tail}"
        )
    return json.loads(resp_path.read_text(encoding="utf-8"))


__all__ = ["resolve_engine_python", "run_worker_request", "worker_script_path"]
