# state_commitment_layout

A tiny CLI tool that sketches Merkle-style state commitment layouts for Web3 projects.

It is conceptually inspired by:

- Aztec-style zk privacy rollups
- Zama-style FHE compute stacks
- Soundness-first protocol labs

The goal is to quickly reason about:

- tree height
- number of nodes
- proof branch length
- approximate proof size in bytes and bits

for different commitment styles and tree fanouts.


Repository contents

This repository intentionally contains exactly two files:

- app.py
- README.md


Concept

Different Web3 projects make different trade-offs:

- Aztec-style rollups care about zk-friendly commitment sizes over encrypted state.
- Zama-style stacks may tolerate larger commitments due to FHE-heavy pipelines.
- Soundness-first protocols often prefer standard, simple commitments that are easy to reason about formally.

state_commitment_layout does not connect to any chain or RPC. It is a pure calculation tool:

- You choose a style (aztec, zama, soundness).
- You choose how many leaf entries your state tree has.
- You choose a tree fanout (2, 4, or 8).
- The tool computes a basic tree layout and rough proof sizes.


Installation

Requirements:

- Python 3.8 or newer

Steps:

1. Create a new GitHub repository with any name.
2. Add app.py and this README.md to the repository root.
3. Ensure the python command is available in your shell.
4. No external dependencies are needed; only the standard library is used.


Usage

All commands below assume you are in the repository root.

Basic Aztec-style layout for 65 536 accounts:

python app.py 65536 --style aztec --fanout 2

Zama-style FHE layout with higher fanout:

python app.py 100000 --style zama --fanout 4

Soundness-first layout with very large state:

python app.py 1000000 --style soundness --fanout 2

JSON output for dashboards or scripts:

python app.py 100000 --style aztec --fanout 2 --json


Output

Human-readable output prints:

- style name, key, and a short note
- number of leaves and fanout
- hash size in bytes
- tree height
- total number of nodes
- nodesPerLevel (array)
- proofBranchLength (how many hashes needed in a Merkle proof)
- perProofBytes and perProofBits
- totalCommitmentBytes (hash_bytes × total_nodes)

JSON mode prints the same fields in a machine-readable object.


Notes

- All numbers are illustrative and do not include optimisations like subtree commitments or batching schemes.
- This tool does not model gas costs or real curve/hash performance.
- You are encouraged to tweak STYLES and the hash_bytes assumptions in app.py to better match your own Aztec-like, Zama-like, or soundness-first systems.
