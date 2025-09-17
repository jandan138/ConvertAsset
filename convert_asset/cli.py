# -*- coding: utf-8 -*-
"""CLI entry for convert_asset utilities."""
import os
import sys
import argparse
from .no_mdl.processor import Processor
from .no_mdl.path_utils import _to_posix


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="convert-asset",
        description="USD conversion utilities (no-MDL copy generator)"
    )
    sub = parser.add_subparsers(dest="cmd", required=False)

    p_nomdl = sub.add_parser("no-mdl", help="Generate *_noMDL.usd siblings recursively")
    p_nomdl.add_argument("src", help="Path to top or single USD file")

    # If no subcommand provided, default to no-mdl for convenience
    args_ns, extras = parser.parse_known_args(argv)
    if args_ns.cmd is None:
        # Re-parse as no-mdl
        args_ns = parser.parse_args(["no-mdl"] + (argv or []))

    if args_ns.cmd == "no-mdl":
        src = _to_posix(args_ns.src)
        if not os.path.exists(src):
            print("Not found:", src)
            return 2
        proc = Processor()
        out = proc.process(src)
        print("\n=== SUMMARY ===")
        for k, v in proc.done.items():
            print(_to_posix(k), "->", _to_posix(v))
        print("\nTop-level new file:", out)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
