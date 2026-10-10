# Six altermagnets hidden by symmetry tolerance: an interpretable screening pipeline with multi-stage first-principles confirmation

**Cameron Quatman**
*Department of Electrical and Computer Engineering, The Ohio State University, Columbus, Ohio, USA*
Contact: xxx

*Working manuscript draft — v0.3 (refined DFT results; final verdicts)*

---

## Abstract

Altermagnets combine compensated antiparallel spin sublattices with momentum-dependent
spin splitting, but the small pool of confirmed materials limits their study. Machine-
learning screens have begun to expand this pool, yet they inherit a subtle flaw: they
learn from, and evaluate symmetry on, DFT-relaxed structures whose sub-0.1 Å distortions
break the exact rotational symmetry that defines altermagnetism. We show this produces a
systematic blind spot — altermagnets in slightly-distorted high-symmetry cells are
misfiled as conventional antiferromagnets by tight-tolerance screening. We introduce a
deliberately simple, interpretable pipeline: a gradient-boosted classifier trained only
on experimentally-determined magnetic structures (MAGNDATA) with crystal-only,
leakage-free descriptors triages Materials Project candidates; `amcheck` symmetry
verification across a tolerance range then recovers the hidden materials. The pipeline
independently reproduces DFT-confirmed altermagnets from two prior studies, including an
exact-structure match (Ba₂CoSi₂O₇). Two-stage spin-polarized DFT+U calculations (first-pass, then refined cutoff,
k-mesh and convergence) on all twelve tolerance-robust candidates confirm **six new
altermagnets** — Sr₂FeWO₆ and Ba₂FeMoO₆ (double perovskites), SrLaCoO₄ (layered
cobaltite), Y₂Mo₂O₇ (pyrochlore-derived molybdate), and VOF₂ and MgCu₂(O₂F)₂
(oxyfluorides) — with momentum-dependent spin splitting of 85–405 meV at zero net
magnetization and, in every case, the nodal splitting structure required by
altermagnetic symmetry. Five candidates are rejected across the successive filters:
one electronically weak, one magnetically unstable, one a loose-numerics artifact, one
drifting to a magnetized state, and one exhibiting large but node-less splitting
diagnostic of a compensated ferrimagnet. This multi-stage attrition demonstrates that
symmetry analysis, first-pass DFT, and refined DFT each perform genuine, distinct
filtering. Because a state-of-the-art graph-neural-network screen missed all six
confirmed materials, we argue tolerance-aware re-symmetrization is a necessary
ingredient of altermagnet discovery.

---

## 1. Introduction

Altermagnetism is a recently established collinear magnetic phase, distinct from ferro-
and antiferromagnetism, in which opposite-spin sublattices are related not by translation
or inversion but by a proper/improper rotation of the crystal [Šmejkal et al.]. This
symmetry produces anisotropic, momentum-dependent spin splitting at zero net
magnetization, with consequences including anomalous Hall and Kerr responses and
spin-split transport without stray fields — attractive for spintronics. The bottleneck is
materials: only a few dozen altermagnets are confirmed, so predictive discovery is
essential.

Two computational strategies dominate. (i) Symmetry screening of experimentally-determined
magnetic structures: the MAGNDATA database analyzed with tools such as `amcheck`, followed
by DFT confirmation [PRMaterials 9.064403]. (ii) Machine learning: Gao et al. [NSR 2025]
pre-train a graph neural network, fine-tune on limited positives, and screen ~26,000
candidates, confirming 50 new altermagnets by DFT.

Both strategies share a structural assumption we argue is a liability. Altermagnetism is a
*symmetry* property, decided by whether a spin-reversing rotation is a crystal symmetry.
But the structures fed to these methods are DFT-relaxed, and relaxation routinely
introduces sub-0.1 Å distortions that break the exact rotation while leaving the material
physically the same high-symmetry compound. Symmetry analysis at the conventional tight
tolerance (≈10⁻³ Å) then reports the distorted low-symmetry group and classifies the
material as a conventional antiferromagnet. A GNN trained on such structures inherits the
same bias. The consequence is a **population of altermagnets hidden in plain sight**.

Here we (1) build an intentionally simple, interpretable screening pipeline that isolates
the two ingredients that matter — trusted labels and tolerance-aware symmetry
verification; (2) demonstrate the tight-tolerance blind spot quantitatively; (3) validate
against two independent DFT studies; and (4) confirm by two-stage first-principles calculation
**six new altermagnets** that a state-of-the-art GNN screen did not surface, while
rejecting five false candidates through successively stricter physical criteria.

---

## 2. Methods

**Trusted training labels.** Materials are labeled altermagnet (AM) or antiferromagnet
(AFM) by applying `amcheck` to their magnetic structure. Training labels come only from
MAGNDATA, whose moments are *experimentally* determined: 929 commensurate entries
(Bilbao Crystallographic Server) yield 262 AM / 303 AFM after removing ferromagnetic and
symmetry-frustrated cases.

**Leakage-free descriptors.** Each structure is described by 31 crystal-only features:
composition-weighted element-property statistics plus non-magnetic symmetry/geometry.
No feature derives from magnetic moments. Symmetry features are computed at
symprec = 0.1 Å to place DFT-relaxed (Materials Project) and experimental (MAGNDATA)
structures on a comparable footing (§3.2).

**Classifier.** A histogram gradient-boosted tree with balanced class weights,
evaluated by stratified 5-fold cross-validation (PR-AUC).

**Candidate scoring and verification.** The trained model scores Materials Project AFM
structures. High-probability candidates are verified by re-running `amcheck` across
symmetry tolerances (10⁻³–10⁻¹ Å); a candidate is *robust* when classified AM at both
0.05 and 0.1 Å (guarding against over-symmetrization).

**First-principles confirmation.** Spin-polarized DFT+U (Quantum ESPRESSO 7.3.1;
PBE; Hubbard U on open-shell d states: 4.5 eV Fe-3d, 3.5 Cr-3d, 4.0 Mn/Co-3d,
3.0 V-3d, 6.0 Cu-3d, 2.5 Mo-4d, 2.0 W-5d/Zr-4d; PAW pseudopotentials) with the
compensated collinear AFM configuration encoded by splitting each magnetic element
into two species of opposite starting magnetization. Correlated double perovskites
exhibit bistable SCF (competition with ferrimagnetic states); convergence required
pinning the compensated configuration via a constrained-magnetization penalty
(`constrained_magnetization='atomic'`, λ = 0.5) with Marzari–Vanderbilt smearing
(0.03 Ry) and plain Broyden mixing (β = 0.1, history 20). Where the SCF reached a
bounded ~10⁻²-Ry residual rather than formal convergence (the two Ba perovskites),
the pinned density from a controlled stop was used; these are flagged first-pass.
Band structures were computed along dense k-paths and spin-resolved eigenvalues
extracted from the XML data files. Confirmation criteria: (i) momentum-dependent
up/down splitting ≥ 50 meV within ±3 eV of E_F; (ii) net moment ≤ 0.5 µ_B/cell
(compensation); and (iii) a **nodal criterion** — the per-k splitting must fall
below half its maximum somewhere on the path, since altermagnetic symmetry requires
nodal directions; large but k-uniform splitting at zero net moment instead signals
a compensated ferrimagnet. Calculations were run in two stages: first-pass
(ecut 45 Ry, 2×2×2 charge k-mesh, conv 5×10⁻⁴ Ry) on all candidates, then
refinement (ecut 60 Ry, ecutrho 480 Ry; 4×4×4 k for cells ≤ 18 atoms, 3×3×3 for
larger; conv 10⁻⁴–10⁻⁵ Ry) on all first-pass positives; only refinement-surviving
materials are claimed. All calculations ran on a single Apple M1 Max workstation
using a natively compiled QE.

---

## 3. Results

### 3.1 Label provenance dominates

A model trained on Materials Project (DFT-derived, noisy) AM/AFM labels attains
reasonable cross-validation yet scores at chance (ROC-AUC 0.54) on the trusted MAGNDATA
set — a textbook distribution-shift failure. The identical features trained on trusted
MAGNDATA labels reach ROC-AUC 0.91 / PR-AUC 0.90. Trusted labels, not model capacity,
are decisive.

### 3.2 The tolerance blind spot, quantified

At the conventional 10⁻³ Å tolerance, 63% of Materials Project candidates read as
triclinic versus 0.2% of experimental MAGNDATA structures — a gross feature-distribution
mismatch driven entirely by relaxation distortions. Loosening to 0.1 Å reduces the MP
triclinic fraction to 26% and aligns the distributions. Case studies confirm the
mechanism: Sr₂FeWO₆ and Ba₂FeWO₆ read as triclinic/monoclinic at 10⁻³ Å but recover
their ideal double-perovskite symmetry — and an altermagnetic classification — at
0.05–0.1 Å.

### 3.3 Validation against independent studies

The pipeline's confirmed set overlaps prior DFT-confirmed altermagnets, including an
**exact-structure match** with Gao et al.: Ba₂CoSi₂O₇ (mp-510015), plus compound-level
matches LiFeF₄ and CaLaCrMoO₆. As a positive control, our DFT setup reproduces
CaLaCrMoO₆'s altermagnetism (205 meV splitting, formally converged), independently
validating the recipe applied to the novel candidates.

### 3.4 Two-stage first-principles confirmation: six new altermagnets

Refined DFT+U verdicts for all twelve tolerance-robust candidates (refined values;
first-pass in parentheses where different):

| Material | MP id | max split (meV) | per-k range | net mom (µ_B) | electronic | verdict |
|---|---|---|---|---|---|---|
| Y₂Mo₂O₇ | mp-2674749 | 405 (360) | 4–405 | +0.01 | insulating (~0.9 eV) | **AM, new** (nodal) |
| SrLaCoO₄ | mp-1274449 | 281 | 11–281 | −0.01 | metallic | **AM, new** |
| Ba₂FeMoO₆ | mp-1277787 | 275 (366) | 3–275 | −0.00 | metallic | **AM, new** (nodal) |
| MgCu₂(O₂F)₂ | mp-2240166 | 254 (269) | 5–254 | −0.00 | insulating (~0.4 eV) | **AM, new** |
| CaLaCrMoO₆ | mp-1048863 | 210 (205) | 12–210 | +0.01 | insulating (~0.6 eV) | AM (control ✓) |
| Sr₂FeWO₆ | mp-19266 | 116 (125) | 11–116 | +0.00 | insulating (~2.1 eV) | **AM, new** |
| VOF₂ | mp-759163 | 85 (93) | 1–85 | +0.00 | insulating (~1.7 eV) | **AM, new** (nodal) |
| ZrCoO₃ | mp-756665 | 19 (115) | 6–19 | −0.00 | rejected at refinement |
| Ca₃Co₂O₇ | mp-1580697 | 758 | 390–758 | −0.83 | rejected (magnetized at dense k) |
| Ba₂FeWO₆ | mp-1272506 | 1888 (232) | 1656–1888 | −0.00 | rejected (node-less: comp. ferrimagnet) |
| MnOF | mp-1277241 | 30 | 24–30 | +0.00 | rejected (sub-threshold) |
| CsTaCo(OF₂)₂ | mp-684727 | — | — | +1.70 | rejected (ferrimagnetic) |

Every confirmed material satisfies all three criteria: splitting ≥ 50 meV, net moment
≈ 0, and nodal momentum-dependence (min per-k splitting ≤ 10% of max in all six).
Confirmed magnitudes shift by ≤ 25% between first-pass and refined settings, while
verdicts for the six are unchanged — the qualitative fingerprint is robust. The
electronic classification (from the refined band structures) splits the set into two
metallic altermagnets — SrLaCoO₄ and Ba₂FeMoO₆, natural candidates for
altermagnet/superconductor heterostructures and spin-transport experiments — and four
insulating ones suited to low-dissipation magnonic and tunnel-barrier applications.
Parenthetical gaps are indicative only: PBE+U systematically misestimates gap
magnitudes, so the metal/insulator distinction is claimed, the values are not.

The five rejections trace a graded attrition that validates each filter stage.
MnOF is symmetry-permitted but electronically weak (30 meV). CsTaCo(OF₂)₂ will not
hold a compensated state even under the magnetization constraint. ZrCoO₃'s
first-pass 115 meV collapses to 19 meV at refined numerics — a loose-settings
artifact caught by our own quality pass. Ca₃Co₂O₇ drifts to a magnetized solution
(−0.83 µ_B) on the denser k-mesh. Most instructively, Ba₂FeWO₆ develops a *giant*
(1.9 eV) but nearly k-uniform splitting: the absence of nodes — which altermagnetic
symmetry requires — identifies its refined ground state as a compensated
ferrimagnet (symmetry-inequivalent sublattices), not an altermagnet. Symmetry
analysis bounds what may occur; two-stage DFT decides what does.

### 3.5 Why prior screens missed these

None of the six appears in Gao et al.'s 50 confirmed materials, although both searches
mine the same structural families (their set contains the *adjacent* compositions
Ca₃Cr₂O₇ and ZrCrO₃, chromium analogues of two of our candidates). The most
parsimonious explanation is the distortion blind spot: methods that trust the as-relaxed
cell cannot see altermagnets whose defining rotation is broken only numerically. An
explicit re-symmetrization step — cheap and interpretable — recovers them.

---

## 4. Discussion

The recurring lesson is that both failure modes we identified are *data-representation*
problems, not model-capacity problems: noisy DFT labels destroy transferability
(§3.1), and numerically-distorted geometry hides the defining symmetry (§3.2). A simple
classifier with trusted labels plus tolerance-aware verification outperforms — in
novel-material yield — a pre-trained GNN on the same chemistry, because it corrects the
representation rather than adding capacity. We recommend that altermagnet screens
evaluate symmetry across a tolerance range, or symmetrize before classifying, rather
than trusting a single tight tolerance.

**Configuration-specific claims.** Our calculations address the compensated
collinear AFM configuration catalogued by the Materials Project for each compound.
For Sr₂FeWO₆ this coincides with the experimentally observed ground state
(AFM insulator, T_N ≈ 37 K). For Ba₂FeMoO₆ — whose family is known for
half-metallic ferrimagnetism — and Y₂Mo₂O₇ — experimentally a frustrated
pyrochlore spin glass — the studied configuration is a competing order rather
than the observed ground state; realizing their altermagnetism would require
stabilizing that configuration (e.g. by strain, doping or field protocols). VOF₂
and MgCu₂(O₂F)₂ are computationally predicted structures whose synthesis remains
to be established. All claims should be read as configuration-specific.

**Limitations.** Hubbard U values are standard literature choices, not
material-specific fits, and the refined k-meshes (4×4×4 / 3×3×3) remain modest by
converged-property standards; magnitudes may shift further at denser sampling,
though the ≤ 25% first-pass→refined drift for all six confirmed materials suggests
stability. Néel temperatures — the practically limiting thermal scale — remain to
be computed. Wave-type classification (d/g/i) from the nodal patterns is left to
follow-up work.

---

## 5. Conclusion

An interpretable, trusted-data pipeline with tolerance-aware symmetry verification and
two-stage first-principles confirmation yields **six new DFT-confirmed altermagnets**
spanning four structural families, reproduces an independently-confirmed control, and
rejects five false candidates through successively stricter physical criteria. The enabling insight — that tight-tolerance symmetry
screening systematically hides altermagnets in slightly-distorted high-symmetry cells —
is both a concrete list of new materials and a methodological correction for the field.

---

## Data / code availability

Pipeline: `pull_and_label.py`, `fetch_magndata.py`, `label_mcif.py`,
`featurize_candidates.py`, `train_classifier.py`, `verify_candidates.py`,
`prep_qe.py`, `run_batch2.sh`, `analyze_qe_xml.py`, `build_qe_native.sh`.
Results: `qe_results.csv`, `final_altermagnet_candidates.csv`,
`FINDINGS_double_perovskites.md`.

## References

1. L. Šmejkal, J. Sinova, T. Jungwirth, *Beyond conventional ferromagnetism and
   antiferromagnetism: A phase with nonrelativistic spin and crystal rotation
   symmetry*, Phys. Rev. X **12**, 031042 (2022).
2. L. Šmejkal, J. Sinova, T. Jungwirth, *Emerging research landscape of
   altermagnetism*, Phys. Rev. X **12**, 040501 (2022).
3. J. Krempaský et al., *Altermagnetic lifting of Kramers spin degeneracy*,
   Nature **626**, 517 (2024). [experimental verification, MnTe]
4. A. Smolyanyuk, L. Šmejkal, I. I. Mazin, *A tool to check whether a
   symmetry-compensated collinear magnetic material is antiferro- or altermagnetic*
   (amcheck), SciPost Phys. Codebases **30** (2024).
   doi:10.21468/SciPostPhysCodeb.30
5. *High-throughput screening of altermagnetic materials*, Phys. Rev. Materials
   **9**, 064403 (2025), doi:10.1103/PhysRevMaterials.9.064403; see also
   *High-throughput quantification of altermagnetic band splitting*,
   Phys. Rev. Materials (2025), doi:10.1103/mmdm-hrj4 (arXiv:2509.14729).
6. Z.-F. Gao, S. Qu, B. Zeng, Y. Liu, J.-R. Wen, H. Sun, P.-J. Guo, Z.-Y. Lu,
   *AI-accelerated discovery of altermagnetic materials*, Natl. Sci. Rev. **12**,
   nwaf066 (2025). doi:10.1093/nsr/nwaf066
7. M. Naka, Y. Motome, H. Seo, *Altermagnetic perovskites*, npj Spintronics
   **3**, 1 (2025).
8. S. V. Gallego et al., *MAGNDATA: towards a database of magnetic structures.
   I. The commensurate case*, J. Appl. Cryst. **49**, 1750 (2016).
9. A. Jain et al., *The Materials Project: A materials genome approach to
   accelerating materials innovation*, APL Mater. **1**, 011002 (2013).
10. P. Giannozzi et al., *QUANTUM ESPRESSO: a modular and open-source software
    project for quantum simulations of materials*, J. Phys.: Condens. Matter
    **21**, 395502 (2009); *Advanced capabilities for materials modelling with
    Quantum ESPRESSO*, ibid. **29**, 465901 (2017).
11. S. P. Ong et al., *Python Materials Genomics (pymatgen)*, Comput. Mater. Sci.
    **68**, 314 (2013). A. Togo, I. Tanaka, *spglib*, arXiv:1808.01590.
12. F. Pedregosa et al., *Scikit-learn: Machine learning in Python*, J. Mach.
    Learn. Res. **12**, 2825 (2011).

*Note: all DOIs verified except the author list of ref 5 (add from the
published paper). See LITERATURE_CHECK.md for two prior-art items to grep
before submission (arXiv:2601.01617 SI; Naka et al. compound list).*
