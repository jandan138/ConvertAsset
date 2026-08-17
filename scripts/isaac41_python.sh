#!/usr/bin/env bash
set -euo pipefail

# Pinned EOS-managed Isaac Sim 4.1 runtime used by formal ConvertAsset gates.
# Keep this wrapper intentionally small: it selects an existing managed runtime;
# it does not create or mutate a Python environment.
prefix="/cpfs/shared/simulation/zhuzihou/dev/conda-managed/envs/embodied-eval-os-sim-isaacsim41-genmanip-py310"
site="${prefix}/lib/python3.10/site-packages"
ld_paths="${site}/isaacsim/extscache/omni.cuda.libs/bin:${site}/isaacsim/extscache/omni.gpu_foundation/bin/deps:${site}/torch/lib"

exec env -i \
  HOME="${HOME:-/tmp}" \
  TMPDIR="${TMPDIR:-/tmp}" \
  PATH="${prefix}/bin:/usr/local/bin:/usr/bin:/bin" \
  LD_LIBRARY_PATH="${ld_paths}" \
  PYTHONNOUSERSITE=1 \
  PYTHONDONTWRITEBYTECODE=1 \
  ACCEPT_EULA=Y \
  OMNI_KIT_ACCEPT_EULA=YES \
  "${prefix}/bin/python" -I -B "$@"
