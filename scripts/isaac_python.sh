#!/usr/bin/env bash
set -euo pipefail

# A portable wrapper to run Python scripts inside Omniverse Isaac Sim's Python.
# It tries to locate the Isaac Sim installation automatically, or uses
# ISAAC_SIM_ROOT if provided.
#
# Usage:
#   ./scripts/isaac_python.sh <script.py> [args...]
#
# Environment variables:
#   ISAAC_SIM_ROOT  Absolute path to Isaac Sim install directory that contains python.sh
#

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <script.py> [args...]" >&2
  exit 2
fi

resolve_isaac_root() {
  # 1) Respect explicit env var
  if [[ -n "${ISAAC_SIM_ROOT:-}" && -x "${ISAAC_SIM_ROOT}/python.sh" ]]; then
    echo "$ISAAC_SIM_ROOT"
    return 0
  fi
  # 2) Common path inside official Docker container
  if [[ -x "/isaac-sim/python.sh" ]]; then
    echo "/isaac-sim"
    return 0
  fi
  # 3) User-local OV packages (default for Isaac Sim standalone installs)
  local ov_root="${HOME}/.local/share/ov/pkg"
  if [[ -d "$ov_root" ]]; then
    local candidates=()
    while IFS= read -r -d '' dir; do
      candidates+=("$dir")
    done < <(find "$ov_root" -maxdepth 1 -type d -name 'isaac_sim-*' -print0 2>/dev/null)
    if [[ ${#candidates[@]} -gt 0 ]]; then
      IFS=$'\n' read -r -d '' -a sorted < <(printf '%s\n' "${candidates[@]}" | sort -V && printf '\0') || true
      for (( idx=${#sorted[@]}-1; idx>=0; idx--)); do
        local dir="${sorted[$idx]}"
        [[ -z "$dir" ]] && continue
        if [[ -x "$dir/python.sh" ]]; then
          echo "$dir"
          return 0
        fi
      done
    fi
  fi
  # 4) A few common system locations
  for base in /opt/nvidia/isaac-sim /opt/NVIDIA/isaac-sim /opt/omniverse/isaac-sim; do
    if [[ -x "${base}/python.sh" ]]; then
      echo "$base"
      return 0
    fi
  done
  return 1
}

ISAAC_ROOT="$(resolve_isaac_root)" || {
  echo "ERROR: Could not locate Isaac Sim installation (python.sh not found)." >&2
  echo "Hint: export ISAAC_SIM_ROOT=\"/abs/path/to/isaac_sim-<version>\"" >&2
  echo "       and re-run: ISAAC_SIM_ROOT=... $0 <script.py> [args...]" >&2
  exit 1
}

RUNNER="${ISAAC_ROOT}/python.sh"
exec "$RUNNER" "$@"
