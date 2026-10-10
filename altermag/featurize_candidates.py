#!/usr/bin/env python3
"""
Featurizer for the altermagnet ML-triage layer.

Turns a set of labeled structures (from Stage 1: stage1_results.csv + the mcif
folder) into a feature matrix for training a classifier that predicts
altermagnet-likelihood FROM CRYSTAL STRUCTURE ALONE.

THE LEAKAGE RULE (read this):
    Every feature here is computable from composition + non-magnetic geometry
    only -- the exact information you'd have for an UNLABELED candidate whose
    magnetic structure you don't know. We deliberately use NOTHING derived from
    the magnetic moments (no net moment, no up/down counts, no magnetic space
    group). Those would leak the label and make the model useless on real
    candidates. The label comes solely from Stage 1's `verdict` column.

What this produces:
    features.csv -- one row per AM/AFM structure: <feature columns>, label
    label = 1 for AM, 0 for AFM.

Dependencies:
    pip install pymatgen numpy        (no matminer needed -- see note below)

Usage:
    python featurize_candidates.py \
        --indir ./mcif --labels stage1_results.csv --out features.csv

NOTE ON FEATURES:
    This uses a compact, hand-rolled composition descriptor (weighted element
    property statistics) so it runs with zero new installs. For a real run,
    swap in matminer's Magpie featurizer (~130 well-tested features):
        from matminer.featurizers.composition import ElementProperty
        ep = ElementProperty.from_preset("magpie")
    It's strictly better; this lean version just gets you moving today.
"""

import argparse
import csv
import sys
import traceback
from pathlib import Path

import numpy as np
from pymatgen.core import Element
from pymatgen.io.cif import CifParser
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

# Element properties we aggregate across the composition. All are crystal-only
# (intrinsic atomic properties), so none of this leaks the magnetic label.
_ELEMENT_PROPS = ("Z", "X", "row", "group", "atomic_mass", "atomic_radius")

_CRYSTAL_SYSTEMS = {
    "triclinic": 0, "monoclinic": 1, "orthorhombic": 2, "tetragonal": 3,
    "trigonal": 4, "hexagonal": 5, "cubic": 6,
}


def _element_value(el, prop):
    """Pull one intrinsic property from a pymatgen Element, NaN if undefined."""
    try:
        if prop == "X":
            v = el.X                       # electronegativity (NaN for some)
        elif prop == "atomic_radius":
            v = el.atomic_radius           # may be None
        elif prop == "atomic_mass":
            v = el.atomic_mass
        else:
            v = getattr(el, prop)          # Z, row, group
        return float(v) if v is not None else np.nan
    except Exception:  # noqa: BLE001
        return np.nan


def composition_features(comp):
    """Composition-weighted statistics over element properties.

    For each property we emit: weighted mean, min, max, and range across the
    distinct elements. Crystal-only; computable for any formula."""
    elements = list(comp.elements)
    fracs = np.array([comp.get_atomic_fraction(e) for e in elements])
    feats = {}
    for prop in _ELEMENT_PROPS:
        vals = np.array([_element_value(e, prop) for e in elements])
        mask = ~np.isnan(vals)
        if mask.sum() == 0:
            wmean = vmin = vmax = vrng = np.nan
        else:
            w = fracs[mask]
            w = w / w.sum()
            wmean = float(np.dot(w, vals[mask]))
            vmin = float(vals[mask].min())
            vmax = float(vals[mask].max())
            vrng = vmax - vmin
        feats[f"{prop}_wmean"] = wmean
        feats[f"{prop}_min"] = vmin
        feats[f"{prop}_max"] = vmax
        feats[f"{prop}_range"] = vrng
    return feats


def structure_features(struct, symprec=1e-3):
    """Non-magnetic symmetry/geometry features. SpacegroupAnalyzer uses only
    species + positions (it ignores magmom), so this is the crystallographic
    symmetry -- exactly what's available for an unlabeled candidate.

    symprec matters a lot for DFT-relaxed structures (e.g. Materials Project):
    at 1e-3 tiny relaxation distortions read as triclinic, which mismatches the
    clean symmetry of experimental training structures. Use a looser symprec
    (~0.1) so both sets land on comparable space groups."""
    sga = SpacegroupAnalyzer(struct, symprec=symprec)
    n_mag = sum(
        1 for s in struct
        if (s.specie.is_transition_metal
            or s.specie.is_lanthanoid
            or s.specie.is_actinoid)
    )
    return {
        "spacegroup_number": sga.get_space_group_number(),
        "crystal_system": _CRYSTAL_SYSTEMS.get(sga.get_crystal_system(), -1),
        "n_sites": len(struct),
        "n_elements": len(struct.composition.elements),
        "n_magnetic_sites": n_mag,
        "density": float(struct.density),
        "volume_per_atom": float(struct.volume / len(struct)),
    }


def featurize_one(path, symprec=1e-3):
    """Return a flat feature dict for one structure file (no label)."""
    parser = CifParser(str(path))
    structures = parser.parse_structures(primitive=False)
    if not structures:
        raise ValueError("no structure parsed")
    struct = structures[0]
    feats = {}
    feats.update(composition_features(struct.composition))
    feats.update(structure_features(struct, symprec=symprec))
    return feats


def load_labels(labels_csv):
    """Map filename -> binary label, keeping only clean AM/AFM verdicts."""
    out = {}
    with open(labels_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            v = row.get("verdict", "")
            if v == "AM":
                out[row["file"]] = 1
            elif v == "AFM":
                out[row["file"]] = 0
            # REVIEW-FLIP / SKIP-FM / ERROR are intentionally dropped:
            # ambiguous or non-applicable labels would only add noise.
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Crystal-only featurizer for the altermagnet ML-triage layer"
    )
    ap.add_argument("--indir", required=True, help="directory of .mcif/.cif files")
    ap.add_argument("--labels", required=True, help="stage1_results.csv from Stage 1")
    ap.add_argument("--out", default="features.csv", help="output feature CSV")
    ap.add_argument("--symprec", type=float, default=1e-3,
                    help="symmetry tolerance; use ~0.1 for DFT-relaxed structures")
    args = ap.parse_args()

    labels = load_labels(args.labels)
    if not labels:
        sys.exit("No AM/AFM rows found in labels file -- nothing to featurize.")

    indir = Path(args.indir)
    rows, fieldnames = [], None
    n_ok = n_fail = 0
    for fname, label in labels.items():
        path = indir / fname
        if not path.exists():
            sys.stderr.write(f"[skip] {fname}: file not found in {indir}\n")
            continue
        try:
            feats = featurize_one(path, symprec=args.symprec)
            feats["file"] = fname
            feats["label"] = label
            if fieldnames is None:
                # file + features + label, with label last for readability
                feat_keys = [k for k in feats if k not in ("file", "label")]
                fieldnames = ["file"] + feat_keys + ["label"]
            rows.append(feats)
            n_ok += 1
        except Exception as e:  # noqa: BLE001
            n_fail += 1
            sys.stderr.write(f"[fail] {fname}: {e}\n")
            sys.stderr.write(traceback.format_exc())

    if not rows:
        sys.exit("No structures featurized successfully.")

    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})

    n_am = sum(r["label"] for r in rows)
    print(f"Featurized {n_ok} structures ({n_fail} failed).")
    print(f"  AM (label=1): {n_am}    AFM (label=0): {n_ok - n_am}")
    print(f"  {len(fieldnames) - 2} features per structure.")
    print(f"Wrote {args.out}.")
    if n_ok < 50:
        print(
            "\nNOTE: this is far too few rows to train on -- it just proves the\n"
            "featurizer works. Grow the labeled set (Materials Project API) to a\n"
            "few hundred before training."
        )


if __name__ == "__main__":
    main()
