"""Architecture diagram (docs/architecture.png)."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from matplotlib.patches import FancyBboxPatch

from .style import _save


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


