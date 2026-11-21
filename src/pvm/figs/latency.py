"""End-to-end latency and throughput figure."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .style import COL, DS_LABEL, _save, _load, _m


def fig_latency(S):
    k = S["latency"].get("kafka")
    if not k:
        return None
    runs = k["runs"]
    trig = ["500 milliseconds", "1 second", "5 seconds"]
    rates = sorted({r["target_rate"] for r in runs if r["target_rate"] > 0})
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw=dict(width_ratios=[2.2, 1]))
    w = 0.26
    pal = ["#9ecae1", "#4292c6", "#08519c"]
    for i, rate in enumerate(rates):
        xs, p50, p95, p99 = [], [], [], []
        for j, t in enumerate(trig):
            r = [r for r in runs if r["trigger"] == t and r["target_rate"] == rate]
            if r:
                xs.append(j + (i - 1) * w); l = r[0]["latency_ms"]
                p50.append(l["p50"]); p95.append(l["p95"]); p99.append(l["p99"])
        ax[0].bar(xs, p50, w, color=pal[i], edgecolor="#222", lw=0.6, label=f"{rate:g} events/s")
        ax[0].scatter(xs, p95, marker="_", s=260, color="#d55e00", zorder=3, lw=2, label="p95" if i == 0 else None)
        ax[0].scatter(xs, p99, marker="x", s=36, color="#222", zorder=3, label="p99" if i == 0 else None)
    ax[0].set_xticks(range(len(trig))); ax[0].set_xticklabels(["0.5 s", "1 s", "5 s"])
    ax[0].set_xlabel("micro-batch trigger interval"); ax[0].set_ylabel("end-to-end latency (ms), bars = p50")
    ax[0].set_yscale("log"); ax[0].set_ylim(top=3e4); ax[0].legend(fontsize=8, ncol=3, loc="upper left")
    ax[0].set_title("Kafka → Spark → Kafka latency (synthetic replay, 1 broker per cluster)")
    thr = []
    for t in trig:
        r = [r for r in runs if r["trigger"] == t and r["target_rate"] == 0]
        thr.append(r[0]["throughput_eps"] if r and r[0].get("throughput_eps") and r[0]["throughput_eps"] < 20000 else 0)
    ax[1].bar(range(len(trig)), thr, color=COL["F"], edgecolor="#222", lw=0.6)
    for i, v in enumerate(thr):
        ax[1].text(i, v, f"{v:,.0f}" if v else "n/a\n(one batch)", ha="center", va="bottom", fontsize=9)
    ax[1].set_xticks(range(len(trig))); ax[1].set_xticklabels(["0.5 s", "1 s", "5 s"])
    ax[1].set_xlabel("trigger"); ax[1].set_ylabel("events / s"); ax[1].set_title("Max sustained throughput\n(local[2])")
    fig.tight_layout()
    return _save(fig, "fig_latency.png")


