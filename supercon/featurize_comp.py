#!/usr/bin/env python3
"""
Composition-only featurizer for Tc prediction (magpie-style).

Turns a chemical formula into a fixed-length descriptor vector using
fraction-weighted statistics of elemental properties. Composition-only on
purpose: the same features are computable for any screening candidate
(a formula from MP, a CIF, a guess) without needing a relaxed structure.

Shared by train_tc.py (training on SuperCon formulas) and screen scripts.
"""

import math

import numpy as np
from pymatgen.core import Composition, Element

# Elemental properties used for weighted stats. Each entry: (name, getter).
# Getters must return a float or None (None -> element skipped for that
# property, weights renormalized).


def _valence_electrons(el: Element):
    """Count electrons outside the noble-gas core."""
    noble_z = [2, 10, 18, 36, 54, 86]
    core = max((z for z in noble_z if z <= el.Z), default=0)
    return float(el.Z - core)


def _unfilled_d(el: Element):
    d = sum(n for (_, orb, n) in el.full_electronic_structure if orb == "d")
    return float(d % 10) if d else 0.0


def _first_ionization(el: Element):
    ie = el.ionization_energies
    return float(ie[0]) if ie else None


_PROPS = [
    ("Z", lambda el: float(el.Z)),
    ("mass", lambda el: float(el.atomic_mass)),
    ("radius", lambda el: float(el.atomic_radius) if el.atomic_radius else None),
    ("electroneg", lambda el: float(el.X) if not math.isnan(el.X) else None),
    ("row", lambda el: float(el.row)),
    ("group", lambda el: float(el.group)),
    ("valence", _valence_electrons),
    ("d_electrons", _unfilled_d),
    ("ionization", _first_ionization),
    ("melting_K", lambda el: _float_or_none(el.melting_point)),
    ("density", lambda el: _float_or_none(el.density_of_solid)),
    ("therm_cond", lambda el: _float_or_none(el.thermal_conductivity)),
]


def _float_or_none(v):
    try:
        f = float(v)
        return f if not math.isnan(f) else None
    except (TypeError, ValueError):
        return None


_ELEM_CACHE: dict[str, dict[str, float | None]] = {}


def _elem_props(sym: str) -> dict[str, float | None]:
    if sym not in _ELEM_CACHE:
        el = Element(sym)
        _ELEM_CACHE[sym] = {name: getter(el) for name, getter in _PROPS}
    return _ELEM_CACHE[sym]


def feature_names() -> list[str]:
    names = []
    for pname, _ in _PROPS:
        for stat in ("wmean", "wstd", "min", "max", "range"):
            names.append(f"{pname}_{stat}")
    names += ["n_elements", "frac_entropy", "max_frac", "min_frac",
              "contains_O", "contains_H", "contains_Cu", "contains_Fe"]
    return names


def featurize_formula(formula: str) -> np.ndarray | None:
    """Return the descriptor vector, or None if the formula is unparseable."""
    try:
        comp = Composition(formula).fractional_composition
    except Exception:
        return None
    items = [(el.symbol, frac) for el, frac in comp.items()]
    if not items:
        return None

    vec: list[float] = []
    for pname, _ in _PROPS:
        vals, wts = [], []
        for sym, frac in items:
            v = _elem_props(sym)[pname]
            if v is not None:
                vals.append(v)
                wts.append(frac)
        if not vals:
            vec += [np.nan] * 5
            continue
        vals = np.asarray(vals)
        wts = np.asarray(wts)
        wts = wts / wts.sum()
        mean = float(np.dot(wts, vals))
        std = float(np.sqrt(np.dot(wts, (vals - mean) ** 2)))
        vec += [mean, std, float(vals.min()), float(vals.max()),
                float(vals.max() - vals.min())]

    fracs = np.asarray([f for _, f in items])
    entropy = float(-(fracs * np.log(fracs)).sum())
    syms = {s for s, _ in items}
    vec += [float(len(items)), entropy, float(fracs.max()), float(fracs.min()),
            float("O" in syms), float("H" in syms),
            float("Cu" in syms), float("Fe" in syms)]
    return np.asarray(vec, dtype=float)


if __name__ == "__main__":
    import sys
    for f in sys.argv[1:]:
        v = featurize_formula(f)
        print(f, "->", None if v is None else f"{len(v)} features")
