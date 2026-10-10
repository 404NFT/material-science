#!/usr/bin/env python3
"""
Is the ERROR bucket a *moment-threshold artifact*?

55/439 (13%) of metallic AFM candidates cannot be labeled at all: amcheck
raises either
  "number of up spins should be the same as the number of down spins" (43)
  "Something is wrong with the description of magnetic atoms!"       (12)

Both depend on how a continuous DFT magmom is discretized into u/d/n, which
is set by ONE free parameter -- the moment threshold (0.05 muB in the
standard pipeline, and in our prior work). Sites below it become 'n'.

This sweeps that threshold and asks how many of the 55 become classifiable,
and whether any come out AM. If verdicts move, the threshold is a second
hidden knob alongside symmetry tolerance -- the same artifact class our
prior manuscript identified, in a different parameter.

Output: moment_threshold_sweep.csv (material x threshold -> verdict)
"""

import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "altermag"))

import pandas as pd  # noqa: E402
from pull_and_label import label_structure  # noqa: E402

TOLS = [1e-5, 1e-4, 1e-3, 1e-2]
THRESHOLDS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50]


def main():
    from mp_api.client import MPRester

    df = pd.read_csv(HERE / "mp_metallic_am" / "results.csv")
    err = df[df.verdict == "ERROR"]
    ids = err.material_id.tolist()
    print(f"sweeping moment threshold over {len(ids)} unclassifiable materials")

    with MPRester(os.environ["MP_API_KEY"]) as mpr:
        structs = {str(d.material_id): d.structure for d in
                   mpr.materials.summary.search(
                       material_ids=ids, fields=["material_id", "structure"])}
        magmoms = {}
        for i in range(0, len(ids), 50):
            for d in mpr.materials.magnetism.search(
                    material_ids=ids[i:i + 50],
                    fields=["material_id", "magmoms"]):
                magmoms[str(d.material_id)] = getattr(d, "magmoms", None)

    rows = []
    for mid in ids:
        s, m = structs.get(mid), magmoms.get(mid)
        formula = s.composition.reduced_formula if s is not None else "?"
        rec = {"material_id": mid, "formula": formula,
               "Tc_analogy_K": float(err.set_index("material_id")
                                     .loc[mid, "Tc_analogy_K"])}
        for th in THRESHOLDS:
            try:
                verdict, _, _, _ = label_structure(s, m, TOLS, th)
            except Exception as e:  # noqa: BLE001
                verdict = f"raise:{type(e).__name__}"
            rec[f"th={th}"] = verdict
        rows.append(rec)

    out = pd.DataFrame(rows)
    out.to_csv(HERE / "moment_threshold_sweep.csv", index=False)

    print("\nverdict counts by moment threshold:")
    for th in THRESHOLDS:
        vc = out[f"th={th}"].value_counts().to_dict()
        print(f"  {th:<5} " + "  ".join(f"{k}:{v}" for k, v in
                                        sorted(vc.items(), key=lambda x: -x[1])))

    rescued = out[(out[[f"th={t}" for t in THRESHOLDS]] == "AM").any(axis=1)]
    print(f"\n{len(rescued)} material(s) come out AM at SOME threshold:")
    if not rescued.empty:
        cols = ["formula", "material_id", "Tc_analogy_K"] + \
               [f"th={t}" for t in THRESHOLDS]
        print(rescued[cols].to_string(index=False))
    print(f"\nwrote {HERE / 'moment_threshold_sweep.csv'}")


if __name__ == "__main__":
    main()
