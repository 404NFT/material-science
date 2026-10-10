#!/usr/bin/env python3
"""
Altermagnet spin-splitting analysis from QE's saved XML (robust).

QE suppresses eigenvalue text output for >100 k-points, so we read the
band-path eigenvalues straight from <candidate>/out/amag.save/data-file-schema.xml
(written by the `bands` run). For each candidate we compute the maximum and
per-k spin splitting near E_F and the net moment, and classify:

  ALTERMAGNET := net |moment| ~ 0  AND  k-DEPENDENT splitting >= threshold near E_F

Usage:
    python analyze_qe_xml.py qe_inputs [--threshold 0.05] [--window 3.0]
"""

import argparse
import glob
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

HA = 27.211386  # eV per Hartree


def net_moment(cand_dir):
    """Net moment from the newest SCF output (sc.out = constrained run wins)."""
    outs = [p for p in (cand_dir / "sc_ref.out", cand_dir / "sc.out",
                        cand_dir / "scf.out") if p.exists()]
    if not outs:
        return None
    newest = max(outs, key=lambda p: p.stat().st_mtime)
    val = None
    for line in newest.read_text().splitlines():
        m = re.search(r"total magnetization\s*=\s*([-\d.]+)", line)
        if m:
            val = float(m.group(1))
    return val


def splitting_from_xml(xml_path, window):
    bs = ET.parse(xml_path).getroot().find(".//band_structure")
    if bs.findtext("lsda") != "true":
        return None
    ef = float(bs.findtext("fermi_energy")) * HA
    nup = int(bs.findtext("nbnd_up"))
    up, dn = [], []
    for k in bs.findall(".//ks_energies"):
        e = np.array([float(x) for x in k.find("eigenvalues").text.split()]) * HA
        up.append(e[:nup]); dn.append(e[nup:])
    up, dn = np.array(up), np.array(dn)
    diff = np.abs(up - dn)
    inwin = (np.abs(up - ef) <= window) | (np.abs(dn - ef) <= window)
    dwin = np.where(inwin, diff, 0.0)
    per_k = dwin.max(axis=1)
    return {
        "ef": ef, "nk": len(up),
        "max_meV": dwin.max() * 1000,
        "mean_meV": per_k.mean() * 1000,
        "min_perk_meV": per_k.min() * 1000,
        "max_perk_meV": per_k.max() * 1000,
        "frac_split": (per_k > 0.026).mean(),
    }


def main():
    ap = argparse.ArgumentParser(description="QE XML altermagnet analysis")
    ap.add_argument("indir", nargs="?", default="qe_inputs")
    ap.add_argument("--threshold", type=float, default=0.05, help="eV")
    ap.add_argument("--moment-tol", type=float, default=0.5, help="Bohr mag/cell")
    ap.add_argument("--window", type=float, default=3.0, help="eV around E_F")
    ap.add_argument("--out", default="qe_results.csv")
    args = ap.parse_args()

    root = Path(args.indir)
    cands = sorted(p for p in root.iterdir()
                   if p.is_dir() and p.name.startswith("mp-"))
    rows = []
    print(f"{'candidate':12s} {'net_mom':>8s} {'max(meV)':>9s} "
          f"{'per-k range':>14s} {'%k':>5s}  verdict")
    for c in cands:
        nm = net_moment(c)
        xmls = sorted(glob.glob(str(c / "out*" / "*.save" / "data-file-schema.xml")),
                      key=lambda p: Path(p).stat().st_mtime, reverse=True)
        if not xmls:
            print(f"{c.name:12s} {'-':>8s} {'-':>9s} {'-':>14s} {'-':>5s}  INCOMPLETE (no XML)")
            rows.append((c.name, nm, None, None, None, None, "INCOMPLETE"))
            continue
        try:
            s = splitting_from_xml(xmls[0], args.window)
        except Exception as e:  # noqa: BLE001
            print(f"{c.name:12s} {'?':>8s} {'-':>9s} {'-':>14s} {'-':>5s}  ERROR ({e})")
            rows.append((c.name, nm, None, None, None, None, "ERROR"))
            continue
        if s is None:
            print(f"{c.name:12s} {'-':>8s} {'-':>9s} {'-':>14s} {'-':>5s}  not spin-polarized")
            rows.append((c.name, nm, None, None, None, None, "NOT-LSDA"))
            continue
        comp = nm is not None and abs(nm) <= args.moment_tol
        # Altermagnetic symmetry REQUIRES nodal directions: the splitting must
        # (nearly) vanish somewhere on the path. A large but k-uniform splitting
        # at zero net moment is a compensated-ferrimagnet signature instead.
        nodal = s["min_perk_meV"] < 0.5 * s["max_perk_meV"]
        if s["max_meV"] >= args.threshold * 1000 and comp and nodal:
            v = "ALTERMAGNET"
        elif s["max_meV"] >= args.threshold * 1000 and not comp:
            v = "SPLIT-but-FM?"
        elif s["max_meV"] >= args.threshold * 1000 and not nodal:
            v = "no-nodes (comp-FiM?)"
        else:
            v = "no-splitting"
        nm_s = f"{nm:+.2f}" if nm is not None else "?"
        print(f"{c.name:12s} {nm_s:>8s} {s['max_meV']:9.0f} "
              f"{s['min_perk_meV']:5.0f}-{s['max_perk_meV']:<5.0f}"
              f" {s['frac_split']*100:4.0f}%  {v}")
        rows.append((c.name, nm, s["max_meV"], s["min_perk_meV"],
                     s["max_perk_meV"], s["frac_split"], v))

    import csv
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["candidate", "net_moment", "max_split_meV", "min_perk_meV",
                    "max_perk_meV", "frac_k_split", "verdict"])
        w.writerows(rows)
    n = sum(1 for r in rows if r[6] == "ALTERMAGNET")
    print(f"\n{n} confirmed altermagnet(s). Wrote {args.out}")


if __name__ == "__main__":
    main()
