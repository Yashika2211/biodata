"""Bytes leaving the site."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .style import COL, DS_LABEL, _save, _load, _m


def fig_cost(S):
    c = S.get("cost") or {}
    if not c:
        return None
    ds = "eicu" if "eicu" in c else list(c)[0]
    v = c[ds]
    vals = [v["raw_stream_bytes"], v["federated_bytes"], v["alert_bytes"], v["model_update_bytes"]]
    labels = ["raw streaming\n(centralised)", "federated total\n(alerts+updates)", "  of which\nalerts", "  of which\nmodel updates"]
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    b = ax.bar(range(4), vals, color=[COL["B"], COL["F"], "#7fcdbb", "#c7e9c0"], edgecolor="#222", lw=0.6)
    ax.set_yscale("log"); ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=9)
    for i, x in enumerate(vals):
        ax.text(i, x * 1.15, f"{x/1e6:,.1f} MB" if x < 1e9 else f"{x/1e9:,.2f} GB", ha="center", fontsize=9)
    ax.set_ylabel("bytes leaving the site / month (log)")
    sc = v["scenario"]
    ax.set_title(f"{sc['patients']} patients, 1 sample/{sc['sample_minutes']:g} min, {sc['days']} days — "
                 f"{v['reduction_factor']:,.0f}× less data leaves", fontsize=10.5)
    ax.set_ylim(top=max(vals) * 8)
    fig.tight_layout()
    return _save(fig, "fig_cost.png")


