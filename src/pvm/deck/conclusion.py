"""Slide: conclusion."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    s = dk.slide("Conclusion",
                 "Answer to the research question: yes, within our statistical resolution and on injected-label benchmarks. "
                 "Adaptive thresholds cut false alarms; federated training on adaptive features matched centralised; record-level DP was "
                 "nearly free at moderate noise; and sending only alerts and model updates cuts bytes by orders of magnitude. "
                 "Next steps: validate on real annotated alarms and analyse patient-level privacy.")
    items = []
    for ds in D:
        h = H[ds]
        items.append(f"**{DS_NAME[ds]}:** adaptive threshold −{h['fa_cut_C_vs_A2']*100:.0f}% false alarms; "
                     f"F − D F1 = {ci(h['F_D']['f1'])}")
    items += ["Privacy noise is nearly free until σ becomes large (record-level ε)",
              "Raw vitals stay local; alerts + model updates only",
              "**Next:** real annotated alarms, patient-level privacy"]
    dk.bullets(s, items, 0.8, 1.7, 11.8, 5.2, size=24)
