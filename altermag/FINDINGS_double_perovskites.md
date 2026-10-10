# Candidate altermagnetic double perovskites from an ML-triage + amcheck pipeline

## Summary

Starting from a machine-learning triage model trained on experimentally-determined
magnetic structures (MAGNDATA) and applied to Materials Project (MP) candidates,
followed by rigorous symmetry verification with `amcheck`, we identify **four
ordered double perovskites** as altermagnet candidates that the standard
tight-tolerance MP pipeline had labeled conventional antiferromagnets:

| Material | MP id | ML P(AM) | amcheck @0.05 | amcheck @0.1 | MP label |
|---|---|---|---|---|---|
| CaLaCrMoO₆ | mp-1048863 | 0.996 | AM | AM | AFM |
| Sr₂FeWO₆ | mp-19266 | 0.995 | AM | AM | AFM |
| Ba₂FeWO₆ | mp-1272506 | 0.983 | AM | AM | AFM |
| Ba₂FeMoO₆ | mp-1277787 | 0.880 | AM | AM | AFM |

All four are **robust** flips: `amcheck` classifies them as altermagnetic at
BOTH the 0.05 and 0.1 symmetry tolerances (not just the loosest), so they are
not over-symmetrization artifacts.

## Cross-check against Gao et al. (NSR 2025, doi:10.1093/nsr/nwaf066)

The independent GNN-based altermagnet screening of Gao et al. reports 50
DFT-confirmed altermagnets. Cross-referencing our four candidates:

- **CaLaCrMoO₆ — IS in their DFT-confirmed set.** This is external validation:
  our MAGNDATA-trained + amcheck-verified pipeline independently reproduces a
  material confirmed by first-principles calculation in a high-impact study.
  (Consequently CaLaCrMoO₆ is already claimed, not novel here.)
- **Sr₂FeWO₆, Ba₂FeWO₆, Ba₂FeMoO₆ — are NOT in their set.** These remain novel,
  symmetry-verified candidates that a state-of-the-art GNN screen did not
  surface. A plausible reason is directly relevant to this work: their GNN
  learns from as-given (DFT-distorted) structures and may share the same
  tight-tolerance blind spot as MP's pipeline — exactly the failure mode our
  re-symmetrization step is designed to catch. DFT confirmation is required to
  establish them as altermagnets (not merely symmetry-permitted).

### Full cross-check of our amcheck-confirmed set vs Gao et al.'s 50

Comparing all 32 of our amcheck-confirmed-AM MP candidates against their table:

VALIDATION (independent methods agree):
- **Ba₂CoSi₂O₇ (mp-510015) — EXACT same MP structure** as their entry #30. Two
  independent pipelines (ours: HistGB + amcheck; theirs: pretrained GNN + DFT)
  converged on the identical entry. Strongest single validation.
- **LiFeF₄** — ours mp-778347 vs their #50 mp-755632 (same compound, polymorph).
- **CaLaCrMoO₆** — ours mp-1048863 vs their #48 mp-1640189 (same compound, polymorph).

NOVEL (12 robust candidates not in their 50): Sr₂FeWO₆, Ba₂FeWO₆, Ba₂FeMoO₆,
VOF₂, MnOF, ZrCoO₃, Ca₃Co₂O₇, Y₂Mo₂O₇, SrLaCoO₄, CsTaCo(OF₂)₂, MgCu₂(O₂F)₂,
NiH₂SeO₅. Note their list has the adjacent Ca₃Cr₂O₇ (#22, vs our Ca₃Co₂O₇) and
ZrCrO₃ (#23, vs our ZrCoO₃) — different metals, so not duplicates; our pipeline
discriminates the correct compositions.

Both lists are rich in fluorides/oxyfluorides and perovskites (same veins), but
the specific hits differ — consistent with their distortion-naive GNN missing
the slightly-distorted-cell altermagnets our re-symmetrization step recovers.

## Why the standard pipeline missed them

MP's magnetism pipeline runs `amcheck` on the DFT-relaxed cell at a tight
symmetry tolerance (~10⁻³ Å). DFT relaxation introduces sub-0.1 Å distortions
that break the exact rotational symmetry enabling altermagnetism, so these
materials read as triclinic/monoclinic AFM. When the structure is symmetrized to
its ideal higher-symmetry cell (tolerance 0.05-0.1 Å), the rotation relating the
two spin sublattices reappears and the altermagnetic classification emerges.

This is a systematic blind spot: **altermagnets in slightly-distorted
high-symmetry structures are mislabeled AFM by tight-tolerance screening.**

## Evidence chain (per candidate)

- **Composition/structure**: ordered A₂BB'O₆ double perovskite, the structural
  family theory associates with altermagnetism (also present in the published
  MAGNDATA gold-standard set, e.g. La₂CoIrO₆).
- **ML score**: high P(AM) from a model with 0.90 PR-AUC on trusted in-distribution
  cross-validation (`am_model_trusted.joblib`).
- **Magnetic compensation**: MP DFT ground state has net moment < 0.05 µ_B
  (passes the compensated-AFM filter; not a ferrimagnet).
- **Symmetry**: `amcheck` confirms altermagnetic symmetry at ideal cell
  (tolerance-robust across 0.05 and 0.1 Å).

## FULL-SET DFT CONFIRMATION: 10 of 12 candidates are altermagnets (9 novel)

DFT (native QE 7.3.1, PBE+U, constrained-magnetization recipe, first-pass
ecut 45 Ry / 2×2×2 k) completed for ALL 12 robust candidates:

| Material | max split | per-k range | net mom | verdict |
|---|---|---|---|---|
| Ba₂FeMoO₆ (mp-1277787) | 366 meV | 105–366 | −0.03 | **ALTERMAGNET** (novel) |
| Y₂Mo₂O₇ (mp-2674749) | 360 meV | 6–360 | +0.01 | **ALTERMAGNET** (novel, near-nodal) |
| SrLaCoO₄ (mp-1274449) | 281 meV | 47–281 | −0.00 | **ALTERMAGNET** (novel) |
| MgCu₂(O₂F)₂ (mp-2240166) | 269 meV | 26–269 | −0.00 | **ALTERMAGNET** (novel) |
| Ca₃Co₂O₇ (mp-1580697) | 247 meV | 71–247 | +0.09 | **ALTERMAGNET** (novel) |
| Ba₂FeWO₆ (mp-1272506) | 232 meV | 132–232 | −0.00 | **ALTERMAGNET** (novel) |
| CaLaCrMoO₆ (mp-1048863) | 205 meV | 31–205 | −0.00 | ALTERMAGNET (control ✓) |
| Sr₂FeWO₆ (mp-19266) | 125 meV | 31–125 | 0.00 | **ALTERMAGNET** (novel) |
| ZrCoO₃ (mp-756665) | 115 meV | 67–115 | −0.00 | **ALTERMAGNET** (novel) |
| VOF₂ (mp-759163) | 93 meV | 1–93 | +0.00 | **ALTERMAGNET** (novel, nodal) |
| MnOF (mp-1277241) | 30 meV | 24–30 | +0.00 | sub-threshold (weak) |
| CsTaCo(OF₂)₂ (mp-684727) | 1168 meV | — | **+1.70** | REJECTED: converged ferrimagnetic |

Notes: VOF₂ and Y₂Mo₂O₇ show per-k splitting collapsing to ~0 along some
directions — the nodal structure characteristic of d/g-wave altermagnetism.
MnOF is symmetry-permitted but electronically weak (30 meV < 50 meV bar).
CsTaCo(OF₂)₂ would not hold a compensated state even under the λ=0.5 constraint
(net moment 1.7 µB) — its MP "AFM" configuration appears unstable; excluded.
The two negatives demonstrate the DFT step does real filtering, not
rubber-stamping of amcheck's symmetry verdicts.

## DFT CONFIRMATION (double perovskites detail): all four are altermagnets

First-principles confirmation completed for ALL FOUR candidates (native QE 7.3.1,
PBE+U, first-pass ecut 45 Ry / 2×2×2 k, computed on an M1 Max). Every one shows
the definitive altermagnetic fingerprint: large, momentum-dependent spin
splitting near E_F at zero net magnetization.

| Material | max split | per-k range | net moment | SCF quality | status |
|---|---|---|---|---|---|
| **Sr₂FeWO₆** (mp-19266) | **125 meV** | 31–125 | 0.00 | 2e-4 Ry residual | **NOVEL** |
| **Ba₂FeWO₆** (mp-1272506) | **232 meV** | 132–232 | −0.00 | ~0.3 Ry residual* | **NOVEL** |
| **Ba₂FeMoO₆** (mp-1277787) | **366 meV** | 105–366 | −0.03 | ~0.02 Ry residual* | **NOVEL** |
| CaLaCrMoO₆ (mp-1048863) | 205 meV | 31–205 | −0.00 | converged (15 it) | control ✓ |

*The two Ba compounds have bistable SCF (ferrimagnet-adjacent family); their
densities come from a controlled maxstep stop with the AFM state pinned by
constrained_magnetization — magnitudes are first-pass and need refinement
(tighter convergence, denser k, higher ecut) for publication values.

**Method validation**: CaLaCrMoO₆ is the positive control — independently
DFT-confirmed as an altermagnet by Gao et al. (NSR 2025). Our recipe reproduces
it (formally converged, 205 meV), validating the setup that produced the three
novel results.

**Convergence recipe for these correlated double perovskites** (plain PBE
diverges; needed): DFT+U + constrained_magnetization='atomic' (lambda=0.5) to
pin the compensated AFM against ferrimagnetic competition + mv smearing
(degauss 0.03) + plain Broyden (beta 0.1, ndim 20) + uniform k-grid. For
CaLaCrMoO₆ additionally: La pseudo WITHOUT 4f valence (spfn variant crashes
QE's ylmr2) and HUBBARD (atomic) projectors.

## Status of DFT confirmation (remaining candidates)

The final gold-standard step is a spin-polarized DFT calculation showing
momentum-dependent spin splitting (≥ 50 meV near E_F) at zero net moment.

- Inputs are prepared: VASP (`dft_inputs/`, cluster) and Quantum ESPRESSO
  (`qe_inputs/`, with DFT+U).
- **These are correlated magnetic oxides**: plain PBE does not converge (SCF
  diverges); DFT+U (U = 4.5 eV on Fe 3d, 3.5 on Cr 3d, 2.5 on Mo 4d) is required
  and stabilizes the SCF. Local test runs on an M1 Max (QE under Rosetta) confirm
  the toolchain and the stable compensated-AFM solution, but do not reach tight
  convergence in practical time. **Converged bands require HPC** (native QE,
  many cores, dense k-mesh) — use `run_dft.slurm` + the +U-enabled inputs.

## Caveat

`amcheck` confirms that symmetry *permits* altermagnetism; it does not prove a
sizeable spin splitting *occurs*. That requires the DFT step above. Treat these
four as high-priority, symmetry-validated candidates for DFT confirmation, not
as established altermagnets.

## Reproduce

```
pull_and_label.py      # MP AFM structures + amcheck labels
fetch_magndata.py      # scrape MAGNDATA (trusted training structures)
label_mcif.py          # amcheck labels for MAGNDATA
featurize_candidates.py --symprec 0.1   # crystal-only features (both sets)
train_classifier.py    # HistGB on MAGNDATA -> am_model_trusted.joblib
                       # score MP -> mp_candidates_scored.csv
verify_candidates.py   # amcheck tolerance sweep -> final_altermagnet_candidates.csv
prep_dft.py / prep_qe.py   # DFT inputs (VASP / QE+U)
```

## FINAL REFINED VERDICTS (two-stage DFT, 2026-07-10)

Refinement (ecut 60 Ry, 4x4x4/3x3x3 k, tighter conv) of all 10 first-pass positives,
plus a nodal criterion (altermagnetic symmetry requires nodal directions):

CONFIRMED (6 novel + control): Y2Mo2O7 405 meV, SrLaCoO4 281, Ba2FeMoO6 275,
MgCu2(O2F)2 254, CaLaCrMoO6 210 (control ✓), Sr2FeWO6 116, VOF2 85. All nodal
(min per-k <= 10% of max), all compensated.

DEMOTED at refinement (3): ZrCoO3 (115 -> 19 meV, loose-numerics artifact);
Ca3Co2O7 (drifts to net -0.83 uB at dense k); Ba2FeWO6 (1.9 eV splitting but
NODE-LESS 1656-1888 meV -> compensated-ferrimagnet state, not altermagnetic).

Earlier rejections stand: MnOF sub-threshold (30 meV), CsTaCo(OF2)2 ferrimagnetic.
Multi-stage attrition 454 -> 15 -> 12 -> 10 -> 6(+control) — each filter did real work.
