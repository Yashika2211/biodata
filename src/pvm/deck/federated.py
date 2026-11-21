"""Slide: federated."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    s = dk.slide("Federated matches centralised",
                 "FedAvg with full participation across non-IID sites. Raw rows never leave a site; only model weights move. "
                 "We ran enough rounds to converge: the training loss reaches the centralised optimum, and the table shows the paired "
                 "difference between F and D over seeds with a 95 percent confidence interval. With five seeds the intervals are wide; "
                 "we say indistinguishable, not identical. Local-only training E is shown for contrast.", tag="both datasets")
    dk.image(s, "figures/fig_fl_convergence.png", 0.5, 1.5, w=6.4)
    y = 1.6
    for ds in D:
        h = H[ds]
        dk.text(s, [f"**{DS_NAME[ds]}**", f"F1(F) − F1(D) = {ci(h['F_D']['f1'])}",
                    f"AUROC(F) − AUROC(D) = {ci(h['F_D']['auroc'])}",
                    f"converged in ~{h['rounds_conv']:.0f} rounds (ran {h['rounds_used']})"], 7.2, y, 5.8, 2.1, size=17,
                color=RGBColor(0x22, 0x22, 0x22))
        y += 2.4
    dk.text(s, "Mean [95% CI] of paired per-seed differences, n = 5.", 7.2, 6.55, 5.8, 0.4, size=13, color=GREY)
