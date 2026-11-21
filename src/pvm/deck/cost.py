"""Slide: cost."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    cost = S.get("cost") or {}
    s = dk.slide("Only alerts and updates leave the site",
                 "Bytes leaving the site per month for a scenario of 1000 patients, one sample per 5 minutes. Centralised raw streaming "
                 "versus alerts plus federated model updates plus threshold count tables. Bytes and CPU-seconds are measured; dollar "
                 "figures use the illustrative price table in the report: egress 9 cents per GB, 4 cents per vCPU-hour.",
                 tag=DS_NAME["eicu"] if "eicu" in cost else "scenario")
    dk.image(s, "figures/fig_cost.png", 0.5, 1.5, w=7.6)
    if cost:
        v = cost.get("eicu") or next(iter(cost.values()))
        dk.stat(s, f"{v['reduction_factor']:,.0f}×", "fewer bytes leave the site", 8.6, 1.6, 4.1, GREEN)
        dk.stat(s, fmt_bytes(v["raw_stream_bytes"]), "raw streaming / month", 8.6, 3.3, 4.1, ORANGE)
        dk.stat(s, fmt_bytes(v["federated_bytes"]), "alerts + FL updates / month", 8.6, 5.0, 4.1, BLUE)
