#!/usr/bin/env python3
"""
Screen the local altermag MP structure set for predicted superconductors.

Reads the 2,472 antiferromagnet/altermagnet structures already pulled from
the Materials Project (../altermag/mp_data), predicts Tc for each with the
SuperCon-trained model, and joins the altermagnet verdicts -- so the output
directly answers "which of our altermagnet candidates might also
superconduct?" (magnetism competes with conventional s-wave pairing, so a
high-Tc prediction on an AM candidate is an unconventional-pairing flag,
not a BCS one -- interpret accordingly).

Novelty flag: chemical systems that appear in the SuperCon training set are
marked known_system=True; predictions there are interpolation. The
interesting rows are high predicted Tc + unseen system.

Usage: ./venv/bin/python screen_local.py
Output: screened_local.csv (ranked by predicted Tc)
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pymatgen.core import Composition

from featurize_comp import featurize_formula
from train_tc import chemical_system

HERE = Path(__file__).resolve().parent
ALTERMAG = HERE.parent / "altermag"


def main():
    bundle = joblib.load(HERE / "tc_model.joblib")
    model, fnames = bundle["model"], bundle["feature_names"]

    train = pd.read_csv(HERE / "train_features.csv", usecols=["formula"])
    known_systems = set(train["formula"].map(chemical_system))

    results = pd.read_csv(ALTERMAG / "mp_data" / "results.csv")
    results["material_id"] = results["file"].str.replace(".cif", "", regex=False)

    scored = pd.read_csv(ALTERMAG / "mp_candidates_scored.csv") \
        if (ALTERMAG / "mp_candidates_scored.csv").exists() else None

    rows = []
    for _, r in results.iterrows():
        vec = featurize_formula(r["formula"])
        if vec is None:
            continue
        rows.append({
            "material_id": r["material_id"],
            "formula": r["formula"],
            "am_verdict": r["verdict"],
            "n_sites": r["n_sites"],
            "system": chemical_system(r["formula"]),
            "_vec": vec,
        })

    df = pd.DataFrame(rows)
    X = np.vstack(df.pop("_vec").to_numpy())
    df["Tc_pred_K"] = model.predict(X)
    df["known_system"] = df["system"].isin(known_systems)

    if scored is not None and "P_AM" in scored.columns:
        scored["material_id"] = scored["file"].str.replace(".cif", "",
                                                           regex=False)
        df = df.merge(scored[["material_id", "P_AM"]], on="material_id",
                      how="left")

    df = df.sort_values("Tc_pred_K", ascending=False)
    out = HERE / "screened_local.csv"
    df.to_csv(out, index=False)

    print(f"screened {len(df)} structures -> {out}\n")
    print("Top 20 by predicted Tc:")
    cols = [c for c in ("formula", "material_id", "Tc_pred_K", "am_verdict",
                        "known_system", "P_AM") if c in df.columns]
    print(df[cols].head(20).to_string(index=False,
                                      float_format=lambda v: f"{v:.2f}"))

    novel = df[~df["known_system"]]
    print(f"\nTop 10 in chemical systems ABSENT from SuperCon (the novel ones):")
    print(novel[cols].head(10).to_string(index=False,
                                         float_format=lambda v: f"{v:.2f}"))


if __name__ == "__main__":
    main()
