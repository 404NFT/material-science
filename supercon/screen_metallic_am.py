#!/usr/bin/env python3
"""
Full-MP screen for METALLIC altermagnet candidates -- the raw material for
altermagnetic superconductivity.

Rationale: pairing theories on altermagnets (2023-) all reuse the same 2-3
model metals because almost no metallic altermagnets are known; most AM
candidates (ours included) are insulators. Nobody has published a systematic
metallic-altermagnet candidate list. This screen produces one:

  1. Pull ALL Materials Project antiferromagnets that are metallic
     (is_metal) and near-stable (E_hull <= --ehull, default 0.10 eV/atom).
  2. Label each AM vs AFM with the same amcheck tolerance sweep as the
     altermag pipeline (imported from ../altermag/pull_and_label.py).
  3. Score each composition with the SuperCon-trained Tc model as a
     "superconductor-likeness" tiebreaker (NOT a Tc claim for magnets --
     it flags compositions resembling known SC families).

Outputs (in --outdir, default mp_metallic_am/):
  results.csv      every screened material: verdicts, E_hull, Tc-analogy
  <mpid>.cif       structures for AM and REVIEW-FLIP hits only
Usage:
  MP_API_KEY=... ./venv/bin/python screen_metallic_am.py
"""

import argparse
import csv
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALTERMAG = HERE.parent / "altermag"
sys.path.insert(0, str(ALTERMAG))

import joblib
import numpy as np
from pymatgen.analysis.magnetism import Ordering
from pymatgen.io.cif import CifWriter

from featurize_comp import featurize_formula
from pull_and_label import label_structure  # amcheck tolerance sweep
from train_tc import chemical_system

TOLS = [1e-5, 1e-4, 1e-3, 1e-2]


def fetch_metallic_afm(mpr, ehull_max, limit=None):
    """(material_id, structure, magmoms, e_hull) for metallic AFM materials."""
    print("Querying MP summary: AFM + metallic + near-stable ...", flush=True)
    docs = mpr.materials.summary.search(
        magnetic_ordering=Ordering.AFM,
        is_metal=True,
        energy_above_hull=(0, ehull_max),
        fields=["material_id", "structure", "energy_above_hull"],
    )
    by_id = {str(d.material_id): d for d in docs}
    mpids = sorted(by_id)
    if limit:
        mpids = mpids[:limit]
    print(f"  {len(mpids)} metallic AFM materials", flush=True)

    magmoms = {}
    for i in range(0, len(mpids), 500):
        batch = mpids[i:i + 500]
        for d in mpr.materials.magnetism.search(
                material_ids=batch, fields=["material_id", "magmoms"]):
            magmoms[str(d.material_id)] = getattr(d, "magmoms", None)
        print(f"  magmoms {min(i + 500, len(mpids))}/{len(mpids)}", flush=True)

    return [(m, by_id[m].structure, magmoms.get(m),
             float(by_id[m].energy_above_hull)) for m in mpids]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key", default=os.environ.get("MP_API_KEY"))
    ap.add_argument("--outdir", default=str(HERE / "mp_metallic_am"))
    ap.add_argument("--ehull", type=float, default=0.10)
    ap.add_argument("--limit", type=int, default=0, help="debug: cap materials")
    args = ap.parse_args()
    if not args.api_key:
        sys.exit("No API key. Pass --api-key or set MP_API_KEY.")

    from mp_api.client import MPRester

    bundle = joblib.load(HERE / "tc_model.joblib")
    model = bundle["model"]

    import pandas as pd
    known_systems = set(
        pd.read_csv(HERE / "train_features.csv", usecols=["formula"])
        ["formula"].map(chemical_system))

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    with MPRester(args.api_key) as mpr:
        docs = fetch_metallic_afm(mpr, args.ehull, args.limit or None)

    fields = (["material_id", "formula", "spacegroup", "n_sites", "e_hull",
               "net_moment"] + [f"AM@{t:g}" for t in TOLS]
              + ["verdict", "Tc_analogy_K", "known_SC_system"])
    counts = {}

    with open(outdir / "results.csv", "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for n, (mpid, structure, magmoms, ehull) in enumerate(docs, 1):
            formula = structure.composition.reduced_formula
            try:
                verdict, sg, net, per_tol = label_structure(
                    structure, magmoms, TOLS, 0.05)
            except Exception as e:  # noqa: BLE001
                verdict, sg, net = f"ERROR", "", float("nan")
                per_tol = {t: f"err:{type(e).__name__}" for t in TOLS}

            vec = featurize_formula(formula)
            tc = float(model.predict(vec.reshape(1, -1))[0]) if vec is not None \
                else float("nan")

            row = {"material_id": mpid, "formula": formula, "spacegroup": sg,
                   "n_sites": len(structure), "e_hull": f"{ehull:.4f}",
                   "net_moment": f"{net:.3f}", "verdict": verdict,
                   "Tc_analogy_K": f"{tc:.2f}",
                   "known_SC_system": chemical_system(formula) in known_systems}
            for t in TOLS:
                row[f"AM@{t:g}"] = per_tol[t]
            writer.writerow(row)
            fh.flush()
            counts[verdict] = counts.get(verdict, 0) + 1

            if verdict in ("AM", "REVIEW-FLIP"):
                CifWriter(structure).write_file(outdir / f"{mpid}.cif")
                print(f"[{n}/{len(docs)}] {mpid:16s} {formula:16s} "
                      f"{verdict:12s} Tc-analogy {tc:6.1f} K", flush=True)
            elif n % 200 == 0:
                print(f"[{n}/{len(docs)}] ...", flush=True)

    print("\nSummary:")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:14s} {v}")
    print(f"\nWrote {outdir}/results.csv")


if __name__ == "__main__":
    main()
