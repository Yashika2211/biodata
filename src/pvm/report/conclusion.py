"""Report section: conclusion."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
    doc.h("6  Conclusion", 1)
    c = []
    for ds in D:
        h = H[ds]
        c.append(f"{DS_NAME[ds]}: {h['fa_cut_C_vs_A2']*100:.0f}% fewer false alarms from an adaptive threshold alone, and "
                 f"federated vs centralised F1 {ci(h['F_D']['f1'])}")
    doc.p("Per-patient adaptive thresholds reduce false alarms substantially compared with one fixed threshold, and a "
          "federated model trained on adaptive features matched the centralised model within our statistical resolution "
          "while raw data stayed local (" + "; ".join(c) + "). Record-level differential privacy was nearly free at moderate noise and "
          "degraded accuracy only at large noise. The pipeline sustains the needed rates with end-to-end latency of about a second at 1000 events/s "
          "(batch processing plus trigger wait), and sending only alerts and model updates cuts the bytes leaving the site by orders of magnitude. "
          "These conclusions hold for injected-label benchmarks and a simple model; prospective validation on real "
          "annotated alarms and a patient-level privacy analysis are the necessary next steps.")
