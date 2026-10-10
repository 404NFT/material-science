#!/usr/bin/env python3
"""Summarize the hypothetical CaBa2FeMoO5 runs: relaxed cell, magnetic state energies,
moments, and spin-resolved DOS at E_F (pairing-relevance verdict)."""
import math
import re
from pathlib import Path

RY_MEV = 13605.693
HERE = Path(__file__).resolve().parent
CASES = [('fim', 'ferrimagnet (Fe up, Mo down)'), ('fm', 'ferromagnet'), ('nm', 'nonmagnetic')]


def relaxed():
    f = HERE / 'relaxed_cell.txt'
    if not f.exists():
        return None
    v = [list(map(float, l.split())) for l in f.read_text().splitlines()[1:4]]
    a, b, c = (2 * abs(v[1][0]), 2 * abs(v[0][1]), 2 * abs(v[0][2]))
    t = (HERE / 'relax.out').read_text()
    p = re.findall(r'P=\s*([-\d.]+)', t)
    return a, b, c, 'bfgs converged' in t, float(p[-1]) if p else math.nan


def scf(d):
    f = d / 'scf.out'
    if not f.exists():
        return None
    t = f.read_text()
    e = re.findall(r'!\s+total energy\s+=\s+([-\d.]+)', t)
    tm = re.findall(r'total magnetization\s+=\s+([-\d.]+)', t)
    am = re.findall(r'absolute magnetization\s+=\s+([-\d.]+)', t)
    return {'conv': 'convergence has been achieved' in t, 'E': float(e[-1]) if e else None,
            'tot': float(tm[-1]) if tm else 0.0, 'abs': float(am[-1]) if am else 0.0}


def dos(d, name):
    f = d / f'{name}.dos'
    if not f.exists():
        return None
    L = f.read_text().splitlines()
    ef = float(re.search(r'EFermi\s*=\s*([-\d.]+)', L[0]).group(1))
    near = [list(map(float, l.split())) for l in L[1:] if l.strip() and abs(float(l.split()[0]) - ef) <= 0.025]
    return sum(r[1] for r in near) / len(near), sum(r[2] for r in near) / len(near)


r = relaxed()
if r:
    print(f"relaxed conventional cell: a={r[0]:.3f} b={r[1]:.3f} c={r[2]:.3f} A  "
          f"(bfgs converged: {r[3]}, final P = {r[4]:.1f} kbar)")
    print("  reference Sr3Fe2O5 (exp): a=3.515 b=3.953 c=20.913 A\n")
info = {c: scf(HERE / c) for c, _ in CASES}
conv = [i['E'] for i in info.values() if i and i['conv'] and i['E'] is not None]
emin = min(conv) if conv else None
print(f"{'case':5s} {'state':30s} {'conv':5s} {'dE meV/f.u.':>12s} {'M_tot':>6s} {'M_abs':>6s} "
      f"{'N_up(EF)':>9s} {'N_dn(EF)':>9s}  verdict")
for c, lab in CASES:
    i = info[c]
    if i is None:
        print(f"{c:5s} {lab:30s} not run"); continue
    de = (i['E'] - emin) * RY_MEV if (i['conv'] and emin is not None) else None
    dd = dos(HERE / c, f'cbfmo5_{c}')
    if dd:
        up, dn = dd; hi, lo = max(up, dn), min(up, dn)
        v = ('insulating' if hi < 0.05 else
             'HALF-METAL (one spin gapped): no singlet pairing' if lo / hi < 0.05 else
             'metal, both spins at E_F')
        ds = f"{up:9.2f} {dn:9.2f}"
    else:
        ds, v = f"{'-':>9s} {'-':>9s}", ('reference' if c == 'nm' else 'no DOS')
    print(f"{c:5s} {lab:30s} {str(i['conv']):5s} {(f'{de:12.0f}' if de is not None else '           -')} "
          f"{i['tot']:6.2f} {i['abs']:6.2f} {ds}  {v}")
print("\n1 formula unit per cell. N(EF): states/eV/cell per spin, +-25 meV average.")
