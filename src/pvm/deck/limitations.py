"""Slide: limitations."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    s = dk.slide("Limitations",
                 "Be upfront. Epsilon is record-level. Federated learning is simulated in one process rather than run over Kafka. There is "
                 "no attack evaluation beyond one simple membership inference check. Labels are injected, so absolute accuracy is not clinical. "
                 "The model is a simple linear model. Thresholds are tuned on labelled data.")
    dk.bullets(s, ["**Record-level DP**, not patient-level",
                   "**FL simulated** in-process (a Kafka-topic demo reproduces it)",
                   "Only a simple membership-inference check (no stronger attacks)",
                   "**Semi-synthetic labels**: injected episodes, not clinical truth",
                   "Simple linear model; thresholds tuned on labelled data",
                   "Small public demo; 5 seeds → wide intervals"], 0.8, 1.7, 11.8, 5.2, size=26)
