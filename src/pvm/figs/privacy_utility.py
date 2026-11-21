"""Privacy-utility curve."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .style import COL, DS_LABEL, _save, _load, _m


def fig_privacy_utility(S, ds):
    d = S["datasets"][ds]
    pu = [r for r in d["privacy_utility"]]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.0))
    f1_ref = d["methods"]["F"]["f1"]; au_ref = d["methods"]["F"]["auroc"]
    for a, metric, ref, nm in ((ax[0], "f1", f1_ref, "Alarm-level F1"), (ax[1], "auroc", au_ref, "Sample-level AUROC")):
        eps = np.array([r["epsilon"] for r in pu]); mu = np.array([r[metric]["mean"] for r in pu])
        sd = np.array([r[metric]["sd"] for r in pu])
        a.errorbar(eps, mu, yerr=sd, marker="o", color=COL["G"], capsize=3, lw=1.8, label="G: FL + DP")
        for e, m_, r in zip(eps, mu, pu):
            a.annotate(f"σ={r['sigma']:g}", (e, m_), textcoords="offset points", xytext=(4, 8), fontsize=8.5)
        a.axhline(ref["mean"], color=COL["F"], lw=1.8, label="F: FedAvg, no DP (ε=∞)")
        a.axhspan(ref["mean"] - ref["sd"], ref["mean"] + ref["sd"], color=COL["F"], alpha=0.15, lw=0)
        base = d["methods"]["B"][metric]["mean"]
        a.axhline(base, color=COL["B"], lw=1.4, ls="--", label="B: centralised baseline")
        a.set_xscale("log"); a.set_xlabel("record-level ε  (δ = 1e-5; smaller = more private)")
        a.set_ylabel(nm); a.legend(fontsize=8.5, loc="lower right")
    fig.suptitle(f"{DS_LABEL[ds]} — privacy–utility (ε is record-level, not patient-level)", fontsize=11, y=1.02)
    fig.tight_layout()
    return _save(fig, f"fig_privacy_utility_{ds}.png")


