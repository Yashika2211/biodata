"""Generate every figure from data / results/summary.json.  Dataset on every title."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from . import config as C
from . import features as F
from . import metrics as M

FIG = "figures"
DS_LABEL = {"synthetic": "Synthetic cohort", "eicu": "eICU-CRD demo + injected episodes"}
COL = {"A": "#9a9a9a", "A2": "#6b6b6b", "B": "#e69f00", "C": "#56b4e9", "D": "#0072b2",
       "E": "#cc79a7", "F": "#009e73", "G": "#d55e00"}
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 12, "axes.labelsize": 11, "figure.dpi": 100,
                     "savefig.dpi": 200, "savefig.bbox": "tight", "legend.frameon": False})


def _save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    p = os.path.join(FIG, name)
    fig.savefig(p)
    plt.close(fig)
    return p


# ----------------------------------------------------------------- architecture
def fig_architecture(path="docs/architecture.png"):
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.set_xlim(0, 11); ax.set_ylim(0, 4.6); ax.axis("off")

    def box(x, y, w, h, text, fc, ec="#333", fs=10, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08",
                                    fc=fc, ec=ec, lw=1.2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", linespacing=1.25)

    def arrow(x0, y0, x1, y1, text="", dy=0.16):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#333"))
        if text:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, text, ha="center", fontsize=8.5, color="#333")

    ax.add_patch(FancyBboxPatch((0.1, 0.35), 7.3, 4.0, boxstyle="round,pad=0.03,rounding_size=0.1",
                                fc="#eef6fb", ec="#0072b2", lw=1.6, ls="--"))
    ax.text(0.3, 4.1, "SITE (raw vitals never leave)", fontsize=10.5, color="#0072b2", fontweight="bold")
    box(0.35, 2.0, 1.7, 1.2, "Producer\nreplays vitals\n+ producer ts", "#fff")
    box(2.55, 2.0, 1.9, 1.2, "kafka-site :9092\nvitals.raw.<site>\n(1 h retention)", "#fde9c8", bold=False)
    box(4.95, 2.0, 2.2, 1.2, "Spark Structured\nStreaming\nper-patient JSON state", "#d8f0e5")
    box(0.35, 0.55, 3.6, 0.95, "Local training\n(FedAvg / DP-SGD client)", "#e8e3f4")
    box(4.75, 3.45, 2.6, 0.55, "shared code path: offline == serving", "#fff", fs=8.5)
    ax.add_patch(FancyBboxPatch((8.0, 0.35), 2.9, 4.0, boxstyle="round,pad=0.03,rounding_size=0.1",
                                fc="#fdf1e8", ec="#d55e00", lw=1.6, ls="--"))
    ax.text(8.2, 4.1, "CENTRAL", fontsize=10.5, color="#d55e00", fontweight="bold")
    box(8.25, 2.0, 2.4, 1.2, "kafka-central :9093\nalerts.central\n(hashed id, score)", "#fde9c8")
    box(8.25, 0.55, 2.4, 0.95, "FL server (FedAvg)\n+ alert consumer", "#e8e3f4", fs=9.5)
    arrow(2.05, 2.6, 2.55, 2.6)
    arrow(4.45, 2.6, 4.95, 2.6)
    arrow(7.15, 2.6, 8.25, 2.6, "alerts only", dy=0.2)
    arrow(3.95, 1.0, 8.25, 1.0, "model updates / count tables", dy=0.15)
    return _save_to(fig, path)


def _save_to(fig, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


# ------------------------------------------------------- adaptive-threshold example
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
    from .data import public as PB
    from .data import synthetic as SY
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
            from .cohort import Patient, inject_episodes
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


if __name__ == "__main__":
    fig_architecture()
    print(fig_adaptive_examples())
