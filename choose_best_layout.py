#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

__all__ = ["LayoutResult", "parse_args", "run_app", "metric_value", "main"]

@dataclass
class LayoutResult:
    fanout: int
    data: Dict[str, Any]


METRICS = [
    "treeHeight",
    "totalNodes",
    "proofBranchLength",
    "perProofBytes",
    "totalCommitmentBytes",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Choose best state commitment layout for given leaves/style."
    )
    p.add_argument(
        "--leaves",
        type=int,
        required=True,
        help="Number of leaves in the tree.",
    )
    p.add_argument(
        "--style",
        choices=["aztec", "zama", "soundness"],
        required=True,
        help="Commitment style to use.",
    )
    p.add_argument(
        "--fanouts",
        nargs="+",
        type=int,
        default=[2, 4, 8, 16],
        help="Fanouts to test (default: 2 4 8 16).",
    )
    p.add_argument(
        "--metric",
        choices=METRICS,
        default="totalCommitmentBytes",
        help=f"Metric to minimize when choosing best layout (default: totalCommitmentBytes).",
    )
    p.add_argument(
        "--app-path",
        type=str,
        default="app.py",
        help="Path to app.py (default: ./app.py).",
    )
    return p.parse_args()


def run_app(app_path: Path, leaves: int, style: str, fanout: int) -> Dict[str, Any]:
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
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse JSON from app.py for leaves={leaves}, fanout={fanout}: {e}\n"
            f"stdout:\n{result.stdout}"
        ) from e


def metric_value(data: Dict[str, Any], metric: str) -> float:
    val = data.get(metric)
    if val is None:
        # treat missing metrics as infinite (worst)
        return float("inf")
    return float(val)


def main() -> None:
    args = parse_args()

    app_path = Path(args.app_path)
    if not app_path.is_file():
        print(f"ERROR: app.py not found at {app_path}", file=sys.stderr)
        sys.exit(1)

    layouts: List[LayoutResult] = []

    for f in args.fanouts:
        try:
            data = run_app(app_path, args.leaves, args.style, f)
            layouts.append(LayoutResult(fanout=f, data=data))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR for fanout={f}: {e}", file=sys.stderr)

    if not layouts:
        print("No successful layouts computed. (Did app.py error out for all?)", file=sys.stderr)
        sys.exit(1)

    # choose best by metric (minimize)
    best = min(
        layouts,
        key=lambda lr: metric_value(lr.data, args.metric),
    )

    # Print table
    header = (
        f"{'FANOUT':>6}  {'HEIGHT':>6}  {'NODES':>10}  "
        f"{'BRANCH':>8}  {'PROOF BYTES':>12}  {'TOTAL COMM BYTES':>16}  {'METRIC':>12}"
    )
    print(header)
    print("-" * len(header))

    for lr in layouts:
        d = lr.data
        fanout = lr.fanout
        height = d.get("treeHeight", 0)
        nodes = d.get("totalNodes", 0)
        branch = d.get("proofBranchLength", 0)
        proof_b = d.get("perProofBytes", 0)
        total_b = d.get("totalCommitmentBytes", 0)
        mval = metric_value(d, args.metric)

        mark = "*" if lr.fanout == best.fanout else " "
        print(
            f"{fanout:6d}  {height:6d}  {nodes:10d}  "
            f"{branch:8d}  {proof_b:12d}  {total_b:16d}  {mval:12.2f}{mark}"
        )

    print()
    print(
        f"Best fanout for leaves={args.leaves}, style={args.style}, "
        f"metric={args.metric}: {best.fanout} (marked with *)"
    )


if __name__ == "__main__":
    main()
