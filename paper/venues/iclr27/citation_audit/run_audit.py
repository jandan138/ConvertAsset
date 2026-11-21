"""Run the official auditor with the venue's actual LaTeX input search directory.

Only input-path resolution is adapted. Identity, context hashing, support decisions,
cache handling and exit codes are the unchanged skill implementation.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

SKILL_SCRIPT = Path('/root/.codex/skills/citation-integrity-auditor/scripts/audit_citations.py')
spec = importlib.util.spec_from_file_location('official_citation_auditor', SKILL_SCRIPT)
official = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = official
spec.loader.exec_module(official)
args = official.build_parser().parse_args()
venue = args.main_tex.resolve().parent

def resolve_input(current, target):
    relative = Path(target)
    if not relative.suffix:
        relative = relative.with_suffix('.tex')
    # Build runs from the venue directory. Retain child-relative fallback for
    # explicit local nested includes; fail instead of silently dropping inputs.
    candidates = [venue / relative, current.parent / relative]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f'Unresolved TeX input {target!r} in {current}')

official._resolve_input = resolve_input
status = official.main()
if args.json_out.exists() and status in (0, 1):
    report = json.loads(args.json_out.read_text())
    report['inputs']['input_resolution_adapter'] = {
        'path': str(Path(__file__).resolve().relative_to((args.project_root or Path.cwd()).resolve())),
        'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rule': 'venue-working-directory first, then child-relative; missing inputs fail',
    }
    if args.cache and args.cache.exists():
        report['inputs']['metadata_cache'] = {'path': str(args.cache), 'sha256': hashlib.sha256(args.cache.read_bytes()).hexdigest()}
    normalization = Path(__file__).parent / 'metadata-normalization.json'
    if args.cache and args.cache.name == 'normalized-metadata-cache.json':
        report['inputs']['metadata_normalization'] = {'path': str(normalization), 'sha256': hashlib.sha256(normalization.read_bytes()).hexdigest()}
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
sys.exit(status)
