#!/usr/bin/env python3
"""
layout_sizer.py

Small helper script for state_commitment_layout.

Given a desired number of leaves and an arity (branching factor),
compute the basic k-ary tree layout parameters:

- minimal height such that arity**height >= leaves
- total nodes (internal + leaves)
- number of padding leaves required to fill the last level

Example:
    python layout_sizer.py --leaves 1_000_000 --arity 4
    python layout_sizer.py --leaves 1_000_000 --arity 4 --json
"""

import argparse
import json
import math
import sys
from typing import Dict, Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute basic k-ary commitment tree layout statistics "
            "for a given number of leaves and arity."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--leaves",
        type=int,
        required=True,
        help="Number of real leaves / state entries.",
    )
    parser.add_argument(
        "--arity",
        type=int,
        default=2,
        help="Branching factor (k-ary tree arity, e.g. 2, 4, 8).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable summary.",
    )
    return parser.parse_args()


def compute_layout(leaves: int, arity: int) -> Dict[str, Any]:
    if leaves <= 0:
        print("❌ --leaves must be > 0", file=sys.stderr)
        sys.exit(2)
    if arity <= 1:
        print("❌ --arity must be >= 2", file=sys.stderr)
        sys.exit(2)

    # Minimal height h such that arity**h >= leaves
    # height = number of levels from leaves to root (leaf level = h, root = 0)
    height = math.ceil(math.log(leaves, arity))

    # Total leaves in a full k-ary tree at that height
    full_leaves = arity ** height

    padding_leaves = full_leaves - leaves

    # Total nodes in a full k-ary tree of height h (root at level 0, leaves at h):
    # sum_{i=0}^{h} arity**i
    total_nodes = (arity ** (height + 1) - 1) // (arity - 1)

    # Leaves are the last level; everything else is internal
    internal_nodes = total_nodes - full_leaves

    return {
        "leaves": leaves,
        "arity": arity,
        "height": height,
        "fullLeaves": full_leaves,
        "paddingLeaves": padding_leaves,
        "totalNodes": total_nodes,
        "internalNodes": internal_nodes,
        "leafNodes": full_leaves,
    }


def print_human(layout: Dict[str, Any]) -> None:
    print("state_commitment_layout :: tree sizing")
    print(f"  leaves           : {layout['leaves']}")
    print(f"  arity            : {layout['arity']}")
    print()
    print(f"  height (levels)  : {layout['height']}")
    print(f"  leaf nodes       : {layout['leafNodes']}")
    print(f"  internal nodes   : {layout['internalNodes']}")
    print(f"  total nodes      : {layout['totalNodes']}")
    print()
    print(f"  padding leaves   : {layout['paddingLeaves']}")
    if layout["paddingLeaves"] > 0:
        frac = layout["paddingLeaves"] / layout["leafNodes"]
        print(f"  padding fraction : {frac:.4%}")
    else:
        print("  padding fraction : 0%")


def main() -> None:
    args = parse_args()
    layout = compute_layout(args.leaves, args.arity)

    if args.json:
        print(json.dumps(layout, indent=2, sort_keys=True))
    else:
        print_human(layout)


if __name__ == "__main__":
    main()
