# Superconductivity check: "CaBa2FeMoO5" / Ba2FeMoO6 / Ca-doped Ba2FeMoO6

Started 2026-10-10. The question: could this composition superconduct at low temperature?

## 1. The literal formula CaBa2FeMoO5

The formula does not charge-balance. Ca2+ + 2 Ba2+ = +6 and O5 = -10, which would
leave Fe + Mo with only +4 between them, i.e. Mo(II). Mo(II) is not found in
oxides. The cation ratio (3 A : 2 B) also doesn't fit the A2BB'O6
double-perovskite structure. No structure for it exists to compute, so the work
below uses the real neighbours: Ba2FeMoO6 and (Ba,Ca)2FeMoO6.

## 2. Spin splitting at the Fermi surface (from existing data)

`fermi_splitting.py` reads the refined band-path XML for Ba2FeMoO6
(`altermag/qe_inputs/mp-1277787/out_r/amag.xml`). That run is the compensated
altermagnetic configuration, i.e. the most favourable case for pairing, because
it is the only one with both spins at E_F.

- 8 Fermi crossings on the path. Where one spin channel crosses E_F, the
  opposite-spin bands sit 9-118 meV away (median 78 meV).
- A spin-singlet BCS state survives an exchange field h = splitting/2 only if
  h < Delta0/sqrt(2) (the Pauli/Clogston limit). That requires
  Tc >~ 4.65 K per meV of splitting: about 40 K at the nodal crossings and
  230-550 K everywhere else on the path.
- Conclusion: conventional singlet superconductivity is ruled out on most of the
  Fermi surface. What remains is the near-nodal pockets, which are too small to
  carry a bulk state.

**Caveat on that input (also matters for the altermag paper):** the run did not
converge. `sc_ref.out` hit electron_maxstep = 250 without converging. The scf
residual oscillated between 0.025 and 0.34 Ry and ended at 0.28 Ry. The
manuscript describes a "bounded ~1e-2 Ry residual", but for the refined
Ba2FeMoO6 run the residual is about 10x larger. The run also used the
constrained-magnetization penalty, so it shows a pinned state, not the ground
state.

## 3. SuperCon Tc model (composition analogy only)

The featurizer was rebuilt without pymatgen; element properties were recovered
from train_features.csv and reproduce all 68 features to 1e-7.

| formula | "Tc" score |
|---|---|
| CaBa2FeMoO5 | 23.5 K |
| Ba1.5Ca0.5FeMoO6 | 21.0 K |
| Ba2FeMoO6 | 16.4 K |
| Sr2FeMoO6 | 11.8 K |

Negative control: Sr2FeMoO6 and Ba2FeMoO6 are well-studied and are known NOT
to superconduct (they are ferrimagnetic half-metals), yet they score 12-16 K.
The nearest training compounds to CaBa2FeMoO5 are iron-pnictide oxides
(Fe2As2Ba4Sc3O7.5, LaFePO). The model has no non-superconductor class, so this
family scores as a false positive. These numbers carry no evidential weight.

## 4. Runs to do on the Mac (`./run.sh`)

All runs are unconstrained. Each composition gets an SCF (ecut 50/400 Ry,
3x3x3 k, conv 1e-6), then for magnetic states an NSCF on 6x6x6 k with
tetrahedra and dos.x:

| dir | system | state |
|---|---|---|
| bfmo_fim | Ba2FeMoO6 | ferrimagnet (Fe up, Mo down), the experimental order |
| bfmo_afm | Ba2FeMoO6 | compensated AFM (the altermagnetic configuration) |
| bfmo_nm  | Ba2FeMoO6 | nonmagnetic reference |
| bcfmo_fim | Ba1.5Ca0.5FeMoO6 (1 of 4 Ba -> Ca) | ferrimagnet |
| bcfmo_afm | Ba1.5Ca0.5FeMoO6 | compensated AFM |

`analyze.py` reports, for each state:
- energy per formula unit, relative to the lowest state of the same composition
- net and absolute moment
- spin-resolved DOS at E_F, with a verdict: half-metal (no singlet pairing
  possible) or both spins present

What would change the conclusion: the AFM or NM state becoming the ground
state under Ca doping. Expected outcome, from the literature: the ferrimagnet
wins by a large margin and is half-metallic.

Limitations: the Ca-doped cell is not relaxed (Ca is smaller than Ba, so a
vc-relax would be the next step), and the U values are carried over from the
altermag runs. Electron-phonon (DFPT) Tc is not attempted, because Allen-Dynes
is invalid for a magnetic ground state.
