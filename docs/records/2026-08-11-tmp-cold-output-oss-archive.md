# 2026-08-11 tmp cold-output OSS archive

Old visual-review scratch directories under `tmp/` were considered for OSS
archive without removing the project workspace or active paper assets. The
initial audit retained 331 referenced directories. A final fixed-point active
reference scan retained 16 more ACL-named directories before upload.

The remaining 182 directories (1,437,774,631 bytes) were copied to the unique
permanent prefix
`archives/ConvertAsset/cold-output-v1/20260811T-convertasset-batch01-v2` in
`pjlab-bjpai-zhuzihou-assets`. Local removal occurred only after exact remote
count/size checks, common-MD5 `rclone check`, deterministic SHA-256 restore
samples, atomic quarantine, `python -m pytest -q`, stable Git status, and a
final tree SHA-256. Validation reported 804 passed and 4 skipped.

Authoritative per-file manifests, logs, the effective candidate inventory,
remote totals, and restore instructions are recorded under
`/cpfs/user/zhuzihou/ops/storage-cleanup/`, with the summary in
`REPORT-2026-08-11.md`.
