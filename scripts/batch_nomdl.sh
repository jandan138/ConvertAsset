#!/usr/bin/env bash
set -euo pipefail

# Batch convert all instance.usd under a root folder to *_noMDL.usd
# Defaults to minimal output: --only-new-usd
# Options:
#   --jobs N            Number of parallel jobs (default: 1)
#   --skip-existing     Skip if a matching *_noMDL*.usd already exists next to the instance.usd
#   --no-parallel       Force single-process even if --jobs > 1
#   --dry-run           Only print the commands without executing
#   --limit N           Process only first N files (for pilot runs)
#   --timeout SEC       Kill a single task if it runs longer than SEC (requires GNU timeout)
#   --log-dir PATH      Directory to write per-run CSV logs (default: /opt/my_dev/ConvertAsset/logs)
# Usage:
#   ./scripts/batch_nomdl.sh /shared/.../Asset_Library --jobs 2 --skip-existing --timeout 900

ROOT=""
JOBS=1
SKIP_EXISTING=0
NO_PARALLEL=0
DRY_RUN=0
LIMIT=0
TIMEOUT_SEC=0
LOG_DIR="/opt/my_dev/ConvertAsset/logs"

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
    --limit)
      LIMIT="$2"; shift 2;;
    --timeout)
      TIMEOUT_SEC="$2"; shift 2;;
    --log-dir)
      LOG_DIR="$2"; shift 2;;
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

# Prepare logging
mkdir -p "$LOG_DIR"
RUN_ID=$(date +%Y%m%d_%H%M%S)
LOG_CSV="$LOG_DIR/batch_nomdl_${RUN_ID}.csv"
echo "run_id,file,start_epoch,end_epoch,duration_sec,exit_code,output_found,output_file" > "$LOG_CSV"

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
      # log skip row
      local start_epoch end_epoch dur status out_found out_name
      start_epoch=$(date +%s)
      end_epoch=$start_epoch
      dur=0
      status="skip"
      out_found="yes"
      out_name="${matches[0]}"
      printf '%s,%s,%s,%s,%s,%s,%s,%s\n' "$RUN_ID" "$usd" "$start_epoch" "$end_epoch" "$dur" "$status" "$out_found" "$out_name" >> "$LOG_CSV" || true
      return 0
    fi
  fi
  local start_epoch end_epoch dur status
  start_epoch=$(date +%s)
  local cmd=("$ISAAC" "$MAIN" no-mdl "$usd" --only-new-usd)
  local wrapped
  if [[ $TIMEOUT_SEC -gt 0 ]]; then
    if command -v timeout >/dev/null 2>&1; then
      wrapped=(timeout "$TIMEOUT_SEC" "${cmd[@]}")
    else
      echo "[warn] GNU timeout not found, running without timeout for: $usd" >&2
      wrapped=("${cmd[@]}")
    fi
  else
    wrapped=("${cmd[@]}")
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    printf 'DRY: %q ' "${cmd[@]}"; echo
    return 0
  fi
  # execute without aborting the whole script on error
  status=0
  "${wrapped[@]}" || status=$?
  end_epoch=$(date +%s)
  dur=$(( end_epoch - start_epoch ))
  # detect output
  local base_noext="${usd%.*}_noMDL"
  shopt -s nullglob
  local outs=("${base_noext}"*.usd)
  shopt -u nullglob
  local out_found="no" out_name=""
  if [[ ${#outs[@]} -gt 0 ]]; then
    # pick the newest
    IFS=$'\n' read -r -d '' -a outs_sorted < <(ls -t -- "${outs[@]}" 2>/dev/null && printf '\0') || true
    out_name="${outs_sorted[0]}"
    # verify mtime >= start_epoch to ensure it's from this run
    if [[ -n "$out_name" ]]; then
      local mtime
      mtime=$(stat -c %Y -- "$out_name" 2>/dev/null || echo 0)
      if [[ "$mtime" -ge "$start_epoch" ]]; then
        out_found="yes"
      fi
    fi
  fi
  printf '%s,%s,%s,%s,%s,%s,%s,%s\n' "$RUN_ID" "$usd" "$start_epoch" "$end_epoch" "$dur" "$status" "$out_found" "$out_name" >> "$LOG_CSV"
  if [[ "$status" -eq 0 ]]; then
    echo "[ok] ${usd} (${dur}s) out=${out_found} ${out_name##*/}"
  else
    echo "[err](${status}) ${usd} (${dur}s) out=${out_found} ${out_name##*/}"
  fi
}

export -f convert_one
export SKIP_EXISTING ISAAC MAIN DRY_RUN LIMIT TIMEOUT_SEC LOG_DIR LOG_CSV RUN_ID

# Find all instance.usd
mapfile -d '' files < <(find "$ROOT" -type f -name 'instance.usd' -print0)

count=${#files[@]}
echo "Found $count instance.usd under $ROOT"

if [[ $count -eq 0 ]]; then exit 0; fi

# Apply limit if requested
if [[ $LIMIT -gt 0 && $LIMIT -lt $count ]]; then
  files=("${files[@]:0:$LIMIT}")
  count=${#files[@]}
  echo "Limiting to first $count files (via --limit)"
fi

PROCESSED=0; SUCCEEDED=0; FAILED=0

if [[ $NO_PARALLEL -eq 1 || $JOBS -le 1 ]]; then
  # Sequential
  for f in "${files[@]}"; do
    if convert_one "$f"; then SUCCEEDED=$((SUCCEEDED+1)); else FAILED=$((FAILED+1)); fi
    PROCESSED=$((PROCESSED+1))
    if (( PROCESSED % 50 == 0 )); then
      echo "[hb] processed=$PROCESSED ok=$SUCCEEDED err=$FAILED log=$LOG_CSV"
    fi
  done
else
  # Parallel using xargs (exit codes summarized after)
  printf '%s\0' "${files[@]}" | xargs -0 -n1 -P "$JOBS" bash -lc 'convert_one "$@"' _ || true
  # Summarize from CSV (count lines minus header with exit_code==0)
  if command -v awk >/dev/null 2>&1; then
    PROCESSED=$(awk 'NR>1 {c++} END{print c+0}' "$LOG_CSV" || echo 0)
    SUCCEEDED=$(awk -F, 'NR>1 && $6=="0" {ok++} END{print ok+0}' "$LOG_CSV" || echo 0)
    FAILED=$(( PROCESSED - SUCCEEDED ))
  fi
fi

echo "Summary: processed=$PROCESSED ok=$SUCCEEDED err=$FAILED log=$LOG_CSV"
