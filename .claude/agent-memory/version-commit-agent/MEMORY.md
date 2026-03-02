# Project: ConvertAsset — Version/Commit Agent Memory

## Commit Message Convention
- Format: `Type: Short description` (capital Type, colon, space)
- Common types seen: `Chore`, `docs(scope)`
- Examples from history:
  - `Chore: Add Claude Code agents to version control`
  - `docs(glb): clarify isaac_python usage`
- Always append Co-Authored-By trailer for Claude

## Gitignore Rules (as of 2026-03-02)
- `asset/` — legacy ignored asset folder
- `assets/` — new consolidated asset folder (added 2026-03-02)
- `*.glb` — all GLB output files
- `logs/`, `*.log`, `*.csv`
- Python caches, venvs, build artifacts

## Asset Directory Layout
- `assets/glb/` — output .glb files (git-ignored)
- `assets/usd/` — output .usd files, e.g. *_noMDL.usd (git-ignored); consistent with `assets/` gitignore rule
- `examples/` — demo/sample assets tracked in git (do NOT move)
- `reports/` — report outputs tracked in git (do NOT move)

## Key File Locations
- `.gitignore` — project root
- `CLAUDE.md` — project instructions (tracked, root)
- `convert_asset/` — main Python package
- `examples/` — tracked sample USD/GLB files
- `reports/` — tracked report outputs

## Version Files
- No package.json or setup.py with version fields found yet
- No explicit VERSION file present
