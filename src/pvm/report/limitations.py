"""Report section: limitations."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
    doc.h("5  Limitations", 1)
    doc.bullets([
        "**Record-level, not patient-level DP.** ε bounds one training row; patients contribute hundreds of correlated rows, so patient-level privacy is much weaker. Standardisation moments, class counts and threshold-tuning count tables are shared without noise.",
        "**FL is simulated, not run over Kafka.** Sites are simulated in one process (no network, stragglers or dropouts); only inference runs over Kafka. Communication bytes for FL are computed analytically (rounds × sites × 2 × parameters × 8 B).",
        "**No real attack evaluation.** We ran only a simple loss-threshold membership-inference check; it finds nothing, which does not show that stronger attacks (gradient inversion, attribute inference) fail.",
        "**Semi-synthetic labels.** Episodes are injected with hand-chosen shapes and magnitudes; absolute F1/recall are not clinical performance, and methods that model the injection well are favoured. eICU invasive SBP and temperature are mostly missing, so deteriorations are mainly visible through HR, SpO2 and RR.",
        "**Simple linear model.** A 16-parameter logistic regression is explainable but cannot capture interactions or trends; conclusions about FL/DP may not transfer to deep models.",
        "**Thresholds are tuned on labelled data** (first 60 %), which real deployments lack; the count-table protocol makes tuning federated but still needs labels.",
        "**Small public sample.** The eICU demo has a few hundred eligible stays; confidence intervals use 5 seeds and are wide. Seeds resample the same underlying real stays, so they are not independent patients.",
        "**Latency benchmarks** ran on one laptop with a single broker per cluster and Spark local mode; absolute numbers will differ in production, and per-event alerts (\"emit-all\") were enabled only to measure latency.",
    ])
