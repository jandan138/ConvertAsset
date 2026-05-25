#!/usr/bin/env python3
"""Provenance stub for legacy selected InternNav rerun figures.

The three figures below were assembled from selected rerun media before the
repo-resident packaging script owned the later 0036/0066 panels:

- paper/shared/figures/fig_internnav_downstream_panel.png
- paper/shared/figures/fig_internnav_rollout_stills.png
- paper/shared/figures/fig_internnav_rollout_selected6_supp.png

This file intentionally does not regenerate those legacy PNGs. It exists so
`paper/shared/figures/sources.yaml` can point to a concrete, auditable
repo-resident provenance file instead of a non-path sentinel string.
"""

from __future__ import annotations


LEGACY_OUTPUTS = [
    "paper/shared/figures/fig_internnav_downstream_panel.png",
    "paper/shared/figures/fig_internnav_rollout_stills.png",
    "paper/shared/figures/fig_internnav_rollout_selected6_supp.png",
]


def main() -> int:
    for output in LEGACY_OUTPUTS:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
