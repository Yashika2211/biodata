"""Slide: problem."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    h0 = H[first]
    s = dk.slide("One fixed threshold for every patient fails",
                 "Alarm fatigue: a single SpO2 < 92% rule alarms constantly for a patient whose healthy baseline is 90%, "
                 "for example chronic lung disease. Centralising raw vitals to learn better rules creates privacy and bandwidth "
                 "problems. Our research question is the one at the bottom. Labels in this study are semi-synthetic: real or simulated "
                 "physiology with injected, labelled deterioration episodes, so numbers are not clinical performance.")
    dk.bullets(s, ["Static ward thresholds → constant false alarms → **alarm fatigue**",
                   "Patients differ: athlete HR 52, COPD SpO2 90, hypertensive SBP 150",
                   "Pooling raw vitals centrally raises **privacy** and **bandwidth** problems"], 0.7, 1.7, 12, 3.2, size=26)
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(5.0), Inches(11.9), Inches(1.6))
    box.fill.solid(); box.fill.fore_color.rgb = LIGHT; box.line.color.rgb = BLUE
    dk.text(s, ["**Research question**", "Can we match baseline accuracy while raw data stays local (federated and/or private)?"],
            0.95, 5.1, 11.4, 1.4, size=24, color=NAVY)
