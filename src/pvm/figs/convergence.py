"""Federated convergence figure."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .style import COL, DS_LABEL, _save, _load, _m


def fig_fl_convergence(S):
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for ds, c in (("synthetic", "#0072b2"), ("eicu", "#d55e00")):
        if ds not in S["datasets"]:
            continue
        f = S["datasets"][ds]["federated"]
        curve = np.array(f["loss_curve"])
        opt = curve[-1, 1] - f["final_loss_gap"]["mean"]
        ax.plot(curve[:, 0], np.maximum(curve[:, 1] - opt, 1e-9), color=c, lw=1.8,
                label=f"{DS_LABEL[ds].split(' +')[0]} (≤1e-3 rel. at round {f['rounds_to_converge']['mean']:.0f})")
    ax.set_yscale("log"); ax.set_xlabel("FedAvg round"); ax.set_ylabel("training loss − centralised optimum")
    ax.axhline(1e-3 * 0.4, color="#777", ls=":", lw=1)
    ax.legend(fontsize=8.5); ax.set_title("Federated training reaches the centralised optimum (seed 0)")
    fig.tight_layout()
    return _save(fig, "fig_fl_convergence.png")


