"""Slide: latency."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    lat = S["latency"]; k = lat.get("kafka"); ip = lat.get("inprocess")
    s = dk.slide("Latency is set by the micro-batch trigger",
                 "Real end-to-end latency measured by the alert consumer: producer timestamp to consumer receipt, through Kafka, Spark and "
                 "Kafka again, at three event rates and three trigger intervals. Benchmarks ran on one laptop, one broker per cluster, Spark "
                 "local mode with two cores. In-process, one event takes about "
                 + (f"{ip['step_us']['p50']:.0f} microseconds. " if ip else "") +
                 "So Spark's micro-batch trigger dominates. For 5-minute vitals even a 5 second trigger is clinically negligible.",
                 tag="Synthetic replay")
    dk.image(s, "figures/fig_latency.png", 0.5, 1.45, w=9.0)
    if k:
        r1 = [r for r in k["runs"] if r["trigger"] == "1 second" and r["target_rate"] == 500]
        if r1:
            dk.stat(s, f"{r1[0]['latency_ms']['p50']/1000:.2f} s", "p50 end-to-end, 1 s trigger, 500 ev/s", 9.8, 1.5, 3.1, BLUE)
            dk.stat(s, f"{r1[0]['latency_ms']['p99']/1000:.2f} s", "p99 end-to-end, same run", 9.8, 3.2, 3.1, ORANGE)
    if ip:
        dk.stat(s, f"{ip['step_us']['p99']:.0f} µs", "p99 in-process, per event", 9.8, 4.9, 3.1, GREEN)
