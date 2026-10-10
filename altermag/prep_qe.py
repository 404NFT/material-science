#!/usr/bin/env python3
"""
Generate Quantum ESPRESSO inputs to confirm altermagnetism LOCALLY (no cluster).

Targets the small/medium candidates only (default: the 4 double perovskites),
because a Mac is not an HPC node. For each candidate we:
  1. fetch structure + collinear magmoms from Materials Project,
  2. split every magnetic element into TWO QE species by moment sign
     (e.g. Fe -> Fe1 spin-up, Fe2 spin-down) so the AFM order is encoded via
     opposite starting_magnetization -- the standard QE collinear-AFM trick,
  3. write an scf.in (nspin=2) and a bands.in (line mode) per candidate.

Confirm altermagnetism: run scf -> bands, then `python analyze_qe.py`. An
altermagnet shows k-dependent up/down band splitting with ~zero net moment.

Needs MP_API_KEY in the environment, and a pseudopotential set (SSSP, see
README_qe.md). Pseudos are referenced as <Element>.upf in --pseudo-dir.

Usage:
    MP_API_KEY=... python prep_qe.py --outdir qe_inputs
"""

import argparse
import os
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

# The Mac-feasible headliners (≈20-atom cells). Add more ids if you're patient.
DEFAULT_IDS = ["mp-19266", "mp-1272506", "mp-1277787", "mp-1048863"]
#               Sr2FeWO6    Ba2FeWO6     Ba2FeMoO6    CaLaCrMoO6

# Hubbard U (eV) and correlated manifold per transition metal. Plain PBE cannot
# stably describe these correlated magnetic oxides (the SCF diverges); a Hubbard
# correction on the open-shell d electrons fixes that. Values are standard
# literature choices; tune per material for publication.
U_PARAMS = {
    "Ti": ("3d", 3.0), "V": ("3d", 3.0), "Cr": ("3d", 3.5), "Mn": ("3d", 4.0),
    "Fe": ("3d", 4.5), "Co": ("3d", 4.0), "Ni": ("3d", 5.0), "Cu": ("3d", 6.0),
    "Nb": ("4d", 2.0), "Mo": ("4d", 2.5), "Ru": ("4d", 2.0), "Zr": ("4d", 2.0),
    "W": ("5d", 2.0), "Os": ("5d", 2.0),
}


def hubbard_card(startmag, base, projection="ortho-atomic"):
    """QE HUBBARD card for the magnetic (open-shell d) species only.

    Only species that carry a moment (the split X1/X2 labels) get a U -- the
    formally-empty-d ions (e.g. W6+ d0) are left uncorrected."""
    lines = [f"HUBBARD ({projection})"]
    for tag in sorted(base):
        el = base[tag]
        if abs(startmag.get(tag, 0.0)) > 0 and el in U_PARAMS:
            manifold, u = U_PARAMS[el]
            lines.append(f"U {tag}-{manifold} {u}")
    return "\n".join(lines) + "\n" if len(lines) > 1 else ""


def species_split(structure, magmoms, threshold=0.3):
    """Map each site -> (label, start_mag). Magnetic elements split by sign."""
    scal = []
    for m in magmoms:
        a = np.atleast_1d(np.asarray(m, dtype=float))
        scal.append(float(a[np.argmax(np.abs(a))]) if a.size else 0.0)
    labels, startmag, base = [], {}, {}
    for site, mu in zip(structure, scal):
        el = site.specie.symbol
        if abs(mu) >= threshold:
            tag = f"{el}1" if mu > 0 else f"{el}2"
            startmag[tag] = +0.5 if mu > 0 else -0.5
        else:
            tag = el
            startmag.setdefault(tag, 0.0)
        labels.append(tag)
        base[tag] = el
    return labels, startmag, base


def kgrid(structure, kspacing=0.25):
    """Gamma-centered MP grid from a target k-spacing (1/Ang)."""
    recip = structure.lattice.reciprocal_lattice.abc  # 2*pi/a units
    return [max(1, int(round(b / kspacing))) for b in recip]


def write_scf(path, structure, labels, startmag, base, kpts, ecutwfc, pdir):
    sp_lines, sm_lines = [], []
    from pymatgen.core import Element
    for i, (tag, el) in enumerate(sorted(base.items()), start=1):
        sp_lines.append(f"  {tag}  {Element(el).atomic_mass:.4f}  {el}.upf")
        sm_lines.append(f"  starting_magnetization({i}) = {startmag[tag]:.2f}")
    ntyp = len(base)
    cell = structure.lattice.matrix
    txt = f"""&CONTROL
  calculation = 'scf'
  prefix = 'amag'
  outdir = './out'
  pseudo_dir = '{pdir}'
  tprnfor = .true.
/
&SYSTEM
  ibrav = 0
  nat = {len(structure)}
  ntyp = {ntyp}
  ecutwfc = {ecutwfc}
  ecutrho = {ecutwfc*8}
  occupations = 'smearing'
  smearing = 'gaussian'
  degauss = 0.01
  nspin = 2
{chr(10).join(sm_lines)}
/
&ELECTRONS
  conv_thr = 1.0d-7
  mixing_beta = 0.2
  mixing_mode = 'local-TF'
  electron_maxstep = 250
/
ATOMIC_SPECIES
{chr(10).join(sp_lines)}
CELL_PARAMETERS angstrom
""" + "\n".join(f"  {v[0]:.10f} {v[1]:.10f} {v[2]:.10f}" for v in cell) + """
ATOMIC_POSITIONS crystal
""" + "\n".join(f"  {lab}  {s.frac_coords[0]:.10f} {s.frac_coords[1]:.10f} "
                f"{s.frac_coords[2]:.10f}"
                for lab, s in zip(labels, structure)) + f"""
K_POINTS automatic
  {kpts[0]} {kpts[1]} {kpts[2]} 0 0 0
""" + hubbard_card(startmag, base)
    (path / "scf.in").write_text(txt)


def write_bands(path, structure, labels, startmag, base, ecutwfc, pdir, npts=20):
    from ase import Atoms
    a = Atoms(cell=structure.lattice.matrix,
              scaled_positions=structure.frac_coords,
              numbers=[s.specie.Z for s in structure], pbc=True)
    try:
        bp = a.cell.bandpath(npoints=max(60, npts * 6))
        kpath = bp.kpts
    except Exception:
        # Distorted cells ASE can't classify: use a generic path through the BZ.
        # For spin-splitting detection we only need k-coverage, not labels.
        corners = np.array([
            [0, 0, 0], [.5, 0, 0], [.5, .5, 0], [0, .5, 0], [0, 0, 0],
            [0, 0, .5], [.5, 0, .5], [.5, .5, .5], [0, .5, .5], [0, 0, .5],
            [0, 0, 0], [.5, .5, .5],
        ])
        segs = []
        for p, q in zip(corners[:-1], corners[1:]):
            segs.append(np.linspace(p, q, 11)[:-1])
        kpath = np.vstack(segs + [corners[-1:]])
    from pymatgen.core import Element
    sp_lines, sm_lines = [], []
    for i, (tag, el) in enumerate(sorted(base.items()), start=1):
        sp_lines.append(f"  {tag}  {Element(el).atomic_mass:.4f}  {el}.upf")
        sm_lines.append(f"  starting_magnetization({i}) = {startmag[tag]:.2f}")
    cell = structure.lattice.matrix
    head = f"""&CONTROL
  calculation = 'bands'
  prefix = 'amag'
  outdir = './out'
  pseudo_dir = '{pdir}'
/
&SYSTEM
  ibrav = 0
  nat = {len(structure)}
  ntyp = {len(base)}
  ecutwfc = {ecutwfc}
  ecutrho = {ecutwfc*8}
  occupations = 'smearing'
  smearing = 'gaussian'
  degauss = 0.01
  nspin = 2
  nbnd = {max(40, len(structure)*8)}
{chr(10).join(sm_lines)}
/
&ELECTRONS
  conv_thr = 1.0d-7
/
ATOMIC_SPECIES
{chr(10).join(sp_lines)}
CELL_PARAMETERS angstrom
""" + "\n".join(f"  {v[0]:.10f} {v[1]:.10f} {v[2]:.10f}" for v in cell) + """
ATOMIC_POSITIONS crystal
""" + "\n".join(f"  {lab}  {s.frac_coords[0]:.10f} {s.frac_coords[1]:.10f} "
                f"{s.frac_coords[2]:.10f}"
                for lab, s in zip(labels, structure))
    kp = ["K_POINTS crystal", f"  {len(kpath)}"]
    kp += [f"  {k[0]:.8f} {k[1]:.8f} {k[2]:.8f} 1.0" for k in kpath]
    (path / "bands.in").write_text(
        head + "\n" + "\n".join(kp) + "\n" + hubbard_card(startmag, base))


def main():
    ap = argparse.ArgumentParser(description="Generate local QE altermagnet inputs")
    ap.add_argument("--ids", nargs="+", default=DEFAULT_IDS)
    ap.add_argument("--outdir", default="qe_inputs")
    ap.add_argument("--pseudo-dir", default="../pseudos",
                    help="path (relative to each candidate dir) to UPF pseudos")
    ap.add_argument("--ecutwfc", type=float, default=50.0, help="Ry")
    ap.add_argument("--kspacing", type=float, default=0.30, help="1/Ang")
    args = ap.parse_args()

    key = os.environ.get("MP_API_KEY")
    if not key:
        sys.exit("Set MP_API_KEY in the environment.")

    from mp_api.client import MPRester
    with MPRester(key) as mpr:
        S = {str(d.material_id): d.structure for d in mpr.materials.summary.search(
            material_ids=args.ids, fields=["material_id", "structure"])}
        F = {str(d.material_id): d.formula_pretty for d in mpr.materials.summary.search(
            material_ids=args.ids, fields=["material_id", "formula_pretty"])}
        M = {str(d.material_id): d.magmoms for d in mpr.materials.magnetism.search(
            material_ids=args.ids, fields=["material_id", "magmoms"])}

    root = Path(args.outdir)
    root.mkdir(parents=True, exist_ok=True)
    elements = set()
    done = []
    for mid in args.ids:
        s, mm = S.get(mid), M.get(mid)
        if s is None or mm is None:
            print(f"[skip] {mid}: no data")
            continue
        labels, startmag, base = species_split(s, mm)
        elements |= set(base.values())
        d = root / mid
        d.mkdir(exist_ok=True)
        kpts = kgrid(s, args.kspacing)
        write_scf(d, s, labels, startmag, base, kpts, args.ecutwfc, args.pseudo_dir)
        write_bands(d, s, labels, startmag, base, args.ecutwfc, args.pseudo_dir)
        nmag = sum(1 for v in startmag.values() if abs(v) > 0)
        done.append((mid, F.get(mid, ""), len(s), kpts, nmag))
        print(f"[ok] {mid:12s} {F.get(mid,''):12s} {len(s)} atoms  k={kpts}  "
              f"{nmag} magnetic species")

    (root / "pseudos_needed.txt").write_text(
        "\n".join(sorted(f"{e}.upf" for e in elements)) + "\n")
    print(f"\nPrepared {len(done)} candidates in {root}/")
    print(f"Pseudopotentials needed: {sorted(elements)}")
    print("See README_qe.md for the run recipe.")


if __name__ == "__main__":
    main()
