# -*- coding: utf-8 -*-
"""
Project entry point for ConvertAsset.
Usage examples:
  /isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py no-mdl /path/to/top.usd
  /isaac-sim/isaac_python.sh /opt/my_dev/ConvertAsset/main.py /path/to/top.usd  # default subcommand no-mdl
"""
from convert_asset.cli import main as cli_main

if __name__ == "__main__":
    import sys
    raise SystemExit(cli_main(sys.argv[1:]))
