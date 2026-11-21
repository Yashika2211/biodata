"""Accuracy comparison figure."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .style import COL, DS_LABEL, _save, _load, _m


def fig_accuracy(S, ds):
    d = S["datasets"][ds]
    keys = ["A", "A2", "B", "C", "D", "E", "F", "G@8.0"]
    labels = ["A\nstatic", "A2\nstatic+m", "B\ncentral\nfixed", "C\nadaptive\nthreshold", "D\ncentral\nadaptive",
              "E\nlocal", "F\nfederated", "G\nFL+DP\n(σ=8)"]
    cols = [COL[k.split("@")[0]] for k in keys]
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
    for a, metric, ttl, log in ((ax[0], "f1", "Alarm-level F1 (higher is better)", False),
                                (ax[1], "fa_per_day", "False alarms per patient-day (lower is better)", True)):
        mu = [_m(d, k, metric)[0] for k in keys]
        sd = [_m(d, k, metric)[1] for k in keys]
        a.bar(range(len(keys)), mu, yerr=sd, color=cols, capsize=3, edgecolor="#222", lw=0.6)
        a.set_xticks(range(len(keys))); a.set_xticklabels(labels, fontsize=8.5)
        a.set_title(ttl)
        if log:
            a.set_yscale("log")
        for i, m_ in enumerate(mu):
            top = (m_ + sd[i]) * 1.12 if log else m_ + sd[i] + 0.012
            a.text(i, top, f"{m_:.2f}", ha="center", va="bottom", fontsize=8)
        if log:
            a.set_ylim(top=max(mu) * 2.6)
    fig.suptitle(f"{DS_LABEL[ds]} — mean ± sd over {d['n_seeds']} seeds, held-out last 40 % of each series", fontsize=11, y=1.02)
    fig.tight_layout()
    return _save(fig, f"fig_accuracy_{ds}.png")


