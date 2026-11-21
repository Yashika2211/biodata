"""Report section: setup."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
    doc.h("3  Experimental setup", 1)
    doc.h("3.1  Datasets and the semi-synthetic protocol", 2)
    cs, ce = (syn["cohort"] if syn else None), (eic["cohort"] if eic else None)
    doc.p("**Public dataset.** The eICU Collaborative Research Database demo (`vitalPeriodic`: heartrate, sao2, "
          "respiration, systemicsystolic, temperature; column names verified on the downloaded file). Vitals are stored "
          "every 5 minutes, so the sampling interval is a parameter and false alarms, tolerances and delays are in real "
          "time units. Sites are groups of hospitals (`hospitalid`), a naturally non-IID split. Invasive systolic BP "
          "and temperature are sparse in this table (mostly missing), so most signal comes from HR, SpO2 and RR; missing "
          "values are \"no evidence\". "
          + (f"Each seed resamples 85 % of {ce['patients']['mean']:.0f} eligible stays and draws fresh episodes." if ce else ""))
    doc.p("**Synthetic cohort.** A generator with six phenotypes (normal, athlete, COPD, hypertensive, tachycardic, "
          "low-BP), per-site phenotype mixes drawn from a Dirichlet distribution (non-IID), AR(1) noise, circadian drift, "
          "missing values and probe-off bursts, and benign motion artefacts of 1–8 samples labelled normal "
          "(long enough that persistence does not trivially remove them). "
          + (f"Each seed is a fresh cohort of {cs['patients']['mean']:.0f} patients over 4 days and 4 sites." if cs else ""))
    doc.p("**Labels.** Public vitals have no independent ground-truth anomaly label, so we use the standard semi-synthetic "
          "protocol: real (or simulated) physiology plus injected, labelled deterioration episodes (sepsis-like, hypoxia, "
          "shock, bradycardia/hypotension; 1.5–6 h; ramped onset). No episode crosses the train/test split. "
          "**Results are therefore on injected labels and are not clinical performance.** Every table and figure is "
          "labelled with its dataset; synthetic results are never presented as results on the public dataset.")
    doc.h("3.2  Protocol and metrics", 2)
    doc.p(f"The first 60 % of each patient's series is used for training and threshold tuning; the last 40 % is held out. "
          f"Alarm-level metrics: precision, recall, F1, false alarms per patient-day and median detection delay in minutes. "
          f"Sample-level: AUROC and AUPRC. All numbers are mean ± sd over 5 seeds (fresh cohort or resample each); paired "
          f"differences use per-seed differences with a t-based 95% CI (n = 5, so intervals are wide). Ablations use "
          f"{(syn or eic)['ablations']['alpha']['0.02']['D']['f1']['n']} seeds.")
