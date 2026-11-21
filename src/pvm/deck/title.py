"""Slide: title."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    s = dk.slide(None, "Introduce the project in one sentence: we stream patient vitals, flag anomalies instantly, "
                 "and ask whether we can keep accuracy while raw data stays at the hospital. Three things to remember: "
                 "adaptive thresholds cut false alarms; federated learning matches centralised; privacy noise is cheap until it is large.")
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Hh); bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
    dk.text(s, "Privacy-Preserving Patient Vitals Monitoring", 0.8, 2.0, 11.8, 1.4, size=44, bold=True, color=RGBColor(255, 255, 255))
    dk.text(s, "A Kafka + Spark Streaming study", 0.8, 3.35, 11.8, 0.8, size=28, color=RGBColor(0xBF, 0xDB, 0xEE))
    dk.text(s, "Yashika Bhatia  ·  Big Data course project", 0.8, 5.3, 11.8, 0.6, size=20, color=RGBColor(255, 255, 255))
    dk.text(s, "Can the system match baseline accuracy while raw data stays local?", 0.8, 4.3, 11.8, 0.7, size=22,
            color=RGBColor(0xFF, 0xC8, 0x8A))
