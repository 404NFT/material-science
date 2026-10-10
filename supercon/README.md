# supercon — superconductor candidate screening

Sibling pipeline to `../altermag`, same two-stage philosophy:
trusted experimental training data → ML triage → (eventually) DFT verification.

## Pipeline

1. **Data**: `data/unique_m.csv` — UCI superconductivity dataset
   (Hamidieh 2018; 21,263 experimentally measured superconductors with Tc,
   derived from the NIMS SuperCon database).
2. **`featurize_comp.py`** — composition-only descriptor: 68 magpie-style
   features (fraction-weighted stats of elemental properties) from a formula.
   Composition-only on purpose, so any candidate with a formula can be scored.
3. **`train_tc.py`** — HistGradientBoosting Tc regressor.
   Reports random 10-fold CV (interpolation) AND grouped CV by chemical
   system (honest extrapolation number). Outputs `tc_model.joblib`,
   `metrics.txt`, cached `train_features.csv`.
4. **`screen_local.py`** — scores `../altermag/mp_data` structures, joins
   altermagnet verdicts + P_AM, flags whether each chemical system exists in
   SuperCon. Output: `screened_local.csv` ranked by predicted Tc.

## Current results (2026-07-19)

- Random CV: RMSE 9.5 K, R² 0.923 (matches Hamidieh's published 0.92).
- Grouped-by-system CV: RMSE 13.0 K, R² 0.857; "predicted Tc>20K" flag is
  91% precise even on never-seen chemical systems.
- Screen of the altermag MP set: top of list dominated by cuprate-like
  oxides (expected — model learned the Cu-O signal). Notable
  altermagnet ∩ high-Tc rows: MnVAgO4 (P_AM 0.59, ~77 K pred),
  LaFe4(CuO4)3 (P_AM 0.87, ~73 K pred).

## Known caveats

- Composition-only: the model cannot distinguish polymorphs and does not
  know whether a compound is metallic. Predictions on magnetic *insulators*
  mean "this composition resembles superconducting families", often
  "…when doped" (cuprate parents are AFM insulators).
- Training set contains only superconductors — the model answers
  "if this superconducts, what Tc?", not "does it superconduct?".
  A non-SC/SC classifier (needs negative examples, e.g. 3DSC or
  Stanev's approach) is the natural next addition.

## Next steps

- [ ] Pull full MP screen (needs `MP_API_KEY`): stable, ambient-pressure,
      metallic compounds → predict Tc → rank novel systems.
- [ ] Add non-superconductor negatives + classifier stage.
- [ ] DFT verification for conventional candidates: QE `ph.x` DFPT →
      electron-phonon λ, ω_log → Allen-Dynes Tc (native QE build exists
      in ../altermag/qe-native). Only valid for non-magnetic metals.
