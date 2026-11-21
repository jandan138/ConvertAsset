#!/usr/bin/env python3
"""Install the official ICLR 2027 style, recording its archive SHA-256."""
import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

URL = "https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip"
FILES = ("iclr2027_conference.sty", "iclr2027_conference.bst", "fancyhdr.sty", "natbib.sty")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    raw = args.archive.read_bytes() if args.archive else urllib.request.urlopen(URL, timeout=60).read()
    root = Path(__file__).resolve().parents[1]
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        hashes = {}
        for name in FILES:
            content = archive.read(f"iclr2027/{name}")
            target = root / name
            if target.exists() and target.read_bytes() != content:
                raise ValueError(f"Existing template differs: {target}")
            target.write_bytes(content)
            hashes[name] = hashlib.sha256(content).hexdigest()
        (root / "TEMPLATE_PROVENANCE.json").write_text(json.dumps({
            "source": URL, "archive_sha256": hashlib.sha256(raw).hexdigest(), "files": hashes
        }, indent=2) + "\n")
    print("Official ICLR 2027 template installed")


if __name__ == "__main__":
    main()
