#!/usr/bin/env python3
"""Summarize the Ba2FeMoO6 / Ca-doped superconductivity-relevance runs.

For each case: convergence, total energy (meV per formula unit relative to the
lowest state of the same composition), net/absolute moment, and the
spin-resolved DOS at E_F from dos.x. A state can host conventional spin-singlet
pairing only if BOTH spin channels have weight at E_F; a half-metal (one
channel gapped) cannot.
"""
import re
from pathlib import Path

RY_MEV = 13605.693
HERE = Path(__file__).resolve().parent
CASES = [("bfmo_fim", "Ba2FeMoO6", "ferrimagnet"),
         ("bfmo_afm", "Ba2FeMoO6", "compensated AFM (altermagnetic config)"),
         ("bfmo_nm", "Ba2FeMoO6", "nonmagnetic"),
         ("bcfmo_fim", "Ba1.5Ca0.5FeMoO6", "ferrimagnet"),
         ("bcfmo_afm", "Ba1.5Ca0.5FeMoO6", "compensated AFM")]
FU = 2  # formula units per 20-atom cell


def scf_info(d):
    out = d / "scf.out"
    if not out.exists():
        return None
    t = out.read_text()
    e = re.findall(r"!\s+total energy\s+=\s+([-\d.]+)", t)
    tm = re.findall(r"total magnetization\s+=\s+([-\d.]+)", t)
    am = re.findall(r"absolute magnetization\s+=\s+([-\d.]+)", t)
    return {"conv": "convergence has been achieved" in t,
            "E": float(e[-1]) if e else None,
            "tot": float(tm[-1]) if tm else 0.0,
            "abs": float(am[-1]) if am else 0.0}


def dos_at_ef(d, name):
    f = d / f"{name}.dos"
    if not f.exists():
        return None
    lines = f.read_text().splitlines()
    ef = float(re.search(r"EFermi\s*=\s*([-\d.]+)", lines[0]).group(1))
    rows = [list(map(float, l.split())) for l in lines[1:] if l.strip()]
    # average over +-25 meV around E_F to smooth tetrahedron noise
    near = [r for r in rows if abs(r[0] - ef) <= 0.025]
    up = sum(r[1] for r in near) / len(near)
    dn = sum(r[2] for r in near) / len(near)
    return up, dn


def main():
    info = {c: scf_info(HERE / c) for c, _, _ in CASES}
    emin = {}
    for c, comp, _ in CASES:
        i = info[c]
        if i and i["conv"] and i["E"] is not None:
            emin[comp] = min(emin.get(comp, 1e9), i["E"])
    print(f"{'case':10s} {'state':40s} {'conv':5s} {'dE meV/f.u.':>12s} "
          f"{'M_tot':>6s} {'M_abs':>6s} {'N_up(EF)':>9s} {'N_dn(EF)':>9s}  pairing verdict")
    for c, comp, label in CASES:
        i = info[c]
        if i is None:
            print(f"{c:10s} {label:40s} not run"); continue
        de = ((i["E"] - emin[comp]) * RY_MEV / FU) if (i["conv"] and comp in emin) else None
        dos = dos_at_ef(HERE / c, c)
        if dos:
            up, dn = dos
            lo, hi = min(up, dn), max(up, dn)
            if hi < 0.05:
                v = "insulating at E_F"
            elif lo / hi < 0.05:
                v = "HALF-METAL: one spin gapped -> no singlet pairing"
            else:
                v = "both spins at E_F (check splitting vs gap)"
            ds = f"{up:9.2f} {dn:9.2f}"
        else:
            ds, v = f"{'-':>9s} {'-':>9s}", ("nonmagnetic reference" if "nm" in c else "no DOS")
        print(f"{c:10s} {label:40s} {str(i['conv']):5s} "
              f"{(f'{de:12.0f}' if de is not None else '           -')} "
              f"{i['tot']:6.2f} {i['abs']:6.2f} {ds}  {v}")
    print("\ndE: energy above the lowest converged state of the same composition."
          "\nN(EF): states/eV/cell per spin, averaged over +-25 meV.")


if __name__ == "__main__":
    main()
