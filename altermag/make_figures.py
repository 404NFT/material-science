#!/usr/bin/env python3
"""
Generate manuscript figures from data already on disk.

  Fig 2 — label provenance (ROC-AUC bars: MP-CV, MP->MAGNDATA, MAGNDATA-CV)
  Fig 3 — tolerance blind spot (crystal-system distributions at 1e-3 vs 0.1 A)
  Fig 5 — DFT confirmation (nodal splitting profiles VOF2/Y2Mo2O7 + summary bars)

Outputs PNG (300 dpi) + PDF into ./figures/.
"""

import glob
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HA = 27.211386
OUT = Path("figures"); OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False})

CS_NAMES = ["triclinic", "monoclinic", "orthorhombic", "tetragonal",
            "trigonal", "hexagonal", "cubic"]


def savefig(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote figures/{name}.png/.pdf")


# ---------------- Fig 2: label provenance ----------------
def fig2():
    labels = ["MP-trained\n(MP 5-fold CV)", "MP-trained\n→ MAGNDATA",
              "MAGNDATA-trained\n(5-fold CV)"]
    roc = [0.848, 0.537, 0.908]
    fig, ax = plt.subplots(figsize=(4.4, 2.7))
    bars = ax.bar(labels, roc, color=["#7f9cc4", "#c94f4f", "#3f8f5f"], width=0.55)
    ax.axhline(0.5, ls="--", c="gray", lw=0.8)
    ax.text(1.02, 0.505, "chance", transform=ax.get_yaxis_transform(),
            fontsize=7, color="gray")
    for b, v in zip(bars, roc):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.015, f"{v:.2f}",
                ha="center", fontsize=8)
    ax.tick_params(axis="x", labelsize=7.5)
    ax.set_ylabel("ROC-AUC (AM vs AFM)")
    ax.set_ylim(0.4, 1.0)
    ax.set_title("Label provenance decides transferability", fontsize=9)
    savefig(fig, "fig2_provenance")


# ---------------- Fig 3: tolerance blind spot ----------------
def crystal_dist(csv):
    df = pd.read_csv(csv)
    cs = df["crystal_system"].astype(int).clip(0, 6)
    return np.bincount(cs, minlength=7) / len(cs) * 100


def fig3():
    d = {
        ("MP (DFT-relaxed)", "1e-3"): crystal_dist("mp_features.csv"),
        ("MP (DFT-relaxed)", "0.1"): crystal_dist("mp_features_s01.csv"),
        ("MAGNDATA (experimental)", "1e-3"): crystal_dist("mcif_features.csv"),
        ("MAGNDATA (experimental)", "0.1"): crystal_dist("mcif_features_s01.csv"),
    }
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), sharey=True)
    x = np.arange(7)
    for ax, tol, title in zip(
            axes, ["1e-3", "0.1"],
            ["(a) symprec = 10⁻³ Å (conventional)", "(b) symprec = 0.1 Å (this work)"]):
        ax.bar(x - 0.2, d[("MP (DFT-relaxed)", tol)], width=0.4,
               label="Materials Project (DFT-relaxed)", color="#c94f4f")
        ax.bar(x + 0.2, d[("MAGNDATA (experimental)", tol)], width=0.4,
               label="MAGNDATA (experimental)", color="#3f8f5f")
        ax.set_xticks(x); ax.set_xticklabels(CS_NAMES, rotation=40, ha="right")
        ax.set_title(title, fontsize=9)
    axes[0].set_ylabel("fraction of structures (%)")
    axes[0].annotate("63% false-triclinic\nfrom relaxation\ndistortion",
                     xy=(0.25, 60), xytext=(1.6, 45), fontsize=7.5,
                     arrowprops=dict(arrowstyle="->", lw=0.8))
    axes[1].legend(fontsize=7.5, loc="upper right")
    savefig(fig, "fig3_blindspot")


# ---------------- Fig 5: DFT confirmation ----------------
def perk_split(mid, window=3.0):
    xml = glob.glob(f"qe_inputs/{mid}/out*/*.save/data-file-schema.xml")[0]
    bs = ET.parse(xml).getroot().find(".//band_structure")
    ef = float(bs.findtext("fermi_energy")) * HA
    nup = int(bs.findtext("nbnd_up"))
    up, dn = [], []
    for k in bs.findall(".//ks_energies"):
        e = np.array([float(x) for x in k.find("eigenvalues").text.split()]) * HA
        up.append(e[:nup]); dn.append(e[nup:])
    up, dn = np.array(up), np.array(dn)
    diff = np.abs(up - dn)
    inwin = (np.abs(up - ef) <= window) | (np.abs(dn - ef) <= window)
    return np.where(inwin, diff, 0.0).max(axis=1) * 1000  # meV per k-point


def fig5():
    fig = plt.figure(figsize=(7.0, 4.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.15], hspace=0.55, wspace=0.25)

    for i, (mid, name) in enumerate([("mp-759163", "VOF$_2$"),
                                     ("mp-2674749", "Y$_2$Mo$_2$O$_7$")]):
        ax = fig.add_subplot(gs[0, i])
        s = perk_split(mid)
        ax.plot(s, lw=1.2, color="#8f3f9f")
        ax.fill_between(range(len(s)), s, alpha=0.25, color="#8f3f9f")
        ax.axhline(50, ls="--", lw=0.8, c="gray")
        ax.text(len(s) * 0.99, 54, "50 meV", ha="right", fontsize=7, color="gray")
        ax.set_title(f"({'ab'[i]}) {name}: nodal spin splitting", fontsize=9)
        ax.set_xlabel("k-point index along band path")
        if i == 0:
            ax.set_ylabel("max |E↑−E↓| near $E_F$ (meV)")
        ax.set_ylim(0, None)

    # (c) summary bars for the ten confirmed
    res = pd.read_csv("qe_results.csv")
    names = {"mp-1277787": "Ba₂FeMoO₆", "mp-2674749": "Y₂Mo₂O₇",
             "mp-1274449": "SrLaCoO₄", "mp-2240166": "MgCu₂(O₂F)₂",
             "mp-1580697": "Ca₃Co₂O₇", "mp-1272506": "Ba₂FeWO₆",
             "mp-1048863": "CaLaCrMoO₆*", "mp-19266": "Sr₂FeWO₆",
             "mp-756665": "ZrCoO₃", "mp-759163": "VOF₂"}
    conf = res[res.verdict == "ALTERMAGNET"].copy()
    conf["name"] = conf["candidate"].map(names)
    conf = conf.sort_values("max_split_meV", ascending=True)
    ax = fig.add_subplot(gs[1, :])
    y = np.arange(len(conf))
    ax.barh(y, conf["max_split_meV"], height=0.62, color="#3f6fbf",
            label="max per-k splitting")
    ax.barh(y, conf["min_perk_meV"], height=0.62, color="#c9c9c9",
            label="min per-k splitting")
    ax.axvline(50, ls="--", lw=0.8, c="gray")
    ax.set_yticks(y); ax.set_yticklabels(conf["name"], fontsize=8)
    ax.set_xlabel("spin splitting near $E_F$ (meV)")
    ax.set_title("(c) Ten DFT-confirmed altermagnets "
                 "(* = positive control, Gao et al.)", fontsize=9)
    ax.legend(fontsize=7.5, loc="lower right")
    savefig(fig, "fig5_dft")


if __name__ == "__main__":
    fig2(); fig3(); fig5()
    print("done")
