#!/usr/bin/env python3
"""
Train the altermagnet ML-triage classifier.

Reads a crystal-only feature matrix (from featurize_candidates.py) and trains a
gradient-boosted-tree classifier to predict altermagnet-likelihood (label=1 AM,
label=0 AFM) from structure alone.

THE TWO THINGS THAT MATTER HERE:
  1. SEVERE CLASS IMBALANCE. Positives (AM) are ~3% of the data. Accuracy is a
     useless metric -- "always predict AFM" scores ~97%. We report PR-AUC
     (average precision), ROC-AUC, and precision/recall, and weight classes
     balanced so the model actually pays attention to the rare positives.
  2. NOISY LABELS. The MP labels are DFT-derived. The handful of MAGNDATA cases
     in mcif_features.csv are trusted ground truth -- we never train on them,
     only use them as a final sanity check.

Usage:
    python train_classifier.py \
        --features mp_features.csv \
        --validation mcif_features.csv \
        --model-out am_model.joblib
"""

import argparse
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (average_precision_score, classification_report,
                             precision_recall_curve, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.utils.class_weight import compute_sample_weight

# Columns that are not features.
_NON_FEATURES = ("file", "label")


def load_xy(path):
    """Return (X DataFrame, y array, feature_names) from a feature CSV."""
    df = pd.read_csv(path)
    if "label" not in df.columns:
        sys.exit(f"{path}: no 'label' column.")
    feat_cols = [c for c in df.columns if c not in _NON_FEATURES]
    X = df[feat_cols].apply(pd.to_numeric, errors="coerce")
    y = df["label"].astype(int).to_numpy()
    return X, y, feat_cols, df


def make_model():
    """HistGradientBoosting handles NaNs natively and is strong on tabular data.
    class_weight='balanced' makes the rare AM class count proportionally more."""
    return HistGradientBoostingClassifier(
        max_iter=400,
        learning_rate=0.05,
        max_leaf_nodes=31,
        l2_regularization=1.0,
        early_stopping=True,
        validation_fraction=0.15,
        class_weight="balanced",
        random_state=0,
    )


def report_at_best_f1(y_true, scores):
    """Pick the threshold maximizing F1 on the PR curve and report there."""
    prec, rec, thr = precision_recall_curve(y_true, scores)
    # prec/rec have one more element than thr; align and avoid div-by-zero.
    denom = prec + rec
    f1 = np.divide(2 * prec * rec, denom, out=np.zeros_like(denom),
                   where=denom > 0)
    best = int(np.argmax(f1[:-1])) if len(thr) else 0
    t = float(thr[best]) if len(thr) else 0.5
    pred = (scores >= t).astype(int)
    print(f"\nBest-F1 operating point (threshold = {t:.3f}):")
    print(classification_report(y_true, pred, target_names=["AFM", "AM"],
                                digits=3, zero_division=0))
    return t


def main():
    ap = argparse.ArgumentParser(description="Train altermagnet triage classifier")
    ap.add_argument("--features", default="mp_features.csv",
                    help="training feature matrix")
    ap.add_argument("--validation", default="mcif_features.csv",
                    help="trusted held-out feature matrix (MAGNDATA)")
    ap.add_argument("--folds", type=int, default=5, help="stratified CV folds")
    ap.add_argument("--model-out", default="am_model.joblib",
                    help="where to save the final model")
    args = ap.parse_args()

    X, y, feat_cols, _ = load_xy(args.features)
    n_pos, n_neg = int(y.sum()), int((y == 0).sum())
    print(f"Training data: {len(y)} rows, {len(feat_cols)} features")
    print(f"  AM (1): {n_pos}   AFM (0): {n_neg}   "
          f"positive rate: {n_pos / len(y):.1%}")

    # --- Cross-validated, leakage-free out-of-fold scores. ---
    cv = StratifiedKFold(n_splits=args.folds, shuffle=True, random_state=0)
    oof = cross_val_predict(make_model(), X, y, cv=cv,
                            method="predict_proba")[:, 1]

    print(f"\n{args.folds}-fold stratified CV (out-of-fold):")
    print(f"  PR-AUC  (avg precision): {average_precision_score(y, oof):.3f}"
          f"   [baseline = {n_pos / len(y):.3f}]")
    print(f"  ROC-AUC                : {roc_auc_score(y, oof):.3f}")
    report_at_best_f1(y, oof)

    # --- Fit final model on ALL training data. ---
    model = make_model()
    sw = compute_sample_weight("balanced", y)
    model.fit(X, y, sample_weight=sw)

    # --- Permutation importance (which crystal features carry signal). ---
    pi = permutation_importance(model, X, y, n_repeats=10, random_state=0,
                                scoring="average_precision")
    order = np.argsort(pi.importances_mean)[::-1]
    print("\nTop 10 features by permutation importance (PR-AUC drop):")
    for i in order[:10]:
        print(f"  {feat_cols[i]:24s} {pi.importances_mean[i]:+.4f} "
              f"± {pi.importances_std[i]:.4f}")

    # --- Trusted validation check (never trained on). ---
    try:
        Xv, yv, _, dfv = load_xy(args.validation)
        Xv = Xv.reindex(columns=feat_cols)   # align schema
        pv = model.predict_proba(Xv)[:, 1]
        print(f"\nTrusted validation ({args.validation}):")
        for fname, true, score in zip(dfv["file"], yv, pv):
            tag = "AM" if true == 1 else "AFM"
            print(f"  {fname:28s} true={tag:3s}  P(AM)={score:.3f}")
    except FileNotFoundError:
        print(f"\n[skip] validation file {args.validation} not found.")

    # --- Save. ---
    try:
        import joblib
        joblib.dump({"model": model, "features": feat_cols}, args.model_out)
        print(f"\nSaved model -> {args.model_out}")
    except Exception as e:  # noqa: BLE001
        print(f"\n[warn] could not save model: {e}")

    print("\nReminder: PR-AUC is the number to watch, not accuracy. With ~3% "
          "positives,\na model can be 97% 'accurate' and still useless.")


if __name__ == "__main__":
    main()
