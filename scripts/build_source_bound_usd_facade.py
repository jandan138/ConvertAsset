#!/usr/bin/env python3
"""Wrap one producer USD source as a package-local identity facade."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def build(
    *, source: Path, out: Path, entry_name: str, source_prim: str = "/root"
) -> Path:
    source = source.resolve()
    out = out.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite package: {out}")
    deps = out / "deps/source"
    shutil.copytree(source.parent, deps)
    relative_source = (deps / source.name).relative_to(out).as_posix()
    asset = out / "asset.usd"
    asset.write_text(
        f'''#usda 1.0
(
    defaultPrim = "World"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "World"
{{
    def Xform "{entry_name}"
    {{
        def Xform "Visual"
        {{
            def Xform "Source" (
                prepend references = @{relative_source}@<{source_prim}>
            ) {{}}
        }}
    }}
}}
''',
        encoding="utf-8",
    )
    evidence = out / "evidence"
    evidence.mkdir()
    manifest = {
        "schema_version": "aan.source_bound_facade_manifest.v1",
        "overall_status": "facade_only_runtime_pending",
        "entrypoint": "asset.usd",
        "entry_prim": f"/World/{entry_name}",
        "source": {
            "relative_path": relative_source,
            "sha256": _sha(source),
            "source_prim": source_prim,
        },
        "identity_entry_transform": True,
        "claim_boundary": "Package-local source facade only; no physics or runtime qualification.",
    }
    (evidence / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--entry-name", required=True)
    parser.add_argument("--source-prim", default="/root")
    args = parser.parse_args()
    print(
        build(
            source=args.source,
            out=args.out,
            entry_name=args.entry_name,
            source_prim=args.source_prim,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
