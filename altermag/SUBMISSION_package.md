# Submission package: significance, cover letter, figure plan

Companion to `MANUSCRIPT_draft.md`.

---

## Significance statement (≤120 words)

Altermagnets promise spintronics without stray fields, but only a few dozen are
confirmed, and computational discovery is accelerating fast. We identify a
systematic flaw shared by both symmetry-database and machine-learning screens:
they judge symmetry on DFT-relaxed structures whose tiny distortions break the
exact rotation that defines altermagnetism, silently misfiling real high-symmetry
altermagnets as ordinary antiferromagnets. A simple, interpretable pipeline that
trains only on experimental magnetic structures and verifies symmetry across
tolerances closes this gap. It reproduces altermagnets confirmed by two
independent DFT studies — including an exact structural match — and, with
two-stage first-principles confirmation of every tolerance-robust candidate,
establishes six new altermagnets (85–405 meV nodal, momentum-dependent spin
splitting at zero net moment) that a state-of-the-art neural-network screen
missed, while rejecting five false candidates through successively stricter
physical criteria. The result is both new materials and a concrete
methodological correction for the field.

---

## Cover letter (draft)

Dear Editor,

We submit "Six altermagnets hidden by symmetry tolerance: an interpretable
screening pipeline with multi-stage first-principles confirmation" for
consideration.

Altermagnetism has rapidly become a central topic in condensed-matter physics and
spintronics, and computational discovery of new altermagnets — including a recent
neural-network screen in this journal's community — is advancing quickly. Our work
makes a contribution orthogonal to, and complementary with, those efforts. Rather
than proposing another black-box predictor, we identify a concrete and general
failure mode: because altermagnetism is a symmetry property, and because the
structures fed to screening methods are DFT-relaxed and slightly distorted,
tight-tolerance symmetry analysis systematically mislabels a whole population of
altermagnets as antiferromagnets. We quantify this blind spot, show that a simple
re-symmetrization step recovers the hidden materials, and validate the resulting
pipeline against two independent DFT studies — including an exact-structure match.
We then confirm by two-stage DFT+U calculation six new altermagnets — spanning
double perovskites, a layered cobaltite, a molybdate and oxyfluorides, all showing
the nodal splitting required by altermagnetic symmetry — that a leading
graph-neural-network screen did not find, alongside a reproduced positive control
and five candidates rejected by successively stricter physical criteria.

We believe the combination of a general methodological caution with a concrete,
actionable list of new candidates will be of broad interest. We suggest reviewers
with expertise in altermagnetism/spin-group symmetry and in materials-informatics
screening.

Sincerely,
Cameron Quatman
Department of Electrical and Computer Engineering
The Ohio State University

---

## Figure plan

**Fig. 1 — Pipeline schematic.**
Flow: MAGNDATA (experimental) → amcheck labels → trained triage model → score
Materials Project → tolerance-aware amcheck verification → DFT+U confirmation.
Emphasize the two design choices that carry the paper: *trusted labels in*,
*re-symmetrization at verification*.

**Fig. 2 — Label provenance decides everything.** (the "why trusted data" panel)
Bar/paired plot of ROC-AUC & PR-AUC for: MP-trained→MP-CV, MP-trained→MAGNDATA
(≈chance), MAGNDATA-trained→MAGNDATA-CV (0.90). One glance shows the
distribution-shift collapse and the trusted-data recovery.

**Fig. 3 — The tolerance blind spot.** (the central result)
(a) Histogram of assigned space-group / crystal-system for MP vs MAGNDATA at
symprec = 10⁻³ Å — the 63% vs 0.2% triclinic mismatch.
(b) Same at 0.1 Å — distributions aligned.
(c) Worked example (Sr₂FeWO₆): space group vs symprec, annotated AFM→AM flip;
inset of the ideal double-perovskite cell.

**Fig. 4 — Validation & novelty.** (the payoff)
Venn / matrix of our confirmed set vs Gao et al.'s 50 and the MAGNDATA gold
standard: overlaps highlighted (Ba₂CoSi₂O₇ exact match, LiFeF₄, CaLaCrMoO₆);
the 12 novel candidates listed; adjacency callout (Ca₃Cr₂O₇ vs Ca₃Co₂O₇).

**Fig. 5 — DFT confirmation.** (data in hand: qe_results.csv + saved XML)
Spin-resolved band structures showing k-dependent splitting at zero net moment.
Hero panels: VOF₂ and Y₂Mo₂O₇ (nodal structure, splitting collapsing to ~0 along
specific directions) + bar chart of max/min per-k splitting for the seven confirmed (6 novel + control).

**Table 1 — The candidate list.**
All robust candidates: formula, MP id, space group (ideal), P(AM), amcheck
verdict across tolerances, metal/insulator classification (from refined bands;
indicative gaps only — PBE+U), wave type (d/g/i, once assigned), overlap status
with prior work.

---

## Reviewer-anticipation notes (internal)

- **"Symmetry ≠ confirmation."** Closed: all 12 robust candidates two-stage
  DFT-verdicted (7 confirmed incl. reproduced control; 5 rejected across graded
  filters — sub-threshold, unstable-moment, loose-numerics artifact, dense-k
  magnetization drift, node-less compensated ferrimagnet). The attrition chain is
  itself evidence of rigor. Remaining exposure: modest refined k-meshes — the
  ≤25% first-pass→refined drift argues stability; offer denser-k values in revision.
- **"Is 0.1 Å over-symmetrizing?"** Addressed by the robust criterion (AM at BOTH
  0.05 and 0.1) and by showing fragile 0.1-only cases (FeO, LaCoO₃) are correctly
  quarantined as artifacts.
- **"Why not just use the GNN?"** Point: the GNN inherits the same distortion bias;
  interpretability + explicit re-symmetrization is the fix, not more model capacity.
