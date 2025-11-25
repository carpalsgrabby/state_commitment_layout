from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sweep state_commitment_layout over leaf counts + fanouts."
    )
    parser.add_argument(
        "--style",
        required=True,
        choices=["aztec", "zama", "soundness"],
        help="Commitment style to use.",
    )
        parser.add_argument(
        "--json-summary",
        action="store_true",
        help="Emit a JSON summary of all rows to stdout after the table.",
    )

    parser.add_argument(
        "--leaf-min",
        type=int,
        required=True,
        help="Minimum number of leaves (inclusive).",
    )
    parser.add_argument(
        "--leaf-max",
        type=int,
        required=True,
        help="Maximum number of leaves (inclusive).",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=2,
        help=(
            "Log2 step between leaf counts. "
            "Example: leaf-min=1024 leaf-max=65536 step=2 -> 1024,4096,16384,65536."
        ),
    )
    parser.add_argument(
        "--fanouts",
        nargs="+",
        type=int,
        default=[2, 4, 8],
        help="Fanouts to test (default: 2 4 8).",
    )
    parser.add_argument(
        "--app-path",
        type=str,
        default="app.py",
        help="Path to app.py (default: ./app.py).",
    )
    parser.add_argument(
        "--raw-json",
        action="store_true",
        help="Also dump raw JSON lines for each configuration.",
    )
    return parser.parse_args()


def generate_leaf_counts(leaf_min: int, leaf_max: int, step: int) -> List[int]:
    if leaf_min <= 0 or leaf_max < leaf_min:
        raise ValueError("leaf-min must be > 0 and <= leaf-max")

    counts: List[int] = []
    # interpret step as increment in log2 space
    start_pow = math.log2(leaf_min)
    end_pow = math.log2(leaf_max)

    # if not exact powers of two, just linearly step instead
    if not start_pow.is_integer() or not end_pow.is_integer():
        n = leaf_min
        while n <= leaf_max:
            counts.append(int(n))
            n *= 2
        return counts

    p = int(start_pow)
    while p <= int(end_pow):
        counts.append(2**p)
        p += step
    return counts


def run_app(
    app_path: Path, leaves: int, style: str, fanout: int
) -> Dict[str, Any]:
    cmd = [
        sys.executable,
        str(app_path),
        str(leaves),
        "--style",
        style,
        "--fanout",
        str(fanout),
        "--json",
    ]
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"app.py exited with {result.returncode} "
            f"for leaves={leaves}, style={style}, fanout={fanout}.\n"
            f"stderr:\n{result.stderr}"
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse JSON from app.py for leaves={leaves}, fanout={fanout}: {e}\n"
            f"stdout:\n{result.stdout}"
        ) from e

    return data


def main() -> None:
    args = parse_args()
if args.leaves <= 0:
        print("ERROR: --leaves must be > 0.", file=sys.stderr)
        sys.exit(1)
    app_path = Path(args.app_path)
    if not app_path.is_file():
        print(f"ERROR: app.py not found at {app_path}", file=sys.stderr)
        sys.exit(1)

    leaf_counts = generate_leaf_counts(args.leaf_min, args.leaf_max, args.step)

    rows = []
    raw_json_lines = []

    for leaves in leaf_counts:
        for fanout in args.fanouts:
            try:
                data = run_app(app_path, leaves, args.style, fanout)
            except Exception as e:  # noqa: BLE001
                print(f"ERROR: {e}", file=sys.stderr)
                continue

            # keys are based on README description; tweak if you change app.py
            tree_height = data.get("treeHeight")
            total_nodes = data.get("totalNodes")
            proof_branch = data.get("proofBranchLength")
            per_proof_bytes = data.get("perProofBytes")
            total_commitment_bytes = data.get("totalCommitmentBytes")

            rows.append(
                {
                    "leaves": leaves,
                    "fanout": fanout,
                    "treeHeight": tree_height,
                    "totalNodes": total_nodes,
                    "proofBranchLength": proof_branch,
                    "perProofBytes": per_proof_bytes,
                    "totalCommitmentBytes": total_commitment_bytes,
                }
            )

            if args.raw_json:
                raw_json_lines.append(
                    {
                        "style": args.style,
                        "leaves": leaves,
                        "fanout": fanout,
                        "raw": data,
                    }
                )

    if not rows:
        print("No data rows collected (maybe app.py failed?).", file=sys.stderr)
        sys.exit(1)

    # Print a simple table
    header = (
        f"{'LEAVES':>10}  {'FANOUT':>6}  {'HEIGHT':>6}  "
        f"{'NODES':>12}  {'PROOF BYTES':>12}  {'TOTAL COMM BYTES':>16}"
    )
    print(header)
    print("-" * len(header))

    for r in rows:
        print(
            f"{r['leaves']:10d}  {r['fanout']:6d}  "
            f"{(r['treeHeight'] or 0):6d}  "
            f"{(r['totalNodes'] or 0):12d}  "
            f"{(r['perProofBytes'] or 0):12d}  "
            f"{(r['totalCommitmentBytes'] or 0):16d}"
        )
    if args.json_summary:
        summary = {
            "style": args.style,
            "rows": rows,
        }
        # If rows is a list of dataclasses, convert them:
        def row_to_dict(r: Any) -> Dict[str, Any]:
            if hasattr(r, "__dict__"):
                return r.__dict__
            return r

        print(json.dumps(
            {
                "style": args.style,
                "rows": [row_to_dict(r) for r in rows],
            },
            indent=2,
        ))

    if args.raw_json:
        print("\n# Raw JSON lines (one per config):")
        for entry in raw_json_lines:
            print(json.dumps(entry, separators=(",", ":")))


if __name__ == "__main__":
    main()
