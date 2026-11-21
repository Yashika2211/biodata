"""The adaptive-threshold example: a patient whose normal SpO2 is ~90 % alarms constantly under a fixed 92 % threshold."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .. import config as C
from .. import features as F
from .. import metrics as M
from .style import _save


def _trace(p, j=1):
    st = F.new_state("adaptive")
    mu, sd, z = [], [], []
    for x in p.X:
        mu.append(st["mu"][j]); sd.append(max(math.sqrt(st["var"][j]), C.MIN_SCALE[C.VITALS[j]]))
        row = F.update_state(st, x)
        z.append(np.nan if row[j] is None else row[j])
    return np.array(mu), np.array(sd), np.array(z)


def plot_adaptive_example(p, title, fname, tau_z=3.5, thr=92.0, j=1):
    mu, sd, z = _trace(p, j)
    x = p.X[:, j]
    t_h = np.arange(p.T) * p.dt_min / 60.0
    stat = np.where(np.isnan(x), 0.0, (thr - x))         # >0 means below threshold
    s_flag = np.where(np.isnan(x), False, x < thr)
    a_flag = np.where(np.isnan(z), False, z < -tau_z)
    lo = int(2 * 60 / p.dt_min)
    n_static = sum(len(range(a + 2, b, 12)) for a, b in M.runs(s_flag[lo:], 3))
    n_adapt = sum(len(range(a + 2, b, 12)) for a, b in M.runs(a_flag[lo:], 3))
    days = p.T * p.dt_min / 1440.0
    fig, ax = plt.subplots(2, 1, figsize=(10, 5.6), sharex=True, gridspec_kw=dict(height_ratios=[2.2, 1]))
    a = ax[0]
    a.plot(t_h, x, color="#333", lw=0.9, label="SpO2 (%)")
    a.axhline(thr, color="#d55e00", lw=1.8, ls="--", label=f"fixed ward threshold ({thr:.0f}%)")
    a.plot(t_h, mu, color="#0072b2", lw=1.6, label="adaptive baseline")
    a.fill_between(t_h, mu - tau_z * sd, np.minimum(mu + tau_z * sd, 100.0), color="#0072b2", alpha=0.13,
                   label=f"adaptive band (±{tau_z} sd)")
    for s, e, k in p.episodes:
        a.axvspan(s * p.dt_min / 60, e * p.dt_min / 60, color="#d55e00", alpha=0.18, lw=0)
    a.scatter(t_h[s_flag], x[s_flag], s=7, color="#d55e00", zorder=3, label="below fixed threshold")
    a.axvline(p.split * p.dt_min / 60, color="#777", lw=1, ls=":")
    a.set_ylim(40, 103)
    a.text(p.split * p.dt_min / 60 + 0.6, 41.5, "held-out test →", fontsize=9, color="#555", va="bottom")
    a.set_ylabel("SpO2 (%)")
    a.set_title(f"{title}\nFixed threshold: {n_static} alarms in {days:.1f} days;  "
                f"adaptive: {n_adapt} alarm(s)  (shaded = injected deterioration episode)", fontsize=11)
    a.legend(loc="lower center", ncol=3, fontsize=8.5)
    b = ax[1]
    b.plot(t_h, z, color="#333", lw=0.8)
    b.axhline(-tau_z, color="#0072b2", ls="--", lw=1.4)
    b.set_ylim(-9, 4)
    b.set_ylabel("adaptive z (SpO2)"); b.set_xlabel("hours since start of series")
    for s, e, k in p.episodes:
        b.axvspan(s * p.dt_min / 60, e * p.dt_min / 60, color="#d55e00", alpha=0.18, lw=0)
    fig.tight_layout()
    return _save(fig, fname), dict(static_alarms=int(n_static), adaptive_alarms=int(n_adapt), days=float(days))


def fig_adaptive_examples():
    from ..data import public as PB
    from ..data import synthetic as SY
    out = {}
    rng = np.random.default_rng(5)
    best = None
    for sd in range(40):
        r = np.random.default_rng(sd)
        p = SY.make_patient("copd-demo", "site1", "copd", 4.0, r)
        ev = [e for e in p.episodes if e[2] == "hypoxia" and e[0] >= p.split]
        if ev:
            best = p
            break
    best = best or p
    out["synthetic"] = plot_adaptive_example(
        best, "Synthetic cohort — COPD-phenotype patient (normal SpO2 ≈ 90 %)", "fig_adaptive_synthetic.png")
    try:
        series = PB.load_series()
        cand = [(sid, h, X) for sid, h, X in series
                if 89.0 <= np.nanmedian(X[:, 1]) <= 91.5 and np.isnan(X[:, 1]).mean() < 0.1
                and np.nanpercentile(X[:, 1], 10) >= 87 and np.nanpercentile(X[:, 1], 90) <= 96.5]
        for seed in range(30):
            r = np.random.default_rng(seed)
            sid, h, X = cand[seed % len(cand)]
            from ..cohort import Patient, inject_episodes
            Xi, y, ep, eps = inject_episodes(X, r, 5.0)
            if any(k in ("hypoxia", "shock", "sepsis") and s >= int(0.6 * len(X)) for s, e, k in eps):
                p = Patient(f"eicu-{sid}", "site0", Xi, y, ep, eps, 5.0)
                break
        out["eicu"] = plot_adaptive_example(
            p, "eICU-CRD demo (real SpO2 trace, injected episode) — patient whose normal SpO2 ≈ 90 %",
            "fig_adaptive_eicu.png")
    except FileNotFoundError:
        pass
    return out




