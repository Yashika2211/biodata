"""Slide: adaptive."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    ex = "figures/fig_adaptive_synthetic.png"
    s = dk.slide("Each patient vs their own baseline",
                 "This is the example the whole study is about. This patient has a normal SpO2 of about 90 percent. The fixed 92 percent "
                 "threshold, orange dots, alarms essentially all the time. The adaptive baseline, blue, learns the patient's normal "
                 "and alarms only on the injected deterioration, shaded, and a few motion artefacts. Mechanism: per-patient EWMA mean "
                 "and variance, winsorised updates, slower learning while abnormal, population priors for cold start, minimum-scale floors, "
                 "NaN means no evidence. A real eICU trace tells the same story; see the report.", tag="Synthetic cohort (COPD patient)")
    dk.image(s, ex, 0.55, 1.45, w=8.4)
    dk.bullets(s, ["**Fixed 92 %**: alarms all day", "**Adaptive**: learns this patient's ~90 %",
                   "Winsorised, slower while abnormal, prior for cold start"], 9.1, 1.8, 3.9, 4.8, size=20)
