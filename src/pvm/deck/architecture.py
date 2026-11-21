"""Slide: architecture."""
from __future__ import annotations

import os

from pptx.util import Inches

from ..docs_common import DS_NAME, ci, eps_str, fmt_bytes
from .helpers import BLUE, GREEN, GREY, LIGHT, MSO_SHAPE, NAVY, ORANGE, PP_ALIGN, Pt, RGBColor, W, Hh


def add(dk, ctx):
    S, D, H, first, syn = ctx.S, ctx.D, ctx.H, ctx.first, ctx.syn
    s = dk.slide("Architecture: raw vitals stay at the site",
                 "Two single-node Kafka clusters in KRaft mode. kafka-site holds raw vitals with one hour retention. A PySpark 3.5 "
                 "Structured Streaming job keeps per-patient state with applyInPandasWithState, serialised as JSON, and writes only "
                 "alerts to kafka-central: a salted-hash patient id, site, timestamp, score and a model tag. The same Python feature code "
                 "is used by training, evaluation, a Kafka-free runner and the Spark job, and a unit test proves serving equals offline "
                 "exactly. Federated rounds are simulated in-process; that is a stated limitation.")
    dk.image(s, "docs/architecture.png", 0.6, 1.55, w=12.1)
    dk.text(s, "Alerts carry no vitals  ·  one shared feature code path  ·  FL experiments simulated (Kafka demo exists)",
            0.7, 6.75, 12, 0.5, size=16, color=GREY)
