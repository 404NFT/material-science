#!/usr/bin/env python3
"""Spin splitting AT the Fermi surface from an existing LSDA band-path XML,
and the BCS Tc a singlet superconductor would need to survive it (Pauli/
Clogston limit: exchange field h = splitting/2 must stay below Delta0/sqrt(2),
Delta0 = 1.764 kB Tc  ->  Tc_needed = splitting[meV] * 4.65 K/meV).

Usage: python fermi_splitting.py ../../altermag/qe_inputs/mp-1277787/out_r/amag.xml
"""
import sys
import xml.etree.ElementTree as ET
import numpy as np

HA = 27.211386
KB = 0.08617333  # meV/K


def main(path):
    bs = ET.parse(path).getroot().find(".//band_structure")
    ef = float(bs.findtext("fermi_energy")) * HA
    nup = int(bs.findtext("nbnd_up"))
    E = np.array([[float(x) for x in k.find("eigenvalues").text.split()]
                  for k in bs.findall(".//ks_energies")]) * HA
    up, dn = E[:, :nup], E[:, nup:]
    print(f"E_F = {ef:.3f} eV, {len(E)} k-points on path")
    rows = []
    for a, b, lab in ((up, dn, "up"), (dn, up, "down")):
        for j in range(a.shape[1]):
            s = np.sign(a[:, j] - ef)
            for i in np.where(np.diff(s) != 0)[0]:
                # distance of the opposite-spin bands from E_F at this crossing
                d = min(np.abs(b[i] - ef).min(), np.abs(b[i + 1] - ef).min()) * 1000
                rows.append((lab, i, j, d))
    print(f"{'spin':5s} {'k-idx':>5s} {'band':>4s} {'opp-spin offset (meV)':>22s} {'Tc needed (K)':>14s}")
    for lab, i, j, d in rows:
        print(f"{lab:5s} {i:5d} {j:4d} {d:22.1f} {d * 0.7071 / (1.764 * KB):14.0f}")
    ds = np.array([r[3] for r in rows])
    print(f"\n{len(ds)} Fermi crossings; opposite-spin offset min {ds.min():.0f}, "
          f"median {np.median(ds):.0f}, max {ds.max():.0f} meV")


if __name__ == "__main__":
    main(sys.argv[1])
