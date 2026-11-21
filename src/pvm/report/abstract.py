"""Report section: abstract."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
    doc.h("Abstract", 1)
    parts = []
    for ds in D:
        h = H[ds]
        parts.append(
            f"On the {DS_NAME[ds]}, per-patient adaptive thresholds cut false alarms from "
            f"{h['fa_A2']:.1f} to {h['fa_C']:.1f} per patient-day ({h['fa_cut_C_vs_A2']*100:.0f}% fewer) against static "
            f"ward thresholds with persistence, and a model on adaptive features reaches F1 {h['f1']['D']:.2f} "
            f"(static baselines: {h['f1']['A2']:.2f}). Federated training (FedAvg, no raw data shared) reached the "
            f"centralised optimum after about {h['rounds_conv']:.0f} rounds, with an F1 difference to the centralised "
            f"model of {ci(h['F_D']['f1'])} (mean [95% CI] over {D[ds]['n_seeds']} seeds).")
    doc.p("Hospital monitors raise too many false alarms because one fixed threshold is applied to every patient, "
          "and centralising raw vitals to fix this creates privacy and bandwidth problems. We build a real streaming "
          "pipeline (two Kafka KRaft clusters, Spark Structured Streaming with per-patient state) that scores vitals "
          "(heart rate, SpO2, respiratory rate, systolic BP, temperature) with a per-patient adaptive baseline, and ask: "
          "**can the system match baseline accuracy while raw data stays local?** " + " ".join(parts) +
          " Differential privacy (record-level) costs little accuracy until the noise becomes large (Section 4.4). "
          "Labels are semi-synthetic (real or simulated physiology plus injected, labelled deterioration episodes), "
          "so absolute numbers are not clinical performance.")
