#!/usr/bin/env python3
"""
Label MAGNDATA .mcif files into a trusted AM/AFM validation set.

Unlike the Materials Project pull (DFT-derived, noisy), MAGNDATA structures
carry EXPERIMENTALLY-determined magnetic moments. We read those moments straight
out of each .mcif with pymatgen and run the SAME amcheck classifier used in
pull_and_label.py, so the resulting labels are trustworthy ground truth.

Usage:
    python label_mcif.py --indir ./mcif --out ./mcif/validation_labels.csv
"""

import argparse
import csv
import sys
import traceback
from pathlib import Path

import numpy as np
from pymatgen.io.cif import CifParser

# Reuse the exact labeling logic from the MP pipeline.
from pull_and_label import label_structure


def magmoms_from_structure(struct):
    """Collinear scalar magmoms from an .mcif's per-site Magnetic moment vectors.

    MAGNDATA moments may be vectors; collapse each to the dominant component so
    spins_from_magmoms (which expects scalars) gets a clean signed magnitude."""
    prop = struct.site_properties.get("magmom")
    if prop is None:
        raise ValueError("no magmom site property in this mcif")
    out = []
    for m in prop:
        arr = np.atleast_1d(np.asarray(getattr(m, "moment", m), dtype=float))
        out.append(float(arr[np.argmax(np.abs(arr))]) if arr.size else 0.0)
    return out


def main():
    ap = argparse.ArgumentParser(description="Label MAGNDATA mcif -> trusted CSV")
    ap.add_argument("--indir", default="mcif", help="directory of .mcif files")
    ap.add_argument("--out", default="mcif/validation_labels.csv")
    ap.add_argument("--tols", nargs="+", type=float,
                    default=[1e-5, 1e-4, 1e-3, 1e-2])
    ap.add_argument("--moment-threshold", type=float, default=0.05)
    args = ap.parse_args()

    indir = Path(args.indir)
    files = sorted(indir.glob("*.mcif"))
    if not files:
        sys.exit(f"No .mcif files in {indir}")

    fieldnames = (["file", "formula", "spacegroup", "n_sites", "net_moment"]
                  + [f"AM@{t:g}" for t in args.tols] + ["verdict"])
    counts = {}
    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for path in files:
            fname = path.name
            try:
                struct = CifParser(str(path)).parse_structures(primitive=False)[0]
                magmoms = magmoms_from_structure(struct)
                verdict, sg, net, per_tol = label_structure(
                    struct, magmoms, args.tols, args.moment_threshold)
                row = {
                    "file": fname,
                    "formula": struct.composition.reduced_formula,
                    "spacegroup": sg,
                    "n_sites": len(struct),
                    "net_moment": f"{net:.3f}",
                    "verdict": verdict,
                }
                for t in args.tols:
                    row[f"AM@{t:g}"] = per_tol[t]
                writer.writerow(row)
                counts[verdict] = counts.get(verdict, 0) + 1
                print(f"  {fname:32s} {row['formula']:14s} -> {verdict}")
            except Exception as e:  # noqa: BLE001
                counts["ERROR"] = counts.get("ERROR", 0) + 1
                sys.stderr.write(f"[ERROR] {fname}: {e}\n")
                sys.stderr.write(traceback.format_exc())

    print("\nSummary:")
    for k, v in sorted(counts.items()):
        print(f"  {k:14s} {v}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
