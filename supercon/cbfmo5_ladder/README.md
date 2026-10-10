# CaBa2FeMoO5: hypothetical Sr3Fe2O5-type ladder oxide

Started 2026-10-10. This is the literal formula as asked, built as a hypothetical
structure.

## Why this structure

CaBa2FeMoO5 has the A3B2O5 stoichiometry, the same as Sr3Fe2O5. Sr3Fe2O5 is a
real compound, made by CaH2 low-temperature reduction of Sr3Fe2O7: square-planar
Fe2+ forming two-leg ladders, Immm, a = 3.515, b = 3.953, c = 20.913 A. It is a
G-type AFM insulator; a sign of metallization appears only near 34 GPa, together
with a spin-state change and a switch to ferromagnetism.

Charge balance works only in this "reduced" form: Fe2+ plus Mo2+, both
square-planar. Mo2+ is not known in any oxide, so even this is a speculative
target that could only be reached by topotactic reduction, not by direct
synthesis. Square-planar layers made this way are, however, the motif behind
the superconducting infinite-layer and reduced Ruddlesden-Popper nickelates.
That is the only reason the question is worth a calculation.

## Model

- Primitive I-centred cell, 10 atoms, 1 formula unit.
- Ca on the perovskite-block A site (multiplicity 1), Ba on the two rock-salt A
  sites.
- Fe and Mo on the two ends of each ladder rung. This makes the legs pure-Fe and
  pure-Mo; other orderings are not sampled.
- Starting cell is Sr3Fe2O5 expanded about 3% for Ba, then vc-relaxed in the
  ferrimagnetic state.
- PBE+U with U(Fe) = 4.5 and U(Mo) = 2.5 eV, ecut 60/480 Ry, 7x7x7 k for the
  SCF, 10x10x10 k (tetrahedra) for the DOS.

## Runs (`run2.sh`)

`run2.sh` waits for `../bfmo_sc_check/run.sh` to finish, then:
1. vc-relax
2. `post_relax.py` writes the ferrimagnet, ferromagnet and nonmagnetic inputs at
   the relaxed geometry
3. SCF, then NSCF and dos.x for each magnetic state
4. `analyze.py` writes `results.txt`

## What this cannot tell you

- Thermodynamic stability. No convex-hull calculation is attempted, and a Mo(II)
  oxide is expected to be far above the hull.
- Dynamical stability (no phonons).
- G-type or leg-AFM order: that would need a supercell. The parent's real ground
  state is G-AFM.
- Electron-phonon Tc. Allen-Dynes is invalid if the ground state is magnetic,
  which is expected.

The superconductivity verdict therefore rests on the same test as for
Ba2FeMoO6: whether the ground state is magnetic, and whether both spins are
present at E_F.
