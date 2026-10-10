# Metallic altermagnets are rare and mislabeled: a verified census, five failure modes, and three predictions

*Draft v0.2 (2026-07-28). Sequel to "Six altermagnets hidden by symmetry
tolerance". Numbers below are from the session logs in `supercon/`;
re-verify each before submission.*

## Abstract

Altermagnetic metals are the required platform for the rapidly growing
theory of altermagnetic superconductivity, yet pairing proposals reuse the
same two or three model compounds. We ask why, and answer quantitatively:
screening the entire Materials Project, only 439 metallic antiferromagnets
exist within 0.1 eV/atom of the hull, of which just 12 carry robust
altermagnetic symmetry labels and 58 more are tolerance-sensitive. We then
show that symmetry labels alone — the basis of every published altermagnet
screen — fail in four distinct ways, each demonstrated on a named
compound (a fifth mode, ferrimagnet contamination, defeats naive DFT
verification itself): (i) *ordering-vector artifacts*: labels computed on DFT-guessed
k=0 orderings are refuted by experimental neutron structures (LaCu3Fe4O12,
k=(1/2,1/2,1/2); Er2Fe3Si5, k=(1/2,0,0) — for the latter we enumerate all
128 collinear orderings at the experimental wavevector and prove none are
altermagnetic); (ii) *protected degeneracy*: P2_1/c FeOF passes the
symmetry test at every tolerance yet shows identically zero spin splitting
in DFT; (iii) *negligible magnitude*: Ba2CrO4 is symmetry-allowed but
splits by only 4 meV; and (iv) *unclassifiability*: 13% of the census
receives no label at all, a blind spot robust to a 50-fold sweep of the
moment threshold and enriched 5.5-fold in copper compounds
(p = 3e-6) — i.e. screening is systematically blind to exactly the
chemistry where unconventional superconductivity lives. A simple corollary of (i) — altermagnetism requires
k=0 compensated order, while high-throughput magnetic workflows are biased
toward k=0 guesses — contaminates existing candidate lists at their source.
Applying the full verification chain (experimental magnetic structures
where deposited, spin-polarized DFT band splitting where not), our
pipeline blind-rediscovers every published experimentally grounded
metallic altermagnet it could have (CoNb4Se8, La2NiO4, SrMnO3, FeOF) and
yields three predictions on as-yet-unsynthesized structures: Li2MnCuO4
(655 meV, the largest splitting in our set), Mn2CuO4 (423 meV), and
Ba(FeN)2 — a layered iron nitride with 369 meV splitting, compensated
moments, an AFM ground state 33 meV/Fe below a coexisting nonmagnetic
solution, and square-lattice Fe planes in the structural neighborhood of
the iron-pnictide superconductors. We additionally apply the razor to our
own strongest result and retract it: YFe4(CuO4)3, the one synthesized
candidate, is reported in 2013 literature as a charge-disproportionated
(3Fe5+ : 5Fe3+) ferrimagnetic semiconductor below 250 K — an ordering
whose supercell the screened primitive cell cannot represent, making the
compensated k=0 solution an artifact of cell choice rather than a
discovery. The general lesson is that high-throughput screens are blind by
construction to any order requiring a supercell, and that the decisive
check is a measured ordering vector, not a converged calculation.

## 1. Introduction

- Altermagnetic superconductivity theory (2023-) needs metallic
  altermagnets; supply side never quantified. [cite Šmejkal et al.;
  pairing-theory papers; KV2Se2O, RuO2 debates]
- Prior screens (incl. Gao et al. NSR 2025 and our previous work) rank
  candidates by symmetry labels on database orderings; label validity
  never checked against experimental magnetic structures.
- This work: census + five failure modes + verified shortlist + three
  predictions + a worked self-refutation (3.7).

## 2. Methods

- MP query: magnetic_ordering=AFM, is_metal, E_hull <= 0.1 eV/atom
  (2026-07; 439 materials). amcheck tolerance sweep (1e-5..1e-2) on MP
  collinear orderings — identical to prior work.
- k=0 razor: MAGNDATA cross-reference (2,410 entries; 1,153 commensurate).
  Match by reduced formula; commensurate entries re-labeled from
  experimental mcif; incommensurate or k != 0 entries excluded by symmetry
  (translation-connected sublattices ⇒ Kramers degeneracy).
- Er2Fe3Si5 ordering enumeration: 2x1x1 supercell of mp-680269, all 2^8/2
  collinear k=(1/2,0,0) Er patterns, amcheck each (Fe nonmagnetic per
  neutron work).
- DFT: QE PBE(+U where d-shell localized; none for Ba(FeN)2), PAW,
  50/400 Ry, gaussian smearing 0.01 Ry; AFM encoded via split species;
  splitting metric = max |E_up - E_down| within 3 eV of E_F on a
  120-point path; altermagnet := net moment ~0 AND k-dependent splitting
  >= 50 meV with symmetry-degenerate lines present. Nodal test is ABSOLUTE
  (min per-k splitting < 25 meV) and compensation strict
  (|net moment| <= 0.10 muB/cell); see failure mode V.
- SC-analogy score (secondary, motivational only): HistGradientBoosting
  Tc regressor trained on 21,263 SuperCon entries (random-CV R2 0.923,
  grouped-by-chemical-system R2 0.857); explicitly NOT a Tc prediction
  for magnetic compounds.

## 3. Results

### 3.1 The census: metallic altermagnets are rare
439 metallic near-stable AFMs in all of MP; verdicts: 299 AFM, 58
REVIEW-FLIP, 12 AM, 15 uncompensated-skip, 55 error.

**Table 1 — the 12 clean AM labels and what verification did to them:**

| Formula | MP id | E_hull (eV/at) | SC-analogy (K) | Verification status |
|---|---|---|---|---|
| LaFe4(CuO4)3 | mp-1105546 | 0.000 | 73 | KILLED: exp k=(1/2,1/2,1/2) [MAGNDATA 1.846] |
| Ba(FeN)2 | mp-1245963 | 0.030 | 19 | DFT: ALTERMAGNET (369 meV) — new prediction |
| FeOF | mp-675006 | 0.032 | 13 | DFT: ALTERMAGNET (419 meV) — matches PRM 2025 |
| FeOF | mp-754053 | 0.026 | 13 | DFT: no splitting (protected) |
| Y2Mo2O7 | mp-18265 | 0.013 | 8 | unverified (no exp structure) |
| Ba2CrO4 | mp-561426 | 0.000 | 7 | DFT: 4 meV (negligible) |
| La2NiO4 | mp-21874 | 0.048 | 4 | CONFIRMED exp (MAGNDATA 0.45); published |
| Ho2Fe3Si5 | mp-1200585 | 0.000 | 4 | KILLED (family): exp k=(1/2,0,0) [PRB 29,271] |
| Er2Fe3Si5 | mp-680269 | 0.000 | 2 | KILLED: exp k=(1/2,0,0), 128/128 orderings AFM |
| Cu(BiO2)2 | mp-560165 | 0.088 | 0 | KILLED: exp AFM (MAGNDATA 0.348/0.694/0.695) |
| Mn2Sb2O7 | mp-1190856 | 0.037 | 0 | unverified (no exp structure) |
| SrMnO3 | mp-559975 | 0.000 | -1 | CONFIRMED exp (0.1018/0.1019); published |

Scorecard: of 12 symmetry-clean labels, verification kills 4, confirms 2
(both already published), promotes 2 to new predictions, demotes 2 as
splitting-free, and leaves 2 open. A symmetry label alone is right about
"new altermagnetic metal" in at most 2/12 cases. (Ho2Fe3Si5 is killed by
family systematics, not a direct measurement of its own k — noted.)

### 3.2 Failure mode I: ordering-vector artifacts
- LaCu3Fe4O12 (top-ranked candidate: on-hull, metallic, clean AM label):
  MAGNDATA 1.846 gives k=(1/2,1/2,1/2), TN=393 K ⇒ conventional AFM.
- Er2Fe3Si5 (clean AM label; member of the R2Fe3Si5 superconductor
  family, SC-AFM coexistence): neutron k=(1/2,0,0) [Moodenbaugh 1984];
  enumeration: 128/128 orderings AFM. Kills the tantalizing
  "already-synthesized altermagnetic superconductor" reading.
- General statement + proof sketch: k != 0 ⇒ antitranslation symmetry ⇒
  spin-degenerate bands. Database orderings are k=0-biased ⇒ systematic
  false positives.

### 3.3 Failure modes II and III: protected and negligible splitting
- FeOF P2_1/c: AM label at all tolerances, splitting identically 0.
- Ba2CrO4: AM label, 4 meV. Symmetry allowance is necessary, not
  sufficient; magnitude must be computed.

### 3.4 Validation: blind rediscovery of all known cases
CoNb4Se8 (MAGNDATA 0.1112 experimental AM; Nat. Commun. 2025 + ARPES),
La2NiO4 (0.45), SrMnO3 (0.1018/9), FeOF P4_12_12 (419 meV here; PRM 2025
anion-correlation NRSS, TN 315 K). Pipeline finds every published metallic
altermagnet with a deposited/claimed structure, from labels alone.

### 3.5 New predictions: Li2MnCuO4, Mn2CuO4, Ba(FeN)2

Three DFT-verified altermagnet predictions, none previously claimed. All
three are structures Materials Project marks as theoretical (never
synthesized), so no experimental magnetic structure can currently confirm
or refute them; they are predictions awaiting synthesis, and each carries
the cell-size caveat established in 3.8. A fourth candidate,
YFe4(CuO4)3, was our lead until experimental literature refuted it; we
retain that episode as section 3.8 rather than deleting it.

- **Li2MnCuO4 (mp-776054)** — largest splitting in the set: 655 meV,
  17% of k-points, true nodes (min 0.2 meV), net moment 0.00; C2/c,
  theoretical, e_hull 0.082 eV/atom. Promoted from REVIEW-FLIP.
- **Mn2CuO4 (mp-1274535)** — 423 meV, 37% of k-points;
  spinel-derived I4_1/amd; theoretical, e_hull 0.051.
- **Ba(FeN)2 (mp-1245963)** — below.

**Failure mode V (verification-stage false positives).** Two candidates
pass a *relative* nodal test (min per-k splitting < 0.5 x max, the
criterion in our prior pipeline) yet are not altermagnets: CuNi3O4
(1356 meV, splitting at 100% of k-points, minimum 739 meV) and Li2CuNiO4
(1067 meV, 100% of k-points, minimum 447 meV, net moment 0.27 muB).
Altermagnetism requires symmetry-protected nodal surfaces on which the
splitting vanishes *identically*; a minimum of several hundred meV means
no such surface exists, and the finite net moment identifies these as
ferrimagnets. Genuine altermagnets in our set have per-k minima of
0.03-10 meV, i.e. numerically zero. We therefore replace the relative
criterion with an absolute one (min per-k splitting < 25 meV AND
|net moment| <= 0.10 muB), which reclassifies both. Screens that verify
by splitting magnitude alone will admit ferrimagnets; the node test, done
absolutely, is what separates the two.

**Self-correction.** MnVAgO4 (mp-542979) was flagged as an altermagnet
candidate by our own ML triage (P_AM 0.59) and reported as an early hit.
It is experimentally synthesized (e_hull 0.025 eV/atom, Pnma) and its Cu
analogue MnVCuO4 shows protected degeneracy, so we verified it directly:
maximum splitting 0.04 meV, i.e. identically zero. MnVAgO4 is not an
altermagnet, and we retract the earlier flag. Both members of the
MnV(Cu,Ag)O4 pair are symmetry-labeled candidates with rigorously zero
splitting.

#### Ba(FeN)2 details
369 meV splitting, 48% of path k-points split, net moment 0.04, AFM ground
state by 33 meV/Fe over a coexisting self-consistent nonmagnetic solution;
theoretical structure, E_hull 0.030 eV/atom. Weak itinerant moments
(MP r2SCAN ±0.2 μB; PBE 1.1 μB/Fe) — magnetism fragile, near instability.
Square Fe lattice, pnictide-like; SC-analogy score 19 K (motivational).
Falsifiable predictions: neutron k=0 compensated order; ARPES/MOKE
splitting signatures if synthesized.

### 3.6 Failure mode IV: the unclassifiable 13% is copper-enriched

55 of 439 metallic AFM candidates (12.5%) receive no label at all: amcheck
raises at every tolerance, with two causes — orbit-level spin imbalance
("number of up spins should be the same as the number of down spins", 43
cases) and mixed magnetic/nonmagnetic sites of the same element
("Something is wrong with the description of magnetic atoms!", 12 cases).
Published screens report such materials as errors, or omit them silently;
either way they are removed from consideration.

This is not a tunable artifact. Discretizing continuous DFT magmoms into
up/down/nonmagnetic labels depends on a free moment threshold (0.05 muB
here and in prior work), so we swept it over a 50-fold range
(0.01-0.50 muB): all 55 remain unclassifiable at every value, and none
becomes AM (moment_threshold_sweep.csv). Unlike symmetry tolerance, this
knob does not move verdicts — the blind spot is structural, not
parametric.

It is, however, strongly non-random. Copper-containing compounds are
5.5x over-represented among unclassifiable materials (18/55 vs 30/369;
Fisher exact one-sided p = 3.0e-6), and unclassifiable cells are larger
(mean 34.1 vs 26.2 sites; p = 0.02). The affected compounds include
YBCO-family and layered cuprate phases (Ba10Gd4Y(Cu3O7)5, Ba2(CuO2)3,
Sr9Nd3Cu12(PbO4)8). The mechanism is straightforward: chemically complex
cuprates have many inequivalent Cu sites whose DFT moments vary in
magnitude and sign within a symmetry orbit, which the compensated-orbit
test cannot accept.

We explicitly did NOT find enrichment in SC-analogy score itself
(medians 7.2 vs 9.3 K; Mann-Whitney p = 0.33) — the higher mean of the
unclassifiable set is driven by a few extreme cuprates, not a shifted
distribution. The defensible claim is chemical, not thermodynamic:
altermagnet screening is systematically blind to copper-rich, structurally
complex metals, which is precisely the chemistry where unconventional
superconductivity lives. The altermagnet/superconductor intersection is
therefore under-explored for tooling reasons rather than physical ones.

### 3.7 REVIEW-FLIP resolution and the open list
DFT adjudicated 7 of the 58 tolerance-sensitive (REVIEW-FLIP) candidates:
Li2MnCuO4 ALTERMAGNET (655 meV), Mn2CuO4 ALTERMAGNET (423 meV),
YFe4(CuO4)3 ALTERMAGNET (373 meV), CuNi3O4 ferrimagnet (no nodes),
Li2CuNiO4 ferrimagnet (net moment), MnVCuO4 zero splitting (protected),
CaLaFeCuO6 2 meV (negligible). A 3/7 hit rate confirms REVIEW-FLIP as
"genuinely ambiguous — verify", not noise: the tolerance-artifact class
from our prior work contains real altermagnets, ferrimagnets, and
protected conventional AFMs in comparable numbers.

Corollary for prior work: MnVCuO4's protected degeneracy flags its Ag
sibling MnVAgO4 — an ML-flagged (P_AM 0.59, never DFT-verified) candidate
from our first screen — for re-examination.

Remaining: 61/70 AM+flip candidates have no experimental magnetic
structure; 54 REVIEW-FLIPs un-adjudicated (blocked mainly on Ni/Li/Ag/Se
pseudopotentials). Full table in mp_metallic_am/results.csv +
qe_verify/qe_results.csv.

### 3.8 Self-application: our own lead prediction, refuted

We applied the paper's own razor to our strongest result. YFe4(CuO4)3
(= YCu3Fe4O12) was the lead prediction: metallic, E_hull 0.018 eV/atom,
373 meV splitting, true nodes, zero net moment, and — uniquely among our
candidates — experimentally synthesized, which we advertised as making
neutron determination of its ordering vector immediately feasible. Because
MAGNDATA holds no entry for it, we treated the k=0 assumption as an
open, falsifiable premise. It is false, and the disproof was already in
the literature.

Etani et al. (J. Am. Chem. Soc., 2013; high-pressure synthesis at 15 GPa,
1273 K; cubic Im-3, a = 7.3076 A) report that YCu3Fe4O12 undergoes, at
250 K, a simultaneous charge disproportionation
8Fe(3.75+) -> 3Fe(5+) + 5Fe(3+), **ferrimagnetic** ordering, and a
metal-to-semiconductor transition. Every clause contradicts an
altermagnetic assignment:

1. *Ferrimagnetic, not compensated.* Altermagnetism requires zero net
   magnetization; a ferrimagnet has none of the defining symmetry.
2. *Charge disproportionation makes the Fe sublattices inequivalent.* A
   3:5 split cannot be related by any symmetry operation, so opposite-spin
   sublattices are not symmetry-connected — the altermagnetic condition
   fails at its root.
3. *Semiconducting below the ordering temperature.* The compound is not a
   metal in its magnetically ordered state, so it cannot be a metallic
   altermagnet.
4. *Wrong cell, and wrong symmetry.* The experimental ordered phase
   requires 8 Fe (two formula units); the MP entry we screened has 4 Fe in
   a 20-atom Immm cell. Our converged calculation gave four Fe moments of
   *identical* magnitude (+/-3.865 muB, 2 up / 2 down, Cu nonmagnetic) —
   perfect compensation that is an artifact of a cell too small to host
   the observed 3:5 order. Doubling to accommodate it means k != 0 in the
   parent cell, which by the corollary of 3.2 forbids altermagnetism
   outright.

This is failure mode I in its most instructive form: not a database
ordering that merely disagrees with experiment, but a *unit cell that
structurally forbids the experimental ground state*. High-throughput
screens relax primitive cells; any ordering requiring a supercell —
charge disproportionation, spin-density waves, longer-period magnetic
order — is invisible to them by construction, and the compensated k=0
solution they return is guaranteed, not discovered. Every candidate in
this work whose experimental magnetic structure is unknown (including our
three surviving predictions) inherits this caveat; verification against a
measured ordering vector, not merely a converged calculation, is what
separates a candidate from a claim.

We report this at length because the sociology matters: the refuting paper
is thirteen years old, indexed, and in a major journal. The screening
literature's failure mode is not missing data but unconsulted data.

## 4. Discussion

- Why this matters for altermagnetic superconductivity: supply-side
  scarcity is real; verified-metal shortlist; Ba(FeN)2 as pnictide-adjacent
  target; magnetic-instability proximity as a pairing-relevant feature.
- Limitations: PBE(+U) ordering guesses for unverified candidates (razor
  applies to us too); polymorph sensitivity (FeOF: 419 vs 0 meV);
  SC-analogy model has no negative class.

## 5. Conclusion

## Data / code availability
supercon/ pipeline: screen_metallic_am.py, enumerate_er_orderings.py,
razor_matches.csv, qe_verify/ inputs+outputs, tc_model training scripts.

## References
*(verify page numbers/DOIs before submission; retrieved 2026-07)*

1. Šmejkal, Sinova, Jungwirth, "Emerging research landscape of
   altermagnetism", Phys. Rev. X 12, 040501 (2022). [foundational]
2. A.R. Moodenbaugh, D.E. Cox, C.B. Vining, C.U. Segre,
   "Neutron-diffraction study of magnetically ordered Er2Fe3Si5",
   Phys. Rev. B 29, 271 (1984). [k=(1/2,0,0); SC-AFM coexistence]
3. Gallego et al., "MAGNDATA: towards a database of magnetic structures",
   J. Appl. Cryst. 49, 1750 (2016). [2,410 entries as of 2026-07]
4. amcheck: Smolyanyuk, Šmejkal, Mazin, SciPost Phys. Codebases (2024).
5. "Altermagnetism in the layered intercalated transition metal
   dichalcogenide CoNb4Se8", Nat. Commun. 16 (2025),
   doi:10.1038/s41467-025-58642-4; also arXiv:2503.16670 (ARPES).
6. Bernardini, Fiebig, Cano, "Ruddlesden-Popper and perovskite phases as
   a material platform for altermagnetism", arXiv:2401.12910. [La2NiO4]
7. "Anion correlation induced nonrelativistic spin splitting in rutile
   antiferromagnets", Phys. Rev. Materials (2025); arXiv:2512.12179.
   [FeOF, TN=315 K]
8. K. Hamidieh, "A data-driven statistical model for predicting the
   critical temperature of a superconductor", Comput. Mater. Sci. 154,
   346 (2018). [21,263-entry SuperCon set; our R2 0.923 matches]
9. V. Stanev et al., "Machine learning modeling of superconducting
   critical temperature", npj Comput. Mater. 4, 29 (2018).
10. Gao et al., NSR (2025). [GNN altermagnet screening — see prior
    manuscript's discussion of overlap]
11. [our prior manuscript] "Six altermagnets hidden by symmetry
    tolerance...", altermag/MANUSCRIPT_draft.md.
12. Jain et al., "The Materials Project", APL Mater. 1, 011002 (2013).
13. Giannozzi et al., "Advanced capabilities for materials modelling with
    Quantum ESPRESSO", J. Phys.: Condens. Matter 29, 465901 (2017).
14. "Discovery of a metallic room-temperature d-wave altermagnet
    KV2Se2O", arXiv:2408.00320. [motivating scarcity of AM metals]
