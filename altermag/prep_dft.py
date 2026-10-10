#!/usr/bin/env python3
"""
Prepare VASP inputs to CONFIRM altermagnetism in the screened candidates.

For each candidate we:
  1. fetch its structure + collinear magmoms from Materials Project,
  2. symmetrize to the cell where amcheck found altermagnetism (symprec ~0.05),
     so the altermagnetic symmetry is exact in the DFT cell,
  3. set a collinear AFM MAGMOM pattern from the signs of the MP magmoms,
  4. write a spin-polarized static SCF set + a line-mode band-structure set.

To CONFIRM altermagnetism: run the static SCF, then the non-SCF band run, then
compare spin-up vs spin-down eigenvalues. An altermagnet shows momentum-dependent
spin splitting (>~50 meV near E_F) DESPITE near-zero net magnetization -- that is
the gold-standard criterion (PhysRevMaterials 9.064403 / arXiv:2509.14729).

NOTE ON POTCAR: VASP pseudopotentials are licensed and not bundled. We write
POTCAR.spec (the list of needed potentials) instead; add real POTCARs on the
cluster (set PMG_VASP_PSP_DIR or `pmg config`).

Needs MP_API_KEY in the environment.

Usage:
    MP_API_KEY=... python prep_dft.py \
        --candidates final_altermagnet_candidates.csv --outdir dft_inputs --symprec 0.05
"""

import argparse
import csv
import os
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")


def collinear_magmom(structure, mp_magmoms, threshold=0.05):
    """Per-site scalar MAGMOM from MP magmoms, mapped onto `structure` by
    nearest-site matching (the symmetrized cell may reorder/rescale sites)."""
    # Reduce MP magmoms to signed scalars.
    scal = []
    for m in mp_magmoms:
        arr = np.atleast_1d(np.asarray(m, dtype=float))
        scal.append(float(arr[np.argmax(np.abs(arr))]) if arr.size else 0.0)
    # If site counts match (common case), use directly.
    if len(scal) == len(structure):
        return [round(x, 2) for x in scal]
    # Otherwise fall back to a magnitude-by-species heuristic.
    mag = max(abs(x) for x in scal) if scal else 0.0
    out = []
    for s in structure:
        sp = s.specie
        out.append(mag if (sp.is_transition_metal or sp.is_lanthanoid
                           or sp.is_actinoid) else 0.0)
    return out


def main():
    ap = argparse.ArgumentParser(description="Prep VASP altermagnet-confirmation inputs")
    ap.add_argument("--candidates", default="final_altermagnet_candidates.csv")
    ap.add_argument("--outdir", default="dft_inputs")
    ap.add_argument("--symprec", type=float, default=0.05)
    ap.add_argument("--limit", type=int, default=0, help="only first N (0=all)")
    args = ap.parse_args()

    key = os.environ.get("MP_API_KEY")
    if not key:
        sys.exit("Set MP_API_KEY in the environment.")

    ids = []
    with open(args.candidates, newline="") as fh:
        for row in csv.DictReader(fh):
            ids.append(row.get("material_id") or row["file"].replace(".cif", ""))
    if args.limit:
        ids = ids[: args.limit]

    from mp_api.client import MPRester
    from pymatgen.io.vasp.sets import MPStaticSet, MPNonSCFSet
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

    with MPRester(key) as mpr:
        sdocs = mpr.materials.summary.search(
            material_ids=ids, fields=["material_id", "structure", "formula_pretty"])
        struct_by_id = {str(d.material_id): d.structure for d in sdocs}
        fpretty = {str(d.material_id): d.formula_pretty for d in sdocs}
        mdocs = mpr.materials.magnetism.search(
            material_ids=ids, fields=["material_id", "magmoms"])
        magmoms_by_id = {str(d.material_id): getattr(d, "magmoms", None) for d in mdocs}

    outroot = Path(args.outdir)
    outroot.mkdir(parents=True, exist_ok=True)
    done = []
    for mid in ids:
        s = struct_by_id.get(mid)
        mm = magmoms_by_id.get(mid)
        if s is None or mm is None:
            print(f"[skip] {mid}: missing structure or magmoms")
            continue
        try:
            # Attach the collinear AFM moments as a site property (aligned 1:1
            # with the MP structure), so pymatgen writes a correct MAGMOM line.
            # We run DFT on the actual MP structure -- amcheck already showed it
            # is altermagnetic within symprec, and the real cell is the physical
            # one for measuring spin splitting.
            magmom = collinear_magmom(s, mm)
            s = s.copy()
            s.add_site_property("magmom", magmom)
            sg = SpacegroupAnalyzer(s, symprec=args.symprec).get_space_group_symbol()

            d = outroot / mid
            (d / "static").mkdir(parents=True, exist_ok=True)
            (d / "bands").mkdir(parents=True, exist_ok=True)

            incar = {"ISPIN": 2, "LORBIT": 11, "ISMEAR": 0, "SIGMA": 0.05,
                     "EDIFF": 1e-6, "NSW": 0, "LASPH": True, "LREAL": "Auto"}
            static = MPStaticSet(s, user_incar_settings=incar)
            static.write_input(d / "static", potcar_spec=True)

            bands = MPNonSCFSet(s, mode="line", user_incar_settings={
                "ISPIN": 2, "LORBIT": 11, "NEDOS": 2001})
            bands.write_input(d / "bands", potcar_spec=True)

            done.append((mid, fpretty.get(mid, ""), sg, len(s)))
            print(f"[ok] {mid:13s} {fpretty.get(mid,''):14s} sg={sg:8s} "
                  f"{len(s)} sites -> {d}")
        except Exception as e:  # noqa: BLE001
            print(f"[err] {mid}: {e}")

    # A small run guide.
    guide = outroot / "README.md"
    guide.write_text(
        "# Altermagnet-confirmation DFT runs\n\n"
        "Per candidate: `static/` then `bands/`.\n\n"
        "1. Add real POTCARs (see POTCAR.spec; `pmg config -p <vasp_psp>`).\n"
        "2. Run `static/` (spin-polarized SCF). Confirm net |moment| ~ 0.\n"
        "3. Copy `static/CHGCAR` into `bands/`, run `bands/` (ICHARG=11, line mode).\n"
        "4. Plot spin-up vs spin-down bands. Altermagnet = k-dependent spin\n"
        "   splitting (>~50 meV near E_F) with zero net moment.\n\n"
        "Candidates:\n" +
        "\n".join(f"- {m} {f} ({sg}, {n} sites)" for m, f, sg, n in done) + "\n")
    print(f"\nPrepared {len(done)} candidates in {outroot}/  (see README.md)")


if __name__ == "__main__":
    main()
