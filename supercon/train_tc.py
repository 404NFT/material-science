#!/usr/bin/env python3
"""
Train a Tc regressor on the SuperCon dataset (UCI superconductivity data,
Hamidieh 2018; 21,263 experimentally measured superconductors).

Two evaluations are reported, because they answer different questions:
  * random 10-fold CV  -- "can we interpolate within known SC families?"
    (optimistic: doping series like YBa2Cu3O7-x leak across folds)
  * grouped CV by chemical system -- "can we extrapolate to a chemical
    system never seen in training?" (the honest number for screening)

Outputs:
  tc_model.joblib   HistGradientBoostingRegressor trained on all data
  train_features.csv  cached feature matrix (skips refeaturization on rerun)
  metrics.txt
"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, KFold, cross_val_predict

from featurize_comp import feature_names, featurize_formula

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "unique_m.csv"
CACHE = HERE / "train_features.csv"


def chemical_system(formula: str) -> str:
    """Element set, sorted -- doping variants share a system."""
    from pymatgen.core import Composition
    try:
        return "-".join(sorted(el.symbol for el in Composition(formula)))
    except Exception:
        return formula


def build_features() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df = df.rename(columns={"material": "formula"})
    rows, kept = [], []
    for i, (formula, tc) in enumerate(zip(df["formula"], df["critical_temp"])):
        vec = featurize_formula(formula)
        if vec is None:
            continue
        rows.append(vec)
        kept.append((formula, tc))
        if (i + 1) % 5000 == 0:
            print(f"  featurized {i + 1}/{len(df)}", file=sys.stderr)
    X = pd.DataFrame(rows, columns=feature_names())
    X.insert(0, "formula", [f for f, _ in kept])
    X["Tc"] = [t for _, t in kept]
    return X


def main():
    if CACHE.exists():
        feats = pd.read_csv(CACHE)
        print(f"loaded cached features: {len(feats)} rows")
    else:
        feats = build_features()
        feats.to_csv(CACHE, index=False)
        print(f"featurized {len(feats)} formulas")

    fnames = feature_names()
    X = feats[fnames].to_numpy()
    y = feats["Tc"].to_numpy()
    groups = feats["formula"].map(chemical_system).to_numpy()

    model = HistGradientBoostingRegressor(
        max_iter=500, learning_rate=0.1, max_leaf_nodes=63, random_state=0)

    lines = []

    pred_r = cross_val_predict(model, X, y, cv=KFold(10, shuffle=True,
                                                     random_state=0))
    lines.append(_report("random 10-fold CV (interpolation)", y, pred_r))

    pred_g = cross_val_predict(model, X, y, cv=GroupKFold(10), groups=groups)
    lines.append(_report("grouped CV by chemical system (extrapolation)",
                         y, pred_g))

    model.fit(X, y)
    joblib.dump({"model": model, "feature_names": fnames}, HERE / "tc_model.joblib")

    report = "\n".join(lines)
    (HERE / "metrics.txt").write_text(report + "\n")
    print(report)
    print(f"\nmodel saved to {HERE / 'tc_model.joblib'}")


def _report(label, y, pred):
    rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
    mae = float(np.mean(np.abs(y - pred)))
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
    # screening-relevant: if we flag "predicted Tc > 20 K", how often right?
    flag = pred > 20
    prec = float((y[flag] > 20).mean()) if flag.any() else float("nan")
    line = (f"{label}:\n"
            f"  RMSE {rmse:6.2f} K   MAE {mae:6.2f} K   R2 {r2:.3f}\n"
            f"  precision of 'predicted Tc>20K' flag: {prec:.2f}")
    print(line)
    return line


if __name__ == "__main__":
    main()
