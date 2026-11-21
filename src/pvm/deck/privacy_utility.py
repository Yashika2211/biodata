"""Slide: privacy_utility."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    s = dk.slide("Privacy costs little until the noise gets large",
                 "DP-SGD with per-record clipping, Gaussian noise and a Renyi accountant at delta 1e-5. Epsilon here is record-level, not "
                 "patient-level; one patient contributes hundreds of correlated rows, so patient-level protection is much weaker. "
                 "The green band is non-private FedAvg; the orange line is FedAvg with DP at five noise levels; the dashed line is the "
                 "centralised baseline. A simple membership-inference attack found no leakage even for the non-private models, "
                 "which is a sanity check, not a proof.", tag="both datasets")
    yy = 1.4
    for ds in D:
        dk.image(s, f"figures/fig_privacy_utility_{ds}.png", 0.9, yy, w=7.3)
        dk.text(s, DS_NAME[ds], 8.5, yy + 0.5, 4.5, 0.8, size=17, bold=True, color=BLUE)
        k = H[ds]["dp_keep"]
        if k:
            dk.text(s, f"No measurable F1 loss up to σ = {k['sigma']:g} (record-level ε = {eps_str(k['epsilon'])})", 8.5, yy + 1.2, 4.5, 1.2,
                    size=16, color=RGBColor(0x22, 0x22, 0x22))
        yy += 2.9
    dk.text(s, "ε is record-level (δ = 1e-5), not patient-level", 8.5, 6.8, 4.6, 0.4, size=13, color=ORANGE, bold=True)
