#!/usr/bin/env bash
set -euo pipefail

# Batch convert all instance.usd under a root folder to *_noMDL.usd
# Defaults to minimal output: --only-new-usd
# Options:
#   --jobs N           Number of parallel jobs (default: 1)
#   --skip-existing    Skip if a matching *_noMDL*.usd already exists next to the instance.usd
#   --no-parallel      Force single-process even if --jobs > 1
#   --dry-run          Only print the commands without executing
# Usage:
#   ./scripts/batch_nomdl.sh /shared/.../Asset_Library --jobs 2 --skip-existing

ROOT=""
JOBS=1
SKIP_EXISTING=0
NO_PARALLEL=0
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --jobs)
      JOBS="$2"; shift 2;;
    --skip-existing)
      SKIP_EXISTING=1; shift;;
    --no-parallel)
      NO_PARALLEL=1; shift;;
    --dry-run)
      DRY_RUN=1; shift;;
    -h|--help)
      grep '^# ' "$0" | sed 's/^# //'; exit 0;;
    *)
      if [[ -z "$ROOT" ]]; then ROOT="$1"; shift; else echo "Unknown arg: $1"; exit 2; fi;;
  esac
done

if [[ -z "$ROOT" ]]; then
  echo "Usage: $0 <root> [--jobs N] [--skip-existing] [--no-parallel] [--dry-run]" >&2
  exit 2
fi

if [[ ! -d "$ROOT" ]]; then
  echo "Not a directory: $ROOT" >&2
  exit 2
fi

ISAAC="/isaac-sim/isaac_python.sh"
MAIN="/opt/my_dev/ConvertAsset/main.py"

convert_one() {
  local usd="$1"
  # Skip if requested and any *_noMDL*.usd already exists
  if [[ $SKIP_EXISTING -eq 1 ]]; then
    local base_noext="${usd%.*}_noMDL"
    shopt -s nullglob
    local matches=("${base_noext}"*.usd)
    shopt -u nullglob
    if [[ ${#matches[@]} -gt 0 ]]; then
      echo "[skip] ${usd} (found existing: ${matches[0]##*/})"
      return 0
    fi
  fi
  local cmd=("$ISAAC" "$MAIN" no-mdl "$usd" --only-new-usd)
  if [[ $DRY_RUN -eq 1 ]]; then
    printf 'DRY: %q ' "${cmd[@]}"; echo
    return 0
  fi
  "${cmd[@]}"
}

export -f convert_one
export SKIP_EXISTING ISAAC MAIN DRY_RUN

# Find all instance.usd
mapfile -d '' files < <(find "$ROOT" -type f -name 'instance.usd' -print0)

count=${#files[@]}
echo "Found $count instance.usd under $ROOT"

if [[ $count -eq 0 ]]; then exit 0; fi

if [[ $NO_PARALLEL -eq 1 || $JOBS -le 1 ]]; then
  # Sequential
  for f in "${files[@]}"; do
    convert_one "$f"
  done
else
  # Parallel using xargs
  printf '%s\0' "${files[@]}" | xargs -0 -n1 -P "$JOBS" bash -lc 'convert_one "$@"' _
fi
