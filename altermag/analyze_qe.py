#!/usr/bin/env python3
"""
Detect altermagnetic spin splitting from finished local QE band runs.

Reads each candidate's bands.out, extracts spin-up and spin-down eigenvalues at
every k-point, and reports the maximum |E_up - E_down| within a window around the
Fermi level. Altermagnet := compensated (net moment ~0, from scf.out) AND
sizeable k-dependent up/down splitting (gold-standard ~50 meV near E_F).

Usage:
    python analyze_qe.py qe_inputs [--threshold 0.05] [--window 3.0]
"""

import argparse
import re
import sys
from pathlib import Path

import numpy as np


def net_moment(scf_out):
    """Last 'total magnetization' (Bohr mag/cell) from scf.out, or None."""
    if not scf_out.exists():
        return None
    val = None
    for line in scf_out.read_text().splitlines():
        m = re.search(r"total magnetization\s*=\s*([-\d.]+)", line)
        if m:
            val = float(m.group(1))
    return val


def fermi(out):
    txt = out.read_text() if out.exists() else ""
    m = re.findall(r"Fermi energy is\s*([-\d.]+)\s*ev", txt)
    if m:
        return float(m[-1])
    m = re.findall(r"highest occupied.*?([-\d.]+)\s*$", txt, re.M)
    return float(m[-1]) if m else None


def parse_bands(bands_out):
    """Return (up, dn) arrays shaped (n_kpts, n_bands) for the two spins.

    QE prints two blocks: 'SPIN UP' then 'SPIN DOWN', each a series of k-point
    headers followed by eigenvalue rows."""
    txt = bands_out.read_text()
    # split into spin sections
    iup = txt.find("SPIN UP")
    idn = txt.find("SPIN DOWN")
    if iup == -1 or idn == -1:
        raise ValueError("no SPIN UP/DOWN blocks (band run incomplete?)")

    def eigs(block):
        ks = re.split(r"\n\s*k\s*=", block)[1:]
        out = []
        for kchunk in ks:
            nums = re.findall(r"[-+]?\d+\.\d+", kchunk.split("\n", 1)[-1])
            # the k header line itself has 3 coords; drop them via the split above
            vals = [float(x) for x in nums]
            if vals:
                out.append(vals)
        # keep only k-points with the modal band count
        if not out:
            return np.zeros((0, 0))
        nb = max(set(len(r) for r in out), key=[len(r) for r in out].count)
        out = [r for r in out if len(r) == nb]
        return np.array(out)

    up = eigs(txt[iup:idn])
    dn = eigs(txt[idn:])
    n = min(len(up), len(dn))
    return up[:n], dn[:n]


def main():
    ap = argparse.ArgumentParser(description="QE altermagnet spin-splitting analysis")
    ap.add_argument("indir", nargs="?", default="qe_inputs")
    ap.add_argument("--threshold", type=float, default=0.05, help="eV")
    ap.add_argument("--moment-tol", type=float, default=0.5, help="Bohr mag/cell")
    ap.add_argument("--window", type=float, default=3.0, help="eV around E_F")
    ap.add_argument("--out", default="qe_results.csv")
    args = ap.parse_args()

    root = Path(args.indir)
    cands = sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("mp-"))
    if not cands:
        sys.exit(f"No mp-* dirs in {root}")

    rows = []
    print(f"{'candidate':12s} {'net_mom':>8s} {'max_split(eV)':>13s} "
          f"{'%k>26meV':>9s}  verdict")
    for c in cands:
        nm = net_moment(c / "scf.out")
        try:
            ef = fermi(c / "bands.out") or fermi(c / "scf.out")
            up, dn = parse_bands(c / "bands.out")
            if up.size == 0:
                raise ValueError("empty bands")
            nb = min(up.shape[1], dn.shape[1])
            diff = np.abs(up[:, :nb] - dn[:, :nb])
            if ef is not None:
                inwin = (np.abs(up[:, :nb] - ef) <= args.window) | \
                        (np.abs(dn[:, :nb] - ef) <= args.window)
                diff = np.where(inwin, diff, 0.0)
            ms = float(diff.max())
            frac = float((diff.max(axis=1) > 0.026).mean())
        except Exception as e:  # noqa: BLE001
            print(f"{c.name:12s} {'-':>8s} {'-':>13s} {'-':>9s}  INCOMPLETE ({e})")
            rows.append((c.name, nm, None, None, "INCOMPLETE"))
            continue
        comp = nm is not None and abs(nm) <= args.moment_tol
        if ms >= args.threshold and comp:
            v = "ALTERMAGNET"
        elif ms >= args.threshold:
            v = "SPLIT-but-FM?"
        else:
            v = "no-splitting (AFM)"
        nm_s = f"{nm:+.3f}" if nm is not None else "?"
        print(f"{c.name:12s} {nm_s:>8s} {ms:13.4f} {frac*100:8.1f}%  {v}")
        rows.append((c.name, nm, ms, frac, v))

    import csv
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["candidate", "net_moment", "max_split_eV", "frac_k>26meV", "verdict"])
        w.writerows(rows)
    n = sum(1 for r in rows if r[4] == "ALTERMAGNET")
    print(f"\n{n} confirmed altermagnet(s). Wrote {args.out}")


if __name__ == "__main__":
    main()
