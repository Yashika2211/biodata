"""Report section: method."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
    doc.h("2  Method", 1)
    doc.h("2.1  Architecture", 2)
    doc.p("Two independent single-node Kafka clusters (KRaft mode, `apache/kafka`) are run by Docker Compose. "
          "`kafka-site` (port 9092) holds raw vitals in `vitals.raw.<site>` with one-hour retention; "
          "`kafka-central` (port 9093) receives only alerts. A producer replays the dataset as JSON and stamps a "
          "producer timestamp. A PySpark 3.5 Structured Streaming job reads the site cluster, keeps per-patient state "
          "with `applyInPandasWithState` (state serialised as JSON), scores each event and writes alerts to "
          "`alerts.central`. An alert contains only a salted-hash patient id, the site, the timestamp, the score and a "
          "model tag — never vital values. A consumer on the central cluster measures end-to-end latency.")
    doc.figure("docs/architecture.png", "System architecture. Raw vitals stay inside the site boundary; only alerts, "
               "model updates and aggregate count tables cross it.", 16.0)
    doc.p("**One shared code path.** A small Python package (`pvm.features`) extracts features for offline training, "
          "offline evaluation, a Kafka-free local runner and the Spark job. A unit test proves that serving scores equal "
          "offline scores bit-for-bit, including when the per-patient state is serialised to JSON between micro-batches.")
    doc.h("2.2  Per-patient adaptive baseline", 2)
    doc.p("For each vital v of each patient we keep an exponentially weighted mean μ and variance σ². A new sample x is "
          "first scored, then used to update the state: z = (x − μ) / max(σ, s_min), where s_min is a per-vital "
          "minimum scale. The update uses (i) a winsorised value x′ = clip(x, μ ± 3σ), (ii) the rate "
          f"λ = max(α, 1/(n + k₀)) with α = {P['alpha']} per sample and a population-prior pseudo-count k₀ = 12 for cold "
          "start, and (iii) a ten-fold slower rate while |z| > 2.5, so a deterioration is not absorbed into the baseline "
          "it is judged against. Missing or implausible values give NaN, which means \"no evidence\": they do not update "
          "the state and contribute zero to the model features.")
    doc.h("2.3  Features, model and alarm rule", 2)
    doc.p(f"For each vital we use the current z, the mean z and the max |z| over a window of {P['window']} samples "
          f"(30 minutes), giving {P['features']} features. The model is a class-weighted L2 logistic regression on "
          "standardised features; class weights and standardisation use aggregate counts and moments only. An **alarm "
          f"event** fires when the score exceeds a threshold for m = {P['persistence_m']} consecutive samples; while the "
          "condition persists the alarm re-fires hourly, so an always-on alarm cannot hide as one event. An alarm firing "
          f"within an episode padded by {P['tolerance_min']} minutes is a true positive; otherwise it is a false alarm.")
    doc.h("2.4  Compared methods", 2)
    doc.table(["Method", "Description"], [
        ["A", "Static ward thresholds (HR 50–120, SpO2 ≥ 92, RR 10–24, SBP ≥ 90, T 35.5–38.5), instant alarm"],
        ["A2", "Static thresholds + persistence (m = 3)"],
        ["B", "Centralised baseline: ML on features normalised with fixed population priors, raw data pooled"],
        ["C", "Per-patient adaptive threshold, no learning: max |z| over vitals, one tuned threshold"],
        ["D", "Centralised ML on adaptive features"],
        ["E", "Local-only training per site (no sharing)"],
        ["F", "Federated (FedAvg) on adaptive features, full participation, non-IID sites"],
        ["G", "F + differential privacy (per-record clipping, Gaussian noise, Rényi-DP accountant, δ = 1e-5)"],
    ], "The eight compared methods.", widths=[1.6, 14.4])
    doc.h("2.5  Privacy mechanisms", 2)
    doc.p("(i) **Data minimisation:** only salted-hash alerts leave the site; raw vitals expire after one hour on the site "
          "broker. (ii) **FedAvg:** each round a site receives the global weights, runs three local gradient steps on its "
          "own data and returns its weights; the server averages them weighted by record count. (iii) **DP-SGD at each "
          f"site:** every local step samples a Poisson batch (rate q = {P['dp_sampling_rate']}), clips each per-record "
          f"gradient to L2 norm ≤ {P['dp_clip']:g}, adds Gaussian noise N(0, (σ·clip)²) and divides by the expected batch "
          "size. A Rényi-DP accountant for the subsampled Gaussian mechanism (integer-order expansion of Mironov et al., "
          "converted with the tighter bound of Balle et al.) reports ε at δ = 1e-5. **ε is record-level**: it bounds the "
          "influence of one training row (one patient-time-step), not of one patient, who contributes hundreds of "
          "correlated rows. (iv) **Threshold tuning** uses only per-site aggregate count tables (alarms, true positives, "
          "episodes, detected, patient-days over a fixed threshold grid), so it also works without pooling data.")
