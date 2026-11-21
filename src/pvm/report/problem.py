"""Report section: problem."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
    doc.h("1  Problem and research question", 1)
    doc.p("Alarm fatigue is a well-known hazard in intensive and ward care: a single threshold such as \"SpO2 < 92 %\" "
          "alarms continuously for a patient whose healthy baseline is 90 % (for example, chronic obstructive pulmonary "
          "disease), and clinicians learn to ignore alarms. Learning a per-patient baseline fixes this but needs "
          "state per patient and, if models are trained across hospitals, raises the question of moving sensitive "
          "raw data. We study four questions:")
    doc.bullets([
        "**RQ1 (novel angle).** Do per-patient adaptive thresholds cut false alarms compared with one fixed threshold for everyone?",
        "**RQ2 (privacy twist).** Can a model trained federated (FedAvg, raw data stays at the site) match a centralised baseline?",
        "**RQ3.** What does record-level differential privacy cost in accuracy?",
        "**RQ4.** What are the latency, throughput and cost of the streaming pipeline, and how many bytes leave the site?",
    ])
