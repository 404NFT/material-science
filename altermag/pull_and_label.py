#!/usr/bin/env python3
"""
Pull AFM structures from the Materials Project and label them AM vs AFM.

Fetches antiferromagnetic materials (ordering + DFT per-site magmoms) from MP's
magnetism endpoint, fetches their structures from the summary endpoint, derives
a collinear spin pattern from the magmoms, and runs the SAME amcheck
tolerance-sweep used in Stage 1 to label each as altermagnet (AM) or
conventional antiferromagnet (AFM).

It writes outputs in Stage 1's format -- a folder of .cif files plus a
results.csv with file/verdict columns -- so your existing
featurize_candidates.py consumes them with no changes.

Requires Python >= 3.10 (mp-api/emmet dropped 3.9).
Dependencies:
    pip install mp-api pymatgen spglib amcheck numpy

API key:
    Get one from your Materials Project dashboard (materialsproject.org).
    Pass --api-key, or set the MP_API_KEY environment variable.

Usage:
    export MP_API_KEY="...your key..."
    python pull_and_label.py --outdir ./mp_data --num-chunks 5 --max-keep 300

Output (in --outdir):
    <material_id>.cif        one per kept structure
    results.csv              file, formula, spacegroup, n_sites, net_moment,
                             AM@<tol>..., verdict   (verdict vocabulary matches
                             Stage 1: AM / AFM / REVIEW-FLIP / SKIP-FM / ERROR)

LABEL-QUALITY CAVEAT:
    MP orderings/magmoms are DFT-computed (r2SCAN), noisier than MAGNDATA's
    experimental structures. Train on this volume, but VALIDATE on your trusted
    MAGNDATA cases -- keep those two sets separate. (See note at end of run.)

LICENSE NOTE:
    MP data is CC-BY-4.0, but GNoME-originated structures are BY-NC
    (non-commercial). If you ever commercialize, filter those out.
"""

import argparse
import csv
import os
import sys
import traceback
from pathlib import Path

import numpy as np
from pymatgen.analysis.magnetism import Ordering


def get_dataset_field(dataset, name):
    """spglib >= 2.5 returns a dataclass; older returns a dict."""
    if hasattr(dataset, name):
        return getattr(dataset, name)
    return dataset[name]


def spins_from_magmoms(magmoms, threshold):
    """Collinear spin labels from MP magmoms (scalars). Returns (spins, net)."""
    vals = []
    for m in magmoms:
        arr = np.atleast_1d(np.asarray(m, dtype=float))
        # MP collinear magmoms are scalars; if a vector slips through, take the
        # dominant component.
        vals.append(float(arr[0]) if arr.size == 1
                    else float(arr[np.argmax(np.abs(arr))]))
    vals = np.asarray(vals)
    net = float(abs(vals.sum()))
    spins = ["n" if abs(v) < threshold else ("u" if v > 0 else "d") for v in vals]
    return spins, net


def classify(structure, spins, symprec):
    """amcheck verdict at one tolerance. Returns (is_AM, spacegroup_str)."""
    import spglib
    from amcheck import is_altermagnet

    lattice = structure.lattice.matrix
    positions = structure.frac_coords
    numbers = [s.specie.Z for s in structure]       # raises on disordered sites
    symbols = [s.specie.symbol for s in structure]

    ds = spglib.get_symmetry_dataset((lattice, positions, numbers), symprec=symprec)
    if ds is None:
        raise ValueError(f"no symmetry at symprec={symprec}")
    rot = get_dataset_field(ds, "rotations")
    tr = get_dataset_field(ds, "translations")
    eq = get_dataset_field(ds, "equivalent_atoms")
    intl = get_dataset_field(ds, "international")
    num = get_dataset_field(ds, "number")

    sym_ops = [(np.asarray(r, dtype=int), np.asarray(t, dtype=float))
               for r, t in zip(rot, tr)]
    is_am = is_altermagnet(sym_ops, np.asarray(positions, dtype=float),
                           list(eq), list(symbols), list(spins))
    return bool(is_am), f"{intl} ({num})"


def label_structure(structure, magmoms, tols, moment_threshold):
    """Full tolerance sweep -> (verdict, spacegroup, net, per_tol_dict)."""
    if magmoms is None or len(magmoms) != len(structure):
        raise ValueError("magmoms missing or length mismatch with structure")
    spins, net = spins_from_magmoms(magmoms, moment_threshold)

    if net > moment_threshold:
        return "SKIP-FM", "", net, {t: "" for t in tols}

    # amcheck refuses to classify spin-uncompensated structures (unequal up/down
    # magnetic sites). MP may still tag these "AFM", but they cannot be
    # altermagnets by definition -> bucket them as a clean SKIP, not an error.
    n_up = spins.count("u")
    n_down = spins.count("d")
    if n_up != n_down:
        return "SKIP-UNCOMP", "", net, {t: "" for t in tols}

    results, per_tol, sg = {}, {}, ""
    for t in tols:
        try:
            is_am, sg = classify(structure, spins, t)
            results[t] = is_am
            per_tol[t] = "AM" if is_am else "AFM"
        except Exception as e:  # noqa: BLE001
            results[t] = None
            per_tol[t] = f"err:{type(e).__name__}"

    vals = {v for v in results.values() if v is not None}
    if not vals:
        verdict = "ERROR"
    elif len(vals) > 1:
        verdict = "REVIEW-FLIP"
    elif True in vals:
        verdict = "AM"
    else:
        verdict = "AFM"
    return verdict, sg, net, per_tol


def fetch_afm_docs(mpr, num_chunks, chunk_size, max_keep):
    """Return list of (material_id, structure, magmoms) for AFM materials.

    Neither endpoint carries everything: the summary endpoint has 'structure'
    but not 'magmoms', and the magnetism endpoint has 'magmoms' but not
    'structure' (and returns many deprecated IDs with no structure at all).
    So we pull non-deprecated AFM ids + structures from summary in one bulk
    call, then magmoms for those ids from the magnetism endpoint, and zip them.

    num_chunks=None pulls every chunk (all AFM materials). max_keep=None keeps
    all of them; otherwise the id list is truncated before any magmom fetch.
    """
    summary_docs = mpr.materials.summary.search(
        magnetic_ordering=Ordering.AFM,
        fields=["material_id", "structure"],
        num_chunks=num_chunks,
        chunk_size=chunk_size,
    )
    struct_by_id = {str(d.material_id): d.structure for d in summary_docs}
    mpids = list(struct_by_id.keys())
    if max_keep is not None:
        mpids = mpids[:max_keep]
    if not mpids:
        return []

    mag_docs = mpr.materials.magnetism.search(
        material_ids=mpids,
        fields=["material_id", "magmoms"],
    )
    magmoms_by_id = {str(d.material_id): getattr(d, "magmoms", None)
                     for d in mag_docs}

    return [(mid, struct_by_id[mid], magmoms_by_id.get(mid)) for mid in mpids]


def main():
    ap = argparse.ArgumentParser(
        description="Pull AFM structures from Materials Project and label AM/AFM"
    )
    ap.add_argument("--api-key", default=os.environ.get("MP_API_KEY"),
                    help="MP API key (or set MP_API_KEY env var)")
    ap.add_argument("--outdir", default="mp_data", help="output directory")
    ap.add_argument("--num-chunks", type=int, default=5,
                    help="how many chunks of AFM docs to scan (0 = all)")
    ap.add_argument("--chunk-size", type=int, default=1000, help="docs per chunk")
    ap.add_argument("--max-keep", type=int, default=300,
                    help="stop after writing this many structures (0 = no cap)")
    ap.add_argument("--tols", nargs="+", type=float,
                    default=[1e-5, 1e-4, 1e-3, 1e-2])
    ap.add_argument("--moment-threshold", type=float, default=0.05)
    args = ap.parse_args()

    if not args.api_key:
        sys.exit("No API key. Pass --api-key or set MP_API_KEY.")

    # 0 means "no limit" for both knobs.
    num_chunks = args.num_chunks if args.num_chunks > 0 else None
    max_keep = args.max_keep if args.max_keep > 0 else None

    try:
        from mp_api.client import MPRester
    except ImportError:
        sys.exit("mp-api not installed (needs Python >=3.10): pip install mp-api")
    from pymatgen.io.cif import CifWriter

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    fieldnames = (["file", "formula", "spacegroup", "n_sites", "net_moment"]
                  + [f"AM@{t:g}" for t in args.tols] + ["verdict"])
    counts, kept = {}, 0

    with open(outdir / "results.csv", "w", newline="") as fh, \
            MPRester(args.api_key) as mpr:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        # 1) Pull AFM ids + structures (summary) and magmoms (magnetism).
        print("Querying AFM docs (structures + magmoms) ...")
        afm_docs = fetch_afm_docs(mpr, num_chunks, args.chunk_size, max_keep)
        print(f"Got {len(afm_docs)} AFM materials.")

        # 2) Label + write.
        for mpid, structure, magmoms in afm_docs:
            if max_keep is not None and kept >= max_keep:
                break
            try:
                if structure is None:
                    counts["SKIP-NO-STRUCT"] = counts.get("SKIP-NO-STRUCT", 0) + 1
                    print(f"[SKIP] {mpid}: no structure available, skipping")
                    continue
                verdict, sg, net, per_tol = label_structure(
                    structure, magmoms,
                    args.tols, args.moment_threshold,
                )
                fname = f"{mpid}.cif"
                CifWriter(structure).write_file(outdir / fname)

                row = {
                    "file": fname,
                    "formula": structure.composition.reduced_formula,
                    "spacegroup": sg,
                    "n_sites": len(structure),
                    "net_moment": f"{net:.3f}",
                    "verdict": verdict,
                }
                for t in args.tols:
                    row[f"AM@{t:g}"] = per_tol[t]
                writer.writerow(row)
                fh.flush()
                counts[verdict] = counts.get(verdict, 0) + 1
                kept += 1
                print(f"[{kept}/{args.max_keep}] {mpid:14s} "
                      f"{row['formula']:14s} -> {verdict}")
            except Exception as e:  # noqa: BLE001
                counts["ERROR"] = counts.get("ERROR", 0) + 1
                sys.stderr.write(f"[ERROR] {mpid}: {e}\n")
                sys.stderr.write(traceback.format_exc())

    print("\nSummary:")
    for k in ("AM", "AFM", "REVIEW-FLIP", "SKIP-FM", "SKIP-UNCOMP",
              "SKIP-NO-STRUCT", "ERROR"):
        if k in counts:
            print(f"  {k:12s} {counts[k]}")
    print(f"\nWrote {kept} structures + results.csv to {outdir}.")
    print("Next: featurize with your existing script, e.g.\n"
          f"  python featurize_candidates.py --indir {outdir} "
          f"--labels {outdir}/results.csv --out mp_features.csv")
    print("\nReminder: these are DFT (noisy) labels -- train on them, but keep "
          "your MAGNDATA cases as a separate, trusted validation set.")


if __name__ == "__main__":
    main()
