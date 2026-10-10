#!/usr/bin/env python3
"""
Is altermagnetism symmetry-possible for the EXPERIMENTAL magnetic ordering
of Er2Fe3Si5?

Neutron diffraction (Moodenbaugh, Cox, Vining, Segre, PRB 29, 271 (1984))
finds the low-T commensurate phase -- the one coexisting with
superconductivity -- has the tetragonal a axis doubled: k = (1/2, 0, 0).
The paper's moment arrangement isn't accessible to us, so instead of testing
one guess we enumerate ALL collinear k=(1/2,0,0) orderings of the Er
sublattice (Fe carries no ordered moment in R2Fe3Si5) in the 2x1x1
supercell and run the amcheck tolerance sweep on each:

  spins on the 8 Er of the original cell = pattern sigma (any of 2^8),
  spins on their +a images             = -sigma        (k = 1/2 modulation),
  Fe, Si                               = nonmagnetic 'n'.

Global spin flip is a symmetry -> 128 distinct patterns.

Output: er_orderings.csv (pattern, verdict per tolerance, overall) + summary.
"""

import csv
import itertools
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "altermag"))

from pull_and_label import classify  # amcheck at one symprec
from pymatgen.core import Structure

TOLS = [1e-5, 1e-4, 1e-3, 1e-2]
CIF = HERE / "mp_metallic_am" / "mp-680269.cif"


def main():
    prim = Structure.from_file(str(CIF))
    print(f"primitive cell: {prim.composition.reduced_formula}, "
          f"{len(prim)} sites")

    sup = prim.copy()
    sup.make_supercell([2, 1, 1])

    # Track which supercell sites are Er and whether they sit in the first
    # (x < 0.5) or second half of the doubled cell, and pair them up:
    # pymatgen's make_supercell orders images deterministically, but pairing
    # by fractional coordinate is setting-independent.
    er_idx = [i for i, s in enumerate(sup) if s.specie.symbol == "Er"]
    if len(er_idx) % 2:
        sys.exit("odd Er count in supercell?")

    half1, half2 = [], []
    for i in er_idx:
        (half1 if sup[i].frac_coords[0] < 0.5 - 1e-6 else half2).append(i)
    if len(half1) != len(half2):
        sys.exit(f"unbalanced halves: {len(half1)} vs {len(half2)}")

    # pair each half1 Er with its +a image in half2
    pairs = []
    used = set()
    for i in half1:
        target = sup[i].frac_coords + np.array([0.5, 0, 0])
        best, bestd = None, 1e9
        for j in half2:
            if j in used:
                continue
            d = np.linalg.norm((sup[j].frac_coords - target + 0.5) % 1 - 0.5)
            if d < bestd:
                best, bestd = j, d
        if bestd > 1e-3:
            sys.exit(f"no +a image for Er site {i} (best {bestd})")
        used.add(best)
        pairs.append((i, best))

    n = len(pairs)
    print(f"{2 * n} Er sites -> {n} k=(1/2,0,0) pairs -> "
          f"{2 ** n // 2} distinct patterns")

    rows, counts = [], {}
    for bits in itertools.product([1, -1], repeat=n):
        if bits[0] == -1:          # global flip equivalence
            continue
        spins = ["n"] * len(sup)
        for (i, j), b in zip(pairs, bits):
            spins[i] = "u" if b > 0 else "d"
            spins[j] = "d" if b > 0 else "u"

        per_tol, verdicts = {}, set()
        for t in TOLS:
            try:
                is_am, _ = classify(sup, spins, t)
                per_tol[t] = "AM" if is_am else "AFM"
                verdicts.add(per_tol[t])
            except Exception as e:  # noqa: BLE001
                per_tol[t] = f"err:{type(e).__name__}"

        if not verdicts:
            overall = "ERROR"
        elif len(verdicts) > 1:
            overall = "REVIEW-FLIP"
        else:
            overall = verdicts.pop()
        counts[overall] = counts.get(overall, 0) + 1
        rows.append({"pattern": "".join("+" if b > 0 else "-" for b in bits),
                     **{f"AM@{t:g}": per_tol[t] for t in TOLS},
                     "verdict": overall})

    out = HERE / "er_orderings.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"\nwrote {out}")
    print("verdicts over all k=(1/2,0,0) collinear Er orderings:")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:12s} {v:4d}  ({100 * v / len(rows):.0f}%)")


if __name__ == "__main__":
    main()
