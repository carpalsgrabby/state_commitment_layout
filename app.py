#!/usr/bin/env python3
import argparse
import json
import math
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class StyleProfile:
    key: str
    name: str
    hash_bytes: int
    note: str


STYLES: Dict[str, StyleProfile] = {
    "aztec": StyleProfile(
        key="aztec",
        name="Aztec-style privacy rollup",
        hash_bytes=32,
        note="Optimised for zk commitments over encrypted state roots.",
    ),
    "zama": StyleProfile(
        key="zama",
        name="Zama-style FHE compute stack",
        hash_bytes=48,
        note="FHE-heavy designs often tolerate slightly larger commitments.",
    ),
    "soundness": StyleProfile(
        key="soundness",
        name="Soundness-first protocol lab",
        hash_bytes=32,
        note="Prefers simple, standard-sized commitments for verifiable semantics.",
    ),
}


def clamp_int(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def estimate_tree(leaves: int, fanout: int) -> Dict[str, Any]:
    if leaves <= 0:
        raise ValueError("leaves must be positive")
    if fanout not in (2, 4, 8):
        raise ValueError("fanout must be one of 2, 4, or 8")

    height = 0
    nodes = leaves
    total_nodes = 0
    per_level = []

    while nodes > 1:
        per_level.append(nodes)
        total_nodes += nodes
        height += 1
        nodes = math.ceil(nodes / fanout)

    per_level.append(nodes)
    total_nodes += nodes

    return {
        "height": height,
        "totalNodes": total_nodes,
        "nodesPerLevel": per_level,
    }


def build_layout(style: StyleProfile, leaves: int, fanout: int) -> Dict[str, Any]:
    tree = estimate_tree(leaves, fanout)
    hash_bytes = style.hash_bytes

    proof_branch_length = tree["height"]
    per_proof_bytes = (proof_branch_length + 1) * hash_bytes  # path plus root
    per_proof_bits = per_proof_bytes * 8
    total_commitment_bytes = tree["totalNodes"] * hash_bytes

    return {
        "style": style.key,
        "styleName": style.name,
        "note": style.note,
        "leaves": leaves,
        "fanout": fanout,
        "treeHeight": tree["height"],
        "totalNodes": tree["totalNodes"],
        "nodesPerLevel": tree["nodesPerLevel"],
        "hashBytes": hash_bytes,
        "proofBranchLength": proof_branch_length,
        "perProofBytes": per_proof_bytes,
        "perProofBits": per_proof_bits,
        "totalCommitmentBytes": total_commitment_bytes,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="state_commitment_layout",
        description=(
            "Tiny state commitment layout helper inspired by Aztec-style zk rollups, "
            "Zama-style FHE stacks, and soundness-focused protocols."
        ),
    )
    p.add_argument(
        "leaves",
        type=int,
        help="Number of leaf entries in the state tree.",
    )
    p.add_argument(
        "--style",
        choices=list(STYLES.keys()),
        default="aztec",
        help="Commitment style profile (aztec, zama, soundness).",
    )
    p.add_argument(
        "--fanout",
        type=int,
        choices=[2, 4, 8],
        default=2,
        help="Tree fanout per level (2, 4, or 8). Default: 2.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of human-readable text.",
    )
    return p.parse_args()


def print_human(layout: Dict[str, Any]) -> None:
    print("🌳 state_commitment_layout")
    print(f"Style        : {layout['styleName']} ({layout['style']})")
    print(f"Note         : {layout['note']}")
    print("")
    print(f"Leaves       : {layout['leaves']}")
    print(f"Fanout       : {layout['fanout']}")
    print(f"Hash bytes   : {layout['hashBytes']}")
    print("")
    print("Tree shape:")
    print(f"  Height          : {layout['treeHeight']}")
    print(f"  Total nodes     : {layout['totalNodes']}")
    print(f"  Nodes per level : {layout['nodesPerLevel']}")
    print("")
    print("Proof / commitment estimates:")
    print(f"  Branch length   : {layout['proofBranchLength']} nodes")
    print(f"  Per-proof bytes : {layout['perProofBytes']} bytes")
    print(f"  Per-proof bits  : {layout['perProofBits']} bits")
    print(f"  Commitment size : {layout['totalCommitmentBytes']} bytes (all nodes)")


def main() -> None:
    args = parse_args()
    leaves = clamp_int(args.leaves, 1, 10_000_000)
    style = STYLES[args.style]

    layout = build_layout(style, leaves, args.fanout)

    if args.json:
        print(json.dumps(layout, indent=2, sort_keys=True))
    else:
        print_human(layout)


if __name__ == "__main__":
    main()
