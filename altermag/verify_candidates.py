#!/usr/bin/env python3
"""
Verify the model's top MP altermagnet candidates with amcheck at IDEAL symmetry.

The model flags ~454 MP materials as likely altermagnets, but MP's own pipeline
labeled most "AFM" -- because MP-amcheck ran at the DFT-relaxed (distorted) cell,
where the rotation that enables altermagnetism is broken. This script re-fetches
each candidate's structure + experimental-style magmoms and re-runs amcheck across
LOOSER symmetry tolerances (up to 0.1), to see which flip AFM->AM once the tiny
DFT distortions are symmetrized away. Flips are the real, amcheck-confirmed finds.

Needs MP_API_KEY in the environment.

Usage:
    MP_API_KEY=... python verify_candidates.py \
        --candidates mp_high_confidence_candidates.csv --out verified_candidates.csv
"""

import argparse
import csv
import os
import sys

from pull_and_label import label_structure


def main():
    ap = argparse.ArgumentParser(description="amcheck-verify MP AM candidates")
    ap.add_argument("--candidates", default="mp_high_confidence_candidates.csv")
    ap.add_argument("--out", default="verified_candidates.csv")
    ap.add_argument("--tols", nargs="+", type=float,
                    default=[1e-3, 1e-2, 5e-2, 1e-1])
    ap.add_argument("--moment-threshold", type=float, default=0.05)
    args = ap.parse_args()

    key = os.environ.get("MP_API_KEY")
    if not key:
        sys.exit("Set MP_API_KEY in the environment.")

    # Candidate ids (strip .cif).
    ids = []
    with open(args.candidates, newline="") as fh:
        for row in csv.DictReader(fh):
            ids.append(row["file"].replace(".cif", ""))
    print(f"Verifying {len(ids)} candidates at tols {args.tols} ...")

    from mp_api.client import MPRester
    with MPRester(key) as mpr:
        sdocs = mpr.materials.summary.search(
            material_ids=ids, fields=["material_id", "structure", "formula_pretty"])
        struct_by_id = {str(d.material_id): d.structure for d in sdocs}
        fpretty = {str(d.material_id): d.formula_pretty for d in sdocs}
        mdocs = mpr.materials.magnetism.search(
            material_ids=ids, fields=["material_id", "magmoms"])
        magmoms_by_id = {str(d.material_id): getattr(d, "magmoms", None) for d in mdocs}

    tol_cols = [f"AM@{t:g}" for t in args.tols]
    fields = ["material_id", "formula", "ideal_verdict", "flipped"] + tol_cols
    counts = {}
    flips = 0
    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for mid in ids:
            s = struct_by_id.get(mid)
            mm = magmoms_by_id.get(mid)
            if s is None or mm is None:
                counts["NO-DATA"] = counts.get("NO-DATA", 0) + 1
                continue
            try:
                verdict, _, _, per_tol = label_structure(
                    s, mm, args.tols, args.moment_threshold)
            except Exception:
                counts["ERROR"] = counts.get("ERROR", 0) + 1
                continue
            # "ideal" verdict = at the loosest tolerance; flipped = AM at loose but
            # not at tight (1e-3) i.e. altermagnetism only emerges once symmetrized.
            loose = per_tol[args.tols[-1]]
            tight = per_tol[args.tols[0]]
            flipped = (loose == "AM" and tight != "AM")
            flips += int(flipped)
            counts[verdict] = counts.get(verdict, 0) + 1
            row = {"material_id": mid, "formula": fpretty.get(mid, ""),
                   "ideal_verdict": verdict, "flipped": "YES" if flipped else ""}
            for t in args.tols:
                row[f"AM@{t:g}"] = per_tol[t]
            w.writerow(row)

    print("\nVerdict counts (full tolerance sweep):")
    for k, v in sorted(counts.items()):
        print(f"  {k:14s} {v}")
    print(f"\n{flips} candidates flip AFM(tight) -> AM(symmetrized).")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
