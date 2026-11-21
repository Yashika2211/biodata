"""Generate report.docx (and PDF via LibreOffice) from results/summary.json."""
from __future__ import annotations

import datetime
import os
import subprocess

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import costs as CO
from .docs_common import (DS_NAME, METHOD_NAME, ci, eps_str, fmt_bytes, headlines, load, num, pm)

AUTHOR = "Yashika Bhatia"
TITLE = "Privacy-Preserving Patient Vitals Monitoring: A Kafka + Spark Streaming Study"


def verdict(p, higher_better=True):
    """Describe a paired difference by its 95% CI."""
    if p.get("ci95") is None:
        return "is not estimable"
    lo, hi = p["ci95"]
    if lo <= 0 <= hi:
        return "is statistically indistinguishable from"
    good = (p["mean"] > 0) == higher_better
    return "is significantly better than" if good else "is significantly worse than"


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


class Doc:
    def __init__(self):
        self.d = Document()
        s = self.d.sections[0]
        s.page_width, s.page_height = Cm(21.0), Cm(29.7)
        s.left_margin = s.right_margin = Cm(2.1)
        s.top_margin = s.bottom_margin = Cm(2.0)
        st = self.d.styles["Normal"]
        st.font.name = "Calibri"; st.font.size = Pt(10.5)
        st.paragraph_format.space_after = Pt(5)
        st.paragraph_format.line_spacing = 1.08
        for name, size in (("Heading 1", 15), ("Heading 2", 12.5), ("Heading 3", 11)):
            h = self.d.styles[name]
            h.font.name = "Calibri"; h.font.size = Pt(size); h.font.bold = True
            h.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
            h.paragraph_format.space_before = Pt(10 if name != "Heading 1" else 14)
            h.paragraph_format.space_after = Pt(4)
        self.fig_n = 0
        self.tab_n = 0

    def h(self, text, lvl=1):
        return self.d.add_heading(text, lvl)

    def p(self, text="", bold=False, italic=False, size=None, align=None, after=None):
        para = self.d.add_paragraph()
        self._runs(para, text, bold, italic, size)
        if align == "center":
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if after is not None:
            para.paragraph_format.space_after = Pt(after)
        return para

    def _runs(self, para, text, bold=False, italic=False, size=None):
        parts = text.split("**")
        for i, t in enumerate(parts):
            if not t:
                continue
            r = para.add_run(t)
            r.bold = bold or (i % 2 == 1)
            r.italic = italic
            if size:
                r.font.size = Pt(size)

    def bullets(self, items):
        for t in items:
            para = self.d.add_paragraph(style="List Bullet")
            self._runs(para, t)
            para.paragraph_format.space_after = Pt(2)

    def figure(self, path, caption, width=16.0):
        if not path or not os.path.exists(path):
            return
        self.fig_n += 1
        self.d.add_picture(path, width=Cm(width))
        self.d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c = self.p(f"Figure {self.fig_n}. {caption}", italic=True, size=9, align="center", after=8)
        return c

    def table(self, header, rows, caption, widths=None, size=8.5, bold_rows=()):
        self.tab_n += 1
        self.p(f"Table {self.tab_n}. {caption}", italic=True, size=9, after=2)
        t = self.d.add_table(rows=1, cols=len(header))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, htxt in enumerate(header):
            c = t.rows[0].cells[i]
            c.text = ""
            r = c.paragraphs[0].add_run(htxt); r.bold = True; r.font.size = Pt(size)
            shade(c, "DCE6F1")
        for ri, row in enumerate(rows):
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(size)
                r.bold = ri in bold_rows
                if i > 0:
                    cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Cm(w)
        for row in t.rows:
            for c in row.cells:
                for para in c.paragraphs:
                    para.paragraph_format.space_after = Pt(0)
        self.d.add_paragraph().paragraph_format.space_after = Pt(2)
        return t

    def save(self, path):
        self.d.save(path)


def accuracy_rows(d):
    rows = []
    keys = ["A", "A2", "B", "C", "D", "E", "F"] + [f"G@{s:g}" for s in sorted(r["sigma"] for r in d["privacy_utility"])]
    for k in keys:
        m = d["methods"][k]
        name = METHOD_NAME.get(k) or f"G  FL + DP, σ={k[2:]} (ε={eps_str(m['epsilon']['mean'])})"
        rows.append([name, pm(m["precision"]), pm(m["recall"]), pm(m["f1"]), pm(m["fa_per_day"]),
                     pm(m["delay_min"], 0), pm(m["auroc"]), pm(m["auprc"])])
    return rows


def build(summary_path="results/summary.json", out="dist/report/report.docx"):
    S = load(summary_path)
    D = S["datasets"]
    syn, eic = D.get("synthetic"), D.get("eicu")
    H = {k: headlines(S, k) for k in D}
    P = S["protocol"]
    doc = Doc()
    os.makedirs(os.path.dirname(out), exist_ok=True)

    # ------------------------------------------------------------------ title
    doc.p(TITLE, bold=True, size=19, align="center", after=2)
    doc.p(f"{AUTHOR}  ·  Big Data course project  ·  {datetime.date.today():%d %B %Y}", size=10.5,
          align="center", after=10)

    # --------------------------------------------------------------- abstract
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

    # ------------------------------------------------------------- 1 problem
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

    # --------------------------------------------------------------- 2 method
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

    # ----------------------------------------------------------------- 3 setup
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

    # ---------------------------------------------------------------- 4 results
    doc.h("4  Results", 1)
    doc.h("4.1  Accuracy", 2)
    for ds in D:
        d = D[ds]
        doc.table(["Method", "Precision", "Recall", "F1", "False alarms / pt-day", "Delay (min)", "AUROC", "AUPRC"],
                  accuracy_rows(d), f"Held-out accuracy — {DS_NAME[ds]} (mean ± sd, {d['n_seeds']} seeds). "
                  "Alarms: m = 3 except A.", widths=[4.9, 1.7, 1.7, 1.7, 2.0, 1.4, 1.6, 1.6], size=7.5)
        doc.figure(f"figures/fig_accuracy_{ds}.png", f"F1 and false alarms per patient-day — {DS_NAME[ds]}.", 15.0)
    for ds in D:
        h, d = H[ds], D[ds]
        pr = d["paired"]
        doc.p(f"**{DS_SHORT[ds] if ds=='eicu' else 'Synthetic'}.** "
              f"RQ1: the adaptive threshold (C) cuts false alarms from {h['fa_A2']:.2f} (A2) to {h['fa_C']:.2f} per "
              f"patient-day ({h['fa_cut_C_vs_A2']*100:.0f}% fewer) and its F1 {verdict(pr['C_minus_A2']['f1'])} A2 "
              f"({ci(pr['C_minus_A2']['f1'])}). Learning on top of adaptive features (D) gives F1 {h['f1']['D']:.2f}. "
              f"Comparing D with B (same model, fixed-prior normalisation) isolates the adaptive features: AUROC "
              f"{ci(h['D_B']['auroc'])}, AUPRC {ci(h['D_B']['auprc'])}, F1 {ci(h['D_B']['f1'])} — the adaptive features "
              f"{verdict(h['D_B']['auprc'])} B on AUPRC and {verdict(h['D_B']['f1'])} B on F1 at the tuned operating point.")
    doc.h("4.2  Federated vs centralised (RQ2)", 2)
    for ds in D:
        h = H[ds]
        doc.p(f"{DS_NAME[ds]}: F vs D, F1 {ci(h['F_D']['f1'])}, AUROC {ci(h['F_D']['auroc'])}, AUPRC "
              f"{ci(h['F_D']['auprc'])}; F vs the fixed-prior baseline B: F1 {ci(h['F_B']['f1'])}. "
              f"FedAvg reached within 0.1% of the centralised training loss after {h['rounds_conv']:.0f} rounds on average "
              f"(we ran {h['rounds_used']}; final loss gap {h['loss_gap']:.1e}). "
              f"Local-only training (E) had F1 {D[ds]['methods']['E']['f1']['mean']:.2f} versus "
              f"{D[ds]['methods']['F']['f1']['mean']:.2f} for F ({ci(D[ds]['paired']['F_minus_E']['f1'])}).")
    doc.figure("figures/fig_fl_convergence.png", "Federated training loss relative to the centralised optimum (seed 0). "
               "The \"rounds to converge\" diagnostic uses the centralised optimum, which a real deployment would not know; "
               "we used it only to choose and report the number of rounds.", 10.0)
    doc.h("4.3  Privacy–utility (RQ3)", 2)
    for ds in D:
        doc.figure(f"figures/fig_privacy_utility_{ds}.png", f"Privacy–utility curve — {DS_NAME[ds]}. ε is record-level.", 15.5)
    for ds in D:
        h = H[ds]
        k, fl = h["dp_keep"], h["dp_first_loss"]
        txt = f"{DS_NAME[ds]}: "
        if k:
            txt += (f"noise up to σ = {k['sigma']:g} (record-level ε = {eps_str(k['epsilon'])}) did not measurably reduce F1 "
                    f"relative to non-private FedAvg. ")
        if fl:
            txt += (f"A clear loss appears at σ = {fl['sigma']:g} (ε = {eps_str(fl['epsilon'])}), where F1 falls to "
                    f"{fl['f1']['mean']:.2f}. ")
        doc.p(txt + "Small ε at moderate noise is possible because each site holds tens of thousands of rows and the "
              "per-step sampling rate is small; this is **record-level** privacy only. A patient contributes hundreds of "
              "correlated rows, so patient-level protection is far weaker than these ε values suggest.")
    mia = {ds: D[ds].get("mia_auroc") for ds in D}
    rows = []
    for ds in D:
        for n, v in (mia[ds] or {}).items():
            rows.append([DS_NAME[ds], n, pm(v, 3)])
    if rows:
        doc.table(["Dataset", "Model attacked", "Membership-inference AUROC"], rows,
                  "Simple loss-threshold membership inference at the patient level (members = rows of training patients; "
                  "non-members = same time range of held-out patients). 0.5 means no leakage detected.",
                  widths=[5.5, 5.5, 5.0])
        doc.p("The attack is weak by design (a single loss threshold against a 16-parameter linear model) and finds no "
              "measurable leakage even for the non-private models; this is a sanity check, not a privacy proof.")
    doc.h("4.4  Latency, throughput and cost (RQ4)", 2)
    lat = S["latency"]
    ip = lat.get("inprocess")
    if ip:
        doc.p(f"**In-process serving** (one event through `serving.step`, {ip['n_events']:,} events): per-event latency "
              f"p50/p95/p99 = {ip['step_us']['p50']:.1f}/{ip['step_us']['p95']:.1f}/{ip['step_us']['p99']:.1f} µs "
              f"({ip['throughput_eps']:,.0f} events/s on one core); with JSON state (de)serialisation on every event "
              f"{ip['step_json_state_us']['p50']:.0f}/{ip['step_json_state_us']['p95']:.0f}/{ip['step_json_state_us']['p99']:.0f} µs; "
              f"{ip['cpu_seconds_per_million_events']:.1f} CPU-seconds per million events.")
    k = lat.get("kafka")
    if k:
        rows = []
        for r in k["runs"]:
            l = r["latency_ms"]
            rows.append([r["trigger"], "max" if r["target_rate"] == 0 else f"{r['target_rate']:g}",
                         f"{r['received']:,}", f"{l['p50']:.0f}", f"{l['p95']:.0f}", f"{l['p99']:.0f}",
                         f"{r['throughput_eps']:,.0f}" if r.get("throughput_eps") else "n/a",
                         f"{r['cpu_seconds_per_million_events']:.0f}" if r.get("cpu_seconds_per_million_events") else "–"])
        doc.table(["Trigger", "Target events/s", "Events", "p50 (ms)", "p95 (ms)", "p99 (ms)", "Throughput (ev/s)",
                   "CPU-s / 1M ev"], rows,
                  "Real end-to-end Kafka → Spark → Kafka latency measured by the alert consumer (producer timestamp to "
                  "consumer receipt; Spark local[2]; one broker per cluster in Docker on a laptop; synthetic replay). "
                  "The \"max\" rows are backlog bursts (producer unthrottled), so their latency reflects queueing, and CPU-s per million events is reported only there (saturated).",
                  widths=[2.6, 2.0, 1.5, 1.5, 1.5, 1.5, 2.4, 2.0], size=8)
        doc.figure("figures/fig_latency.png", "End-to-end latency by trigger interval and event rate; maximum throughput.", 16.0)
        doc.p("Latency is dominated by the micro-batch trigger interval (a micro-batch engine waits for the trigger), "
              "so p50 tracks the trigger rather than per-event compute, which is microseconds. For 5-minute vitals "
              "even a 5-second trigger is negligible clinically; the shorter triggers matter only if the source rate is high.")
    cost = S.get("cost") or {}
    if cost:
        cs_ = next(iter(cost.values()))
        sc = cs_["scenario"]
        rows = []
        for ds, v in cost.items():
            rows.append([DS_NAME[ds], fmt_bytes(v["raw_stream_bytes"]), fmt_bytes(v["alert_bytes"]),
                         fmt_bytes(v["model_update_bytes"] + v["count_table_bytes"]), fmt_bytes(v["federated_bytes"]),
                         f"{v['reduction_factor']:,.0f}×", f"${v['egress_usd_raw']:.2f}", f"${v['egress_usd_federated']:.4f}",
                         f"${v['scoring_usd']:.3f}"])
        doc.table(["Dataset (alarm volume)", "Raw streaming", "Alerts", "Model upd. + counts", "Federated total",
                   "Reduction", "Egress $ raw", "Egress $ fed.", "Scoring $"], rows,
                  f"Bytes leaving the site per month for {sc['patients']} patients, one sample per {sc['sample_minutes']:g} min "
                  f"(measured bytes per event/alert and measured alarm volume; model updates = {sc['fl_rounds']} rounds × 4 sites "
                  "× 2 × 16 float64). Dollar figures are illustrative.", widths=[3.6, 1.7, 1.4, 1.9, 1.8, 1.6, 1.5, 1.5, 1.4], size=7.5)
        doc.figure("figures/fig_cost.png", "Bytes leaving the site per month (log scale), eICU-rate scenario.", 11.0)
        pr = cs_["prices"]
        doc.table(["Assumed price (illustrative, not measured)", "Value"],
                  [["Data egress", f"${pr['egress_usd_per_gb']}/GB"], ["vCPU", f"${pr['vcpu_usd_per_hour']}/vCPU-hour"],
                   ["Object storage (not used in totals)", f"${pr['storage_usd_per_gb_month']}/GB-month"]],
                  "All assumed prices, defined once in `pvm/costs.py`.", widths=[10.0, 6.0])
        tr = [ (ds, D[ds]["methods"]["D"]["train_seconds"], D[ds]["methods"]["F"]["train_seconds"]) for ds in D]
        doc.p("**Training time (CPU-seconds, simulation on one machine):** " + "; ".join(
            f"{DS_NAME[ds]}: centralised L-BFGS {a['mean']:.2f}s, FedAvg ({H[ds]['rounds_used']} rounds, 4 sites simulated "
            f"sequentially) {b['mean']:.1f}s" for ds, a, b in tr) +
            ". Federated training is slower in CPU terms because it iterates; its benefit is not compute but that raw rows stay put.")
    doc.h("4.5  Ablations", 2)
    for ds in D:
        doc.figure(f"figures/fig_ablations_{ds}.png", f"Ablations — {DS_NAME[ds]}: adaptation rate α, persistence m, DP clip, "
                   "number of sites, number of FL rounds.", 16.0)
    for ds in D:
        A = D[ds].get("ablations")
        if not A:
            continue
        a_best = min(A["alpha"], key=lambda a: -A["alpha"][a]["D"]["f1"]["mean"])
        doc.p(f"{DS_NAME[ds]}: slower adaptation (smaller α) gave the highest F1 for the ML model at α = {a_best} "
              f"(F1 {A['alpha'][a_best]['D']['f1']['mean']:.2f}); our default α = {P['alpha']} was fixed beforehand and was "
              f"not tuned on held-out results. Larger persistence m trades delay for fewer false alarms in all methods. "
              f"Local-only models (E) do not improve with more sites, whereas federated (F) tracks centralised (D) as sites are added.")

    # -------------------------------------------------------------- 5 limitations
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

    # ------------------------------------------------------------- 6 conclusion
    doc.h("6  Conclusion", 1)
    c = []
    for ds in D:
        h = H[ds]
        c.append(f"{DS_NAME[ds]}: {h['fa_cut_C_vs_A2']*100:.0f}% fewer false alarms from an adaptive threshold alone, and "
                 f"federated vs centralised F1 {ci(h['F_D']['f1'])}")
    doc.p("Per-patient adaptive thresholds reduce false alarms substantially compared with one fixed threshold, and a "
          "federated model trained on adaptive features matched the centralised model within our statistical resolution "
          "while raw data stayed local (" + "; ".join(c) + "). Record-level differential privacy was nearly free at moderate noise and "
          "degraded accuracy only at large noise. The pipeline sustains the needed rates with latency dominated by the "
          "trigger interval, and sending only alerts and model updates cuts the bytes leaving the site by orders of magnitude. "
          "These conclusions hold for injected-label benchmarks and a simple model; prospective validation on real "
          "annotated alarms and a patient-level privacy analysis are the necessary next steps.")

    # ------------------------------------------------------------ 7 reproducibility
    doc.h("7  Reproducibility", 1)
    doc.p("Code: `code.zip` / the project repository. `make test` (unit tests), `make up` (two Kafka clusters), "
          "`make data` (download the open eICU demo), `make experiments` (both datasets, 5 seeds, ablations, benchmarks, "
          "`results/summary.json`), `make figures`, `make docs` (this report and the deck are generated from "
          "`results/summary.json`; no result is typed by hand). Environment: Python 3.11, Java 17, PySpark 3.5.3, pandas 2.2, "
          "`apache/kafka` 3.8.0. Seeds 0–4. Data are not redistributed; see `data/README.md`.")

    # --------------------------------------------------------------- references
    doc.h("References", 1)
    for r in [
        "McMahan, H. B., Moore, E., Ramage, D., Hampson, S., Agüera y Arcas, B. (2017). Communication-Efficient Learning of Deep Networks from Decentralized Data. AISTATS.",
        "Abadi, M., Chu, A., Goodfellow, I., McMahan, H. B., Mironov, I., Talwar, K., Zhang, L. (2016). Deep Learning with Differential Privacy. ACM CCS.",
        "Mironov, I. (2017). Rényi Differential Privacy. IEEE Computer Security Foundations Symposium.",
        "Armbrust, M., Das, T., Torres, J., Yavuz, B., Zhu, S., Xin, R., Ghodsi, A., Stoica, I., Zaharia, M. (2018). Structured Streaming: A Declarative API for Real-Time Applications in Apache Spark. ACM SIGMOD.",
        "Kreps, J., Narkhede, N., Rao, J. (2011). Kafka: a Distributed Messaging System for Log Processing. NetDB Workshop.",
        "Pollard, T. J., Johnson, A. E. W., Raffa, J. D., Celi, L. A., Mark, R. G., Badawi, O. (2018). The eICU Collaborative Research Database, a freely available multi-center database for critical care research. Scientific Data 5, 180178.",
    ]:
        para = doc.d.add_paragraph(r, style="List Number")
        para.paragraph_format.space_after = Pt(2)
        for run in para.runs:
            run.font.size = Pt(9.5)
    doc.save(out)
    return out


def to_pdf(docx_path):
    outdir = os.path.dirname(docx_path)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path],
                   check=True, capture_output=True, timeout=180)
    return docx_path.replace(".docx", ".pdf")


def main():
    p = build()
    try:
        print(to_pdf(p))
    except Exception as e:                                     # LibreOffice is optional
        print("PDF conversion skipped:", e)


if __name__ == "__main__":
    main()
