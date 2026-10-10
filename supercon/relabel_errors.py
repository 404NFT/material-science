#!/usr/bin/env python3
"""
Re-label the ERROR rows from screen_metallic_am.py.

Bug found 2026-07-27: the screen fetched magmoms in batches of 500 ids, but
the magnetism endpoint does not always return a doc for every requested id in
a batch. Those materials got magmoms=None -> label_structure raised
ValueError -> bucketed ERROR, without ever being symmetry-tested. The census
("12 AM of 439") was therefore an undercount.

This script re-fetches magmoms for the ERROR rows in small batches, retries
per-id on a miss, re-runs the same amcheck tolerance sweep, and rewrites
results.csv in place (keeping a .bak). Rows that still fail are reported with
their true exception so a genuine-error count can be quoted honestly.
"""

import shutil
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "altermag"))

from pull_and_label import label_structure  # noqa: E402

TOLS = [1e-5, 1e-4, 1e-3, 1e-2]


def main():
    import os
    from mp_api.client import MPRester
    from pymatgen.io.cif import CifWriter

    outdir = HERE / "mp_metallic_am"
    csv = outdir / "results.csv"
    df = pd.read_csv(csv)
    err = df[df.verdict == "ERROR"]
    print(f"{len(err)} ERROR rows to re-check")
    if err.empty:
        return

    ids = err.material_id.tolist()
    key = os.environ["MP_API_KEY"]
    with MPRester(key) as mpr:
        structs = {str(d.material_id): d.structure for d in
                   mpr.materials.summary.search(material_ids=ids,
                                                fields=["material_id",
                                                        "structure"])}
        magmoms = {}
        for i in range(0, len(ids), 50):
            batch = ids[i:i + 50]
            for d in mpr.materials.magnetism.search(
                    material_ids=batch, fields=["material_id", "magmoms"]):
                magmoms[str(d.material_id)] = getattr(d, "magmoms", None)
        # per-id retry for anything still missing
        missing = [m for m in ids if magmoms.get(m) is None]
        print(f"  {len(missing)} still missing after batched fetch; "
              f"retrying individually")
        for m in missing:
            for d in mpr.materials.magnetism.search(
                    material_ids=[m], fields=["material_id", "magmoms"]):
                magmoms[str(d.material_id)] = getattr(d, "magmoms", None)

    counts, still_err = {}, []
    for idx, row in err.iterrows():
        mid = row.material_id
        s, m = structs.get(mid), magmoms.get(mid)
        if s is None:
            still_err.append((mid, row.formula, "no structure"))
            continue
        try:
            verdict, sg, net, per_tol = label_structure(s, m, TOLS, 0.05)
        except Exception as e:  # noqa: BLE001
            still_err.append((mid, row.formula, f"{type(e).__name__}: {e}"))
            continue
        df.loc[idx, "verdict"] = verdict
        df.loc[idx, "spacegroup"] = sg
        df.loc[idx, "net_moment"] = round(float(net), 3)
        for t in TOLS:
            df.loc[idx, f"AM@{t:g}"] = per_tol[t]
        counts[verdict] = counts.get(verdict, 0) + 1
        if verdict in ("AM", "REVIEW-FLIP"):
            CifWriter(s).write_file(outdir / f"{mid}.cif")
            print(f"  RECOVERED {mid:14s} {row.formula:16s} -> {verdict} "
                  f"(Tc-analogy {row.Tc_analogy_K})")

    shutil.copy(csv, csv.with_suffix(".csv.bak"))
    df.to_csv(csv, index=False)

    print("\nre-label outcome:")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:14s} {v}")
    print(f"  genuine errors {len(still_err)}")
    for mid, f, why in still_err[:10]:
        print(f"    {mid:14s} {f:16s} {why[:60]}")
    print("\nNEW CENSUS:")
    print(df.verdict.value_counts().to_string())


if __name__ == "__main__":
    main()
