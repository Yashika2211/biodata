"""Loader for the public eICU Collaborative Research Database *demo*.

File: ``vitalPeriodic.csv.gz`` (columns verified against the real file:
``patientunitstayid, observationoffset`` [minutes since unit admission],
``heartrate, sao2, respiration, systemicsystolic, temperature``).  ``patient.csv.gz``
supplies ``hospitalid`` which defines the (naturally non-IID) sites.

eICU ``vitalPeriodic`` is stored on a 5-minute grid; we re-grid by rounding
offsets to 5-minute bins so any jitter becomes a clean regular series.  Gaps are
NaN ("no evidence").  There is **no ground-truth anomaly label** in this
database: episodes are injected afterwards (semi-synthetic protocol), see
``pvm.cohort.inject_episodes``.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from .. import config as C
from ..cohort import Patient, inject_episodes

COLS = {"hr": "heartrate", "spo2": "sao2", "rr": "respiration",
        "sbp": "systemicsystolic", "temp": "temperature"}
DEFAULT_DIR = os.path.join("data", "raw", "eicu-demo")


def find_files(data_dir: str = DEFAULT_DIR):
    vp = os.path.join(data_dir, "vitalPeriodic.csv.gz")
    if not os.path.exists(vp):
        vp = os.path.join(data_dir, "vitalPeriodic.csv")
    pt = os.path.join(data_dir, "patient.csv.gz")
    if not os.path.exists(pt):
        pt = os.path.join(data_dir, "patient.csv")
    return vp, pt


def load_series(data_dir: str = DEFAULT_DIR, dt_min: float = 5.0,
                min_samples: int = 600, max_samples: int = 1152,
                min_cov: dict | None = None):
    """Return a list of (stay_id, hospital_id, X[T,5]) clean real series.

    ``min_cov`` = minimum non-missing fraction for hr, spo2, rr (SBP and
    temperature are sparse in vitalPeriodic and are simply NaN when absent).
    """
    min_cov = min_cov or {"hr": 0.8, "spo2": 0.6, "rr": 0.5}
    vp, pt = find_files(data_dir)
    if not os.path.exists(vp):
        raise FileNotFoundError(
            f"{vp} not found. Download the eICU-CRD demo (see data/README.md) "
            "and place vitalPeriodic.csv.gz and patient.csv.gz in " + data_dir)
    cols = ["patientunitstayid", "observationoffset"] + list(COLS.values())
    v = pd.read_csv(vp, usecols=cols)
    hosp = {}
    if os.path.exists(pt):
        p = pd.read_csv(pt, usecols=["patientunitstayid", "hospitalid"])
        hosp = dict(zip(p.patientunitstayid, p.hospitalid))
    v = v[v.observationoffset >= 0].copy()
    v["bin"] = np.round(v.observationoffset / dt_min).astype(int)
    out = []
    for sid, g in v.groupby("patientunitstayid"):
        g = g.groupby("bin").last()
        b0, b1 = int(g.index.min()), int(g.index.max())
        T = b1 - b0 + 1
        if T < min_samples:
            continue
        T = min(T, max_samples)
        X = np.full((T, C.NV), np.nan)
        idx = g.index.values - b0
        keep = idx < T
        for j, name in enumerate(C.VITALS):
            X[idx[keep], j] = g[COLS[name]].values[keep]
        # drop implausible values -> NaN
        for j, name in enumerate(C.VITALS):
            lo, hi = C.VALID_RANGE[name]
            bad = (X[:, j] < lo) | (X[:, j] > hi)
            X[bad, j] = np.nan
        ok = all(np.mean(~np.isnan(X[:, C.VITALS.index(k)])) >= c for k, c in min_cov.items())
        if ok:
            out.append((str(sid), int(hosp.get(sid, -1)), X))
    return out


def assign_sites(hospital_ids, n_sites: int):
    """Group hospitals into ``n_sites`` sites of roughly equal patient count."""
    counts = pd.Series(hospital_ids).value_counts()
    loads = [0] * n_sites
    mapping = {}
    for h, c in counts.items():          # largest first, greedy balance
        k = int(np.argmin(loads))
        mapping[h] = k
        loads[k] += int(c)
    return mapping


def make_cohort(series, n_sites: int = 4, seed: int = 0, frac: float = 0.85,
                episode_rate: float = 0.4, dt_min: float = 5.0):
    """Semi-synthetic cohort: real vitals + injected, labelled episodes."""
    rng = np.random.default_rng(seed)
    n = len(series)
    sel = rng.choice(n, size=max(2 * n_sites, int(frac * n)), replace=False)
    sel.sort()
    mapping = assign_sites([series[i][1] for i in sel], n_sites)
    patients = []
    for i in sel:
        sid, hid, X = series[i]
        Xi, y, ep, eps = inject_episodes(X, rng, dt_min, rate_per_day=episode_rate)
        patients.append(Patient(pid=f"eicu-{sid}", site=f"site{mapping[hid]}", X=Xi, y=y,
                               ep_id=ep, episodes=eps, dt_min=dt_min, phenotype=f"h{hid}"))
    return patients
