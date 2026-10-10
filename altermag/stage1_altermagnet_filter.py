#!/usr/bin/env python3
"""
Stage 1 altermagnet symmetry pre-filter.

Reads magnetic CIF (.mcif) files (e.g. from MAGNDATA) and, for each one, runs
amcheck's symmetry test to classify it as altermagnet (AM) vs conventional
antiferromagnet (AFM) -- WITHOUT any DFT. The test is run across a sweep of
spglib symmetry tolerances; any structure whose classification *changes*
across tolerances is flagged for human review (the "tolerance gate").

This is the cheap kill-stage of a high-throughput altermagnet screen: it
discards the large majority of magnetic structures before you ever spend a
DFT cycle.

What this DOES:  symmetry classification (AM vs AFM) given the magnetic pattern.
What this does NOT do:  measure spin-splitting magnitude or metallicity.
    Those are Stage 2/3 (DFT) and are a separate, expensive step.

Dependencies:
    pip install amcheck pymatgen spglib numpy

Usage:
    python stage1_altermagnet_filter.py --indir ./mcif --out results.csv
    python stage1_altermagnet_filter.py --indir ./mcif --out results.csv \
        --tols 1e-5 1e-4 1e-3 1e-2

Output CSV columns:
    file, formula, spacegroup, n_sites, net_moment, <AM@tol per tolerance>, verdict
where verdict is one of:
    AM            -> altermagnet at EVERY tolerance      (promote to Stage 2)
    AFM           -> antiferromagnet at every tolerance  (discard)
    REVIEW-FLIP   -> classification changed across tols   (hand-check: the gate)
    SKIP-FM       -> net moment too large; not compensated (amcheck N/A)
    ERROR         -> parse/classify failure (see stderr log)
"""

import argparse
import csv
import sys
import traceback
from pathlib import Path

import numpy as np


def get_dataset_field(dataset, name):
    """spglib >= 2.5 returns a dataclass; older versions return a dict.
    Support both so the script doesn't break on a version bump."""
    if hasattr(dataset, name):
        return getattr(dataset, name)
    return dataset[name]


def load_structure_and_spins(path, moment_threshold=0.05):
    """
    Parse an mcif into the inputs amcheck/spglib need:
        lattice (3x3), fractional positions (N,3), atomic numbers (N,),
        chemical symbols (N,), spin labels (N,) in {'u','d','n'},
        net-moment magnitude, reduced formula.

    Spin labels are derived from the per-site magnetic moments: we pick a
    global collinear axis (direction of the largest moment), project every
    moment onto it, and assign 'u'/'d' by sign ('n' if negligible).

    NOTE: this collinear-axis projection is the single most likely thing you
    will need to adjust for edge cases (genuinely non-collinear inputs, or
    unusual mcif moment conventions). Validate on known cases first.
    """
    from pymatgen.io.cif import CifParser

    parser = CifParser(str(path))
    structures = parser.parse_structures(primitive=False)
    if not structures:
        raise ValueError("no structure parsed from file")
    struct = structures[0]

    magmoms = struct.site_properties.get("magmom")
    if magmoms is None:
        raise ValueError("no magnetic moments found (is this actually a magCIF?)")

    # Convert pymatgen Magmom objects to plain 3-vectors.
    vecs = []
    for m in magmoms:
        try:
            v = np.asarray(m.moment, dtype=float)     # Magmom -> Cartesian vector
        except AttributeError:
            v = np.asarray(m, dtype=float)            # already array-like
        if v.shape != (3,):
            v = np.array([0.0, 0.0, float(v)])        # scalar fallback
        vecs.append(v)
    vecs = np.asarray(vecs)

    net = float(np.linalg.norm(vecs.sum(axis=0)))

    mags = np.linalg.norm(vecs, axis=1)
    if mags.max() < moment_threshold:
        raise ValueError("all site moments are negligible")

    # Global collinear axis = direction of the largest-magnitude moment.
    axis = vecs[mags.argmax()] / mags[mags.argmax()]

    spins = []
    for v in vecs:
        proj = float(np.dot(v, axis))
        if abs(proj) < moment_threshold:
            spins.append("n")
        elif proj > 0:
            spins.append("u")
        else:
            spins.append("d")

    lattice = struct.lattice.matrix
    positions = struct.frac_coords
    numbers = np.array([site.specie.Z for site in struct])
    symbols = [site.specie.symbol for site in struct]
    formula = struct.composition.reduced_formula
    return lattice, positions, numbers, symbols, spins, net, formula


def classify_one(lattice, positions, numbers, symbols, spins, symprec):
    """Run amcheck at a single spglib tolerance. Returns (is_AM, spacegroup_str)."""
    import spglib
    from amcheck import is_altermagnet

    cell = (lattice, positions, numbers)
    dataset = spglib.get_symmetry_dataset(cell, symprec=symprec)
    if dataset is None:
        raise ValueError(f"spglib found no symmetry at symprec={symprec}")

    rotations = get_dataset_field(dataset, "rotations")
    translations = get_dataset_field(dataset, "translations")
    equiv = get_dataset_field(dataset, "equivalent_atoms")
    intl = get_dataset_field(dataset, "international")
    number = get_dataset_field(dataset, "number")
    spacegroup = f"{intl} ({number})"

    sym_ops = [
        (np.asarray(r, dtype=int), np.asarray(t, dtype=float))
        for r, t in zip(rotations, translations)
    ]

    is_am = is_altermagnet(
        sym_ops,
        np.asarray(positions, dtype=float),
        list(equiv),
        list(symbols),
        list(spins),
    )
    return bool(is_am), spacegroup


def process_file(path, tols, moment_threshold):
    """Run the full tolerance sweep on one file and return a result row (dict)."""
    row = {
        "file": path.name,
        "formula": "",
        "spacegroup": "",
        "n_sites": "",
        "net_moment": "",
        "verdict": "",
    }
    for t in tols:
        row[f"AM@{t:g}"] = ""

    try:
        lattice, positions, numbers, symbols, spins, net, formula = (
            load_structure_and_spins(path, moment_threshold)
        )
        row["formula"] = formula
        row["n_sites"] = len(symbols)
        row["net_moment"] = f"{net:.3f}"

        # amcheck assumes a compensated (net-zero-moment) magnet.
        if net > moment_threshold:
            row["verdict"] = "SKIP-FM"
            return row

        results = {}
        sg = ""
        for t in tols:
            try:
                is_am, sg = classify_one(
                    lattice, positions, numbers, symbols, spins, t
                )
                results[t] = is_am
                row[f"AM@{t:g}"] = "AM" if is_am else "AFM"
            except Exception as e:  # noqa: BLE001
                results[t] = None
                row[f"AM@{t:g}"] = f"err:{type(e).__name__}"
        row["spacegroup"] = sg

        vals = {v for v in results.values() if v is not None}
        if not vals:
            row["verdict"] = "ERROR"
        elif len(vals) > 1:
            row["verdict"] = "REVIEW-FLIP"     # tolerance gate caught instability
        elif True in vals:
            row["verdict"] = "AM"
        else:
            row["verdict"] = "AFM"
    except Exception as e:  # noqa: BLE001
        row["verdict"] = "ERROR"
        sys.stderr.write(f"[ERROR] {path.name}: {e}\n")
        sys.stderr.write(traceback.format_exc())
    return row


def main():
    ap = argparse.ArgumentParser(
        description="Stage 1 altermagnet symmetry pre-filter (amcheck + spglib)"
    )
    ap.add_argument("--indir", required=True, help="directory of .mcif / .cif files")
    ap.add_argument("--out", default="stage1_results.csv", help="output CSV path")
    ap.add_argument(
        "--tols", nargs="+", type=float, default=[1e-5, 1e-4, 1e-3, 1e-2],
        help="spglib symmetry tolerances to sweep (the gate)",
    )
    ap.add_argument(
        "--moment-threshold", type=float, default=0.05,
        help="|moment| below this is treated as non-magnetic; a NET moment above "
             "this means the structure is not compensated and is skipped",
    )
    args = ap.parse_args()

    indir = Path(args.indir)
    files = sorted(indir.glob("*.mcif")) + sorted(indir.glob("*.cif"))
    if not files:
        sys.exit(f"No .mcif/.cif files found in {indir}")

    fieldnames = (
        ["file", "formula", "spacegroup", "n_sites", "net_moment"]
        + [f"AM@{t:g}" for t in args.tols]
        + ["verdict"]
    )

    counts = {}
    # Write incrementally + flush so a crash mid-batch never loses finished work.
    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for i, path in enumerate(files, 1):
            r = process_file(path, args.tols, args.moment_threshold)
            writer.writerow(r)
            fh.flush()
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
            print(f"[{i}/{len(files)}] {path.name:42s} -> {r['verdict']}")

    print("\nSummary:")
    for k in ("AM", "AFM", "REVIEW-FLIP", "SKIP-FM", "ERROR"):
        if k in counts:
            print(f"  {k:12s} {counts[k]}")
    print(
        f"\nWrote {args.out}. Promote verdict=AM rows to Stage 2 (DFT); "
        f"hand-check REVIEW-FLIP rows."
    )


if __name__ == "__main__":
    main()
