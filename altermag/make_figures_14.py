#!/usr/bin/env python3
"""
Fig 1 (pipeline schematic) and Fig 4 (validation & novelty) for the manuscript.
Same style family as make_figures.py: small fonts, muted accents, 300 dpi PNG+PDF.
Color meanings kept consistent across all figures:
  green = experimental/MAGNDATA, red = DFT-relaxed/MP, blue = confirmed result.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path("figures"); OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 9})

INK = "#2b2b2b"; MUTED = "#6b6b6b"
GREEN = "#3f8f5f"; RED = "#c94f4f"; BLUE = "#3f6fbf"; GRAY = "#c9c9c9"


def savefig(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote figures/{name}.png/.pdf")


def box(ax, x, y, w, h, title, sub, edge, face="white", lw=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                                fc=face, ec=edge, lw=lw))
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
            fontsize=8.5, color=INK, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center",
            fontsize=7.0, color=MUTED)


def arrow(ax, x0, y0, x1, y1, label=None, ly=0.03):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                 mutation_scale=11, lw=1.1, color=INK,
                                 shrinkA=2, shrinkB=2))
    if label:
        ax.text((x0 + x1) / 2, max(y0, y1) + ly, label, ha="center",
                fontsize=6.8, color=MUTED, style="italic")


# ---------------- Fig 1: pipeline schematic ----------------
def fig1():
    fig, ax = plt.subplots(figsize=(7.4, 3.1))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    W, H, y1, y0 = 0.185, 0.26, 0.66, 0.14

    box(ax, 0.02, y1, W, H, "MAGNDATA", "929 experimental\nmagnetic structures", GREEN)
    box(ax, 0.265, y1, W, H, "amcheck labels", "262 AM / 303 AFM\n(trusted)", GREEN)
    box(ax, 0.51, y1, W, H, "Triage model", "31 crystal-only feat.\nPR-AUC 0.90", INK)

    box(ax, 0.02, y0, W, H, "Materials Project", "2,471 'AFM' cands\n(DFT-relaxed)", RED)
    box(ax, 0.455, y0, W, H, "Tol.-aware amcheck", "re-symmetrize; AM at\n0.05 AND 0.1 \u00c5", INK)
    box(ax, 0.775, y0, 0.205, H, "Two-stage DFT+U", "nodal + compensated\n+ \u226550 meV", BLUE, lw=1.8)

    arrow(ax, 0.205, y1 + H / 2, 0.265, y1 + H / 2)
    arrow(ax, 0.45, y1 + H / 2, 0.51, y1 + H / 2)
    arrow(ax, 0.205, y0 + H / 2, 0.455, y0 + H / 2, label="score P(AM)")
    arrow(ax, 0.60, y1, 0.55, y0 + H + 0.01)
    ax.add_patch(FancyArrowPatch((0.64, y0 + H / 2), (0.775, y0 + H / 2),
                                 arrowstyle="-|>", mutation_scale=11, lw=1.1,
                                 color=INK, shrinkA=2, shrinkB=2))
    ax.text(0.707, y0 + H / 2 - 0.075, "12 robust", ha="center", fontsize=6.8,
            color=MUTED, style="italic")

    ax.text(0.8775, y1 + H * 0.5, "6 new altermagnets\n+ control\n(5 rejected)",
            ha="center", va="center", fontsize=7.8, color=BLUE, fontweight="bold")
    ax.add_patch(FancyArrowPatch((0.8775, y0 + H), (0.8775, y1 + H * 0.22),
                                 arrowstyle="-|>", mutation_scale=11, lw=1.1,
                                 color=BLUE, shrinkA=2, shrinkB=4))
    ax.text(0.02, 0.985, "trusted labels in", fontsize=7, color=GREEN,
            style="italic", va="top")
    ax.text(0.02, 0.045, "distorted geometry in \u2014 re-symmetrized before judging",
            fontsize=7, color=RED, style="italic")
    savefig(fig, "fig1_pipeline")


# ---------------- Fig 4: validation & novelty ----------------
def fig4():
    ours = [
        ("Ba₂CoSi₂O₇", "exact structure match", 2),
        ("CaLaCrMoO₆", "our control; compound match", 2),
        ("LiFeF₄", "polymorph match", 2),
        ("Y₂Mo₂O₇", "405 meV", 0),
        ("SrLaCoO₄", "281 meV", 0),
        ("Ba₂FeMoO₆", "275 meV", 0),
        ("MgCu₂(O₂F)₂", "254 meV", 0),
        ("Sr₂FeWO₆", "116 meV", 0),
        ("VOF₂", "85 meV", 0),
    ]
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    ax.set_xlim(0, 1); ax.set_ylim(-0.5, len(ours) + 1.8); ax.axis("off")

    cols = {"this work": 0.50, "Gao et al.\n(GNN+DFT)": 0.68,
            "MAGNDATA screen\n(PRM 2025)": 0.87}
    for name, x in cols.items():
        ax.text(x, len(ours) + 0.35, name, ha="center", fontsize=7.6,
                color=INK, fontweight="bold")

    for i, (name, note, status) in enumerate(ours):
        y = len(ours) - 1 - i
        ax.text(0.01, y, name, fontsize=8.2, color=INK, va="center")
        ax.text(0.21, y, note, fontsize=6.8, color=MUTED, va="center")
        ax.scatter([cols["this work"]], [y], s=52, color=BLUE, zorder=3)
        in_gao = status == 2
        ax.scatter([cols["Gao et al.\n(GNN+DFT)"]], [y], s=52, zorder=3,
                   color=GRAY if not in_gao else GREEN,
                   marker="o" if in_gao else "x", linewidths=1.6)
        ax.scatter([cols["MAGNDATA screen\n(PRM 2025)"]], [y], s=52, zorder=3,
                   color=GRAY, marker="x", linewidths=1.6)

    # separator between validation block and novel block
    ysep = len(ours) - 3.5
    ax.axhline(ysep, xmin=0.0, xmax=0.95, color=GRAY, lw=0.8, ls="--")
    ax.text(0.985, ysep + 1.6, "validation\n(independent agreement)", rotation=90,
            fontsize=6.6, color=GREEN, ha="center", va="center")
    ax.text(0.985, ysep - 3.0, "novel\n(this work only)", rotation=90,
            fontsize=6.6, color=BLUE, ha="center", va="center")

    ax.scatter([], [], s=52, color=BLUE, label="confirmed here")
    ax.scatter([], [], s=52, color=GREEN, label="confirmed by prior study")
    ax.scatter([], [], s=52, color=GRAY, marker="x", linewidths=1.6,
               label="absent from study")
    ax.legend(fontsize=6.8, loc="lower left", frameon=False,
              bbox_to_anchor=(0.0, -0.09), ncol=3)
    ax.set_title("Validation and novelty of the confirmed set", fontsize=9, pad=14)
    savefig(fig, "fig4_novelty")


if __name__ == "__main__":
    fig1(); fig4()
    print("done")
