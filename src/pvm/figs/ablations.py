"""Ablation grid."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .style import COL, DS_LABEL, _save, _load, _m


def fig_ablations(S, ds):
    A = S["datasets"][ds].get("ablations")
    if not A:
        return None
    fig, ax = plt.subplots(2, 3, figsize=(13, 7))
    a = ax[0, 0]
    xs = sorted(A["alpha"], key=float)
    for k, c, nm in (("C", COL["C"], "C adaptive threshold"), ("D", COL["D"], "D centralised ML")):
        a.errorbar([float(x) for x in xs], [A["alpha"][x][k]["fa_per_day"]["mean"] for x in xs],
                   yerr=[A["alpha"][x][k]["fa_per_day"]["sd"] for x in xs], marker="o", color=c, label=nm, capsize=2)
    a.set_xscale("log"); a.set_xlabel("EWMA rate α"); a.set_ylabel("false alarms / patient-day"); a.legend(fontsize=8)
    a.set_title("(a) adaptation rate α: false alarms")
    a = ax[0, 1]
    for k, c, nm in (("C", COL["C"], "C"), ("D", COL["D"], "D")):
        a.errorbar([float(x) for x in xs], [A["alpha"][x][k]["f1"]["mean"] for x in xs],
                   yerr=[A["alpha"][x][k]["f1"]["sd"] for x in xs], marker="o", color=c, label=nm, capsize=2)
    a.set_xscale("log"); a.set_xlabel("EWMA rate α"); a.set_ylabel("F1"); a.set_title("(b) adaptation rate α: F1")
    a.legend(fontsize=8)
    a = ax[0, 2]
    xm = sorted(A["m"], key=int)
    for k, c, nm in (("A2", COL["A2"], "A2 static"), ("C", COL["C"], "C adaptive"), ("D", COL["D"], "D ML adaptive")):
        a.errorbar([int(x) for x in xm], [A["m"][x][k]["fa_per_day"]["mean"] for x in xm],
                   yerr=[A["m"][x][k]["fa_per_day"]["sd"] for x in xm], marker="o", color=c, label=nm, capsize=2)
    a.set_yscale("log"); a.set_xlabel("persistence m (consecutive samples)"); a.set_ylabel("false alarms / patient-day")
    a.set_title("(c) persistence m"); a.legend(fontsize=8)
    a = ax[1, 0]
    xc = sorted(A["clip"], key=float)
    a.errorbar([float(x) for x in xc], [A["clip"][x]["f1"]["mean"] for x in xc],
               yerr=[A["clip"][x]["f1"]["sd"] for x in xc], marker="o", color=COL["G"], capsize=2)
    a.axhline(S["datasets"][ds]["methods"]["F"]["f1"]["mean"], color=COL["F"], ls="--", label="F (no DP)")
    a.set_xscale("log"); a.set_xlabel("per-record clip norm C (σ = 8)"); a.set_ylabel("F1")
    a.set_title("(d) DP clipping bound"); a.legend(fontsize=8)
    a = ax[1, 1]
    xs_ = sorted(A["sites"], key=int)
    for k, c, nm in (("D", COL["D"], "D centralised"), ("E", COL["E"], "E local-only"), ("F", COL["F"], "F federated")):
        a.errorbar([int(x) for x in xs_], [A["sites"][x][k]["f1"]["mean"] for x in xs_],
                   yerr=[A["sites"][x][k]["f1"]["sd"] for x in xs_], marker="o", color=c, label=nm, capsize=2)
    a.set_xticks([int(x) for x in xs_]); a.set_xlabel("number of sites"); a.set_ylabel("F1")
    a.set_title("(e) number of sites"); a.legend(fontsize=8)
    a = ax[1, 2]
    xr = sorted(A["rounds"], key=int)
    a.plot([int(x) for x in xr], [A["rounds"][x]["f1"]["mean"] for x in xr], marker="o", color=COL["F"], label="F1")
    a.fill_between([int(x) for x in xr], [A["rounds"][x]["f1"]["mean"] - A["rounds"][x]["f1"]["sd"] for x in xr],
                   [A["rounds"][x]["f1"]["mean"] + A["rounds"][x]["f1"]["sd"] for x in xr], color=COL["F"], alpha=0.2)
    a.set_xscale("log"); a.set_xlabel("FedAvg rounds"); a.set_ylabel("F1"); a.set_title("(f) number of FL rounds")
    fig.suptitle(f"Ablations — {DS_LABEL[ds]} (mean ± sd over {A['alpha'][xs[0]]['C']['f1']['n']} seeds)", fontsize=12)
    fig.tight_layout()
    return _save(fig, f"fig_ablations_{ds}.png")


