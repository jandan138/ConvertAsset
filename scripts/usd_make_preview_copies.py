#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch make per-USD 'noMDL' sibling copies without flattening.
- For a given src USD (top or asset), recursively:
  1) create a sibling copy <name>_noMDL.usd under the SAME directory,
  2) inside the copy: convert MDL -> UsdPreviewSurface (best-effort), then strip MDL,
  3) rewrite references/payloads/variant-refs/clips to point to children's *_noMDL.usd siblings.
- Keeps the original layered & instanced structure. No Flatten.

Run (Isaac Sim python):
/isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/scripts/usd_make_preview_copies.py \
"/abs/path/to/your/file.usd"
"""

import os
import sys

from usd_no_mdl.processor import Processor
from usd_no_mdl.path_utils import _to_posix


def main():
    if len(sys.argv) < 2:
        print("Usage:\n  /isaac-sim/isaac_python.sh usd_make_preview_copies.py <src.usd>\n"
              "Example:\n  /isaac-sim/isaac_python.sh usd_make_preview_copies.py /path/to/top.usd\n"
              "Note: will create sibling *_noMDL.usd for src and all referenced usd recursively.")
        sys.exit(1)
    src = _to_posix(sys.argv[1])
    if not os.path.exists(src):
        print("Not found:", src)
        sys.exit(2)
    proc = Processor()
    out = proc.process(src)
    print("\n=== SUMMARY ===")
    for k, v in proc.done.items():
        print(_to_posix(k), "->", _to_posix(v))
    print("\nTop-level new file:", out)


if __name__ == "__main__":
    main()
