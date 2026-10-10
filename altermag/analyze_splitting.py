#!/usr/bin/env python3
"""
Quantify altermagnetic spin splitting from finished VASP band runs.

For each candidate under dft_inputs/<id>/bands, this reads the spin-resolved
eigenvalues and computes the maximum |E_up(k,n) - E_down(k,n)| over all bands
within an energy window around E_F. An ALTERMAGNET shows a sizeable, momentum-
dependent up/down splitting (the gold-standard threshold is ~50 meV near E_F)
DESPITE zero net magnetization -- so we also report the net moment from the
static run as a compensation check.

  altermagnet  := net |moment| ~ 0  AND  max spin splitting >= --threshold
  (a conventional AFM shows ~0 splitting; a ferromagnet has net moment != 0)

Usage:
    python analyze_splitting.py dft_inputs [--threshold 0.05] [--window 3.0]
"""

import argparse
import sys
from pathlib import Path

import numpy as np


def net_moment(static_dir):
    """Total magnetization (mu_B) from the static OUTCAR, or None."""
    try:
        from pymatgen.io.vasp.outputs import Outcar
        oc = Outcar(str(static_dir / "OUTCAR"))
        if oc.total_mag is not None:
            return float(oc.total_mag)
    except Exception:
        pass
    return None


def max_spin_splitting(bands_dir, window):
    """Return (max_split_eV, frac_of_kpts_split>26meV, efermi) from vasprun."""
    from pymatgen.io.vasp.outputs import Vasprun
    from pymatgen.electronic_structure.core import Spin
    vr = Vasprun(str(bands_dir / "vasprun.xml"), parse_potcar_file=False)
    bs = vr.get_band_structure(line_mode=True)
    if not bs.is_spin_polarized:
        return 0.0, 0.0, bs.efermi
    ef = bs.efermi
    up = bs.bands[Spin.up]      # shape (n_bands, n_kpts)
    dn = bs.bands[Spin.down]
    # Only compare bands with any eigenvalue inside [ef-window, ef+window].
    in_win = (np.abs(up - ef) <= window) | (np.abs(dn - ef) <= window)
    diff = np.abs(up - dn)
    diff_win = np.where(in_win, diff, 0.0)
    max_split = float(diff_win.max()) if diff_win.size else 0.0
    # fraction of k-points where some in-window band splits > 26 meV (k_B*T@300K)
    per_k = diff_win.max(axis=0) if diff_win.size else np.array([0.0])
    frac = float((per_k > 0.026).mean())
    return max_split, frac, ef


def main():
    ap = argparse.ArgumentParser(description="Detect altermagnetic spin splitting")
    ap.add_argument("indir", nargs="?", default="dft_inputs")
    ap.add_argument("--threshold", type=float, default=0.05,
                    help="min max-splitting (eV) to call altermagnet [0.05]")
    ap.add_argument("--moment-tol", type=float, default=0.5,
                    help="max net |moment| (mu_B) to count as compensated")
    ap.add_argument("--window", type=float, default=3.0,
                    help="energy window +/- E_F (eV) to inspect")
    ap.add_argument("--out", default="dft_results.csv")
    args = ap.parse_args()

    root = Path(args.indir)
    cands = sorted(p for p in root.iterdir() if p.is_dir())
    if not cands:
        sys.exit(f"No candidate dirs in {root}")

    rows = []
    print(f"{'candidate':14s} {'net_moment':>10s} {'max_split(eV)':>13s} "
          f"{'%k split':>9s}  verdict")
    for c in cands:
        sdir, bdir = c / "static", c / "bands"
        nm = net_moment(sdir)
        try:
            ms, frac, ef = max_spin_splitting(bdir, args.window)
        except Exception as e:  # noqa: BLE001
            print(f"{c.name:14s} {'-':>10s} {'-':>13s} {'-':>9s}  INCOMPLETE ({e})")
            rows.append((c.name, nm, None, None, "INCOMPLETE"))
            continue
        compensated = (nm is not None and abs(nm) <= args.moment_tol)
        if ms >= args.threshold and compensated:
            verdict = "ALTERMAGNET"
        elif ms >= args.threshold and not compensated:
            verdict = "SPLIT-but-FM?"
        else:
            verdict = "no-splitting (AFM)"
        nm_s = f"{nm:+.3f}" if nm is not None else "?"
        print(f"{c.name:14s} {nm_s:>10s} {ms:13.4f} {frac*100:8.1f}%  {verdict}")
        rows.append((c.name, nm, ms, frac, verdict))

    import csv
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["candidate", "net_moment", "max_split_eV", "frac_k_split",
                    "verdict"])
        w.writerows(rows)
    n_am = sum(1 for r in rows if r[4] == "ALTERMAGNET")
    print(f"\n{n_am} confirmed altermagnet(s). Wrote {args.out}")


if __name__ == "__main__":
    main()
