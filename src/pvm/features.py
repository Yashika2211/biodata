"""The single shared feature-extraction path.

Used by offline training, offline evaluation, the Kafka-free local runner and
the Spark ``applyInPandasWithState`` job.  The per-patient state is a plain
JSON-serialisable dict, so it can be carried between micro-batches.

Two modes share the same code:

* ``adaptive``: z-scores against a per-patient EWMA mean/variance.
* ``static``:   z-scores against fixed population priors (used by methods A/B).

NaN means "no evidence": a missing or implausible sample yields NaN z, which
never updates the state and contributes 0 to the model features.
"""
from __future__ import annotations

import json
import math
from typing import Iterable, Sequence

from . import config as C

NAN = float("nan")


def _isnan(x) -> bool:
    return x is None or x != x


def new_state(mode: str = "adaptive", alpha: float = C.ALPHA,
              window: int = C.WINDOW) -> dict:
    """Fresh per-patient state, initialised from the population priors."""
    return {
        "mode": mode,
        "alpha": alpha,
        "window": window,
        "n": [0.0] * C.NV,
        "mu": [C.PRIOR_MEAN[v] for v in C.VITALS],
        "var": [C.PRIOR_SD[v] ** 2 for v in C.VITALS],
        "buf": [],      # last `window` rows of z (None = NaN), oldest first
        "t": 0,
    }


def state_to_json(state: dict) -> str:
    return json.dumps(state, separators=(",", ":"))


def state_from_json(s: str) -> dict:
    return json.loads(s)


def clean_value(i: int, x) -> float:
    """Return x, or NaN if missing / outside the plausible range."""
    if _isnan(x):
        return NAN
    lo, hi = C.VALID_RANGE[C.VITALS[i]]
    x = float(x)
    if x < lo or x > hi:
        return NAN
    return x


def _scale(state: dict, i: int) -> float:
    floor = C.MIN_SCALE[C.VITALS[i]]
    if state["mode"] == "static":
        return C.PRIOR_SD[C.VITALS[i]]
    return max(math.sqrt(max(state["var"][i], 0.0)), floor)


def update_state(state: dict, x: Sequence[float]) -> list:
    """Score ``x`` against the current state, then update it in place.

    Returns the z-score row (``None`` for NaN) *before* the update, so an
    anomalous sample cannot absorb itself into the baseline it is judged by.
    """
    z_row = []
    adaptive = state["mode"] == "adaptive"
    for i in range(C.NV):
        xi = clean_value(i, x[i])
        if xi != xi:
            z_row.append(None)
            continue
        if adaptive:
            mu, sd = state["mu"][i], _scale(state, i)
        else:
            mu, sd = C.PRIOR_MEAN[C.VITALS[i]], C.PRIOR_SD[C.VITALS[i]]
        z = (xi - mu) / sd
        z_row.append(z)
        if adaptive:
            # Winsorised update, slower while abnormal, prior pseudo-count.
            xw = min(max(xi, mu - C.WINSOR_K * sd), mu + C.WINSOR_K * sd)
            rate = max(state["alpha"], 1.0 / (state["n"][i] + C.PRIOR_COUNT))
            if abs(z) > C.ABNORMAL_Z:
                rate *= C.SLOW_FACTOR
            d = xw - mu
            state["mu"][i] = mu + rate * d
            state["var"][i] = (1.0 - rate) * (state["var"][i] + rate * d * d)
            state["n"][i] += 1.0
    state["buf"].append(z_row)
    if len(state["buf"]) > state["window"]:
        del state["buf"][0]
    state["t"] += 1
    return z_row


def features_from_state(state: dict) -> list:
    """15 features: current z, window mean z, window max|z| per vital."""
    buf = state["buf"]
    cur = buf[-1] if buf else [None] * C.NV
    z_now, z_mean, z_max = [], [], []
    for i in range(C.NV):
        col = [r[i] for r in buf if r[i] is not None]
        z_now.append(0.0 if cur[i] is None else cur[i])
        z_mean.append(sum(col) / len(col) if col else 0.0)
        z_max.append(max(abs(c) for c in col) if col else 0.0)
    return z_now + z_mean + z_max


def process_event(state: dict, x: Sequence[float]) -> list:
    """The one entry point everything calls: update state, return features."""
    update_state(state, x)
    return features_from_state(state)


def process_series(X: Iterable[Sequence[float]], mode: str = "adaptive",
                   alpha: float = C.ALPHA, state: dict | None = None):
    """Offline helper: run a whole series, return (features list, state)."""
    st = state if state is not None else new_state(mode, alpha)
    return [process_event(st, x) for x in X], st
