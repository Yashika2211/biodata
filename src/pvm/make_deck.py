"""Generate the 12-slide deck (with speaker notes) from results/summary.json."""
from __future__ import annotations

import os
import subprocess

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from .docs_common import DS_NAME, ci, eps_str, fmt_bytes, headlines, load

NAVY = RGBColor(0x1F, 0x3A, 0x5F)
BLUE = RGBColor(0x00, 0x72, 0xB2)
ORANGE = RGBColor(0xD5, 0x5E, 0x00)
GREEN = RGBColor(0x00, 0x9E, 0x73)
GREY = RGBColor(0x55, 0x55, 0x55)
LIGHT = RGBColor(0xEE, 0xF3, 0xF8)
W, Hh = Inches(13.333), Inches(7.5)


class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, Hh
        self.blank = self.prs.slide_layouts[6]

    def slide(self, title, notes, tag=None, number=True):
        s = self.prs.slides.add_slide(self.blank)
        if title:
            self.text(s, title, 0.6, 0.35, 12.1, 0.9, size=32, bold=True, color=NAVY)
            bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.22), Inches(1.2), Inches(0.07))
            bar.fill.solid(); bar.fill.fore_color.rgb = BLUE; bar.line.fill.background()
        if tag:
            pill = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.1), Inches(0.42), Inches(4.7), Inches(0.5))
            pill.fill.solid(); pill.fill.fore_color.rgb = LIGHT; pill.line.color.rgb = BLUE
            tf = pill.text_frame; tf.margin_left = tf.margin_right = Inches(0.08)
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
            r = p.add_run(); r.text = f"Dataset: {tag}"; r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = BLUE
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        s.notes_slide.notes_text_frame.text = notes
        return s

    def text(self, s, text, x, y, w, h, size=20, bold=False, color=GREY, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
        lines = text if isinstance(text, list) else [text]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            parts = line.split("**")
            for j, t in enumerate(parts):
                if not t:
                    continue
                r = p.add_run(); r.text = t
                r.font.size = Pt(size); r.font.bold = bold or (j % 2 == 1); r.font.color.rgb = color
            p.space_after = Pt(10)
        return tb

    def bullets(self, s, items, x, y, w, h, size=22):
        return self.text(s, ["•  " + t for t in items], x, y, w, h, size=size, color=RGBColor(0x22, 0x22, 0x22))

    def image(self, s, path, x, y, w=None, h=None):
        if not os.path.exists(path):
            return None
        kw = {}
        if w: kw["width"] = Inches(w)
        if h: kw["height"] = Inches(h)
        return s.shapes.add_picture(path, Inches(x), Inches(y), **kw)

    def stat(self, s, big, small, x, y, w=3.0, color=BLUE):
        box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(1.55))
        box.fill.solid(); box.fill.fore_color.rgb = LIGHT; box.line.fill.background()
        self.text(s, big, x, y + 0.08, w, 0.8, size=34, bold=True, color=color, align=PP_ALIGN.CENTER)
        self.text(s, small, x + 0.1, y + 0.85, w - 0.2, 0.7, size=14, color=GREY, align=PP_ALIGN.CENTER)

    def save(self, path):
        self.prs.save(path)


def build(summary_path="results/summary.json", out="dist/ppt/deck.pptx"):
    S = load(summary_path)
    D = S["datasets"]
    H = {k: headlines(S, k) for k in D}
    dk = Deck()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    first = "eicu" if "eicu" in D else next(iter(D))
    syn = "synthetic" if "synthetic" in D else first

    # 1 title
    s = dk.slide(None, "Introduce the project in one sentence: we stream patient vitals, flag anomalies instantly, "
                 "and ask whether we can keep accuracy while raw data stays at the hospital. Three things to remember: "
                 "adaptive thresholds cut false alarms; federated learning matches centralised; privacy noise is cheap until it is large.")
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Hh); bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
    dk.text(s, "Privacy-Preserving Patient Vitals Monitoring", 0.8, 2.0, 11.8, 1.4, size=44, bold=True, color=RGBColor(255, 255, 255))
    dk.text(s, "A Kafka + Spark Streaming study", 0.8, 3.35, 11.8, 0.8, size=28, color=RGBColor(0xBF, 0xDB, 0xEE))
    dk.text(s, "Yashika Bhatia  ·  Big Data course project", 0.8, 5.3, 11.8, 0.6, size=20, color=RGBColor(255, 255, 255))
    dk.text(s, "Can the system match baseline accuracy while raw data stays local?", 0.8, 4.3, 11.8, 0.7, size=22,
            color=RGBColor(0xFF, 0xC8, 0x8A))

    # 2 problem
    h0 = H[first]
    s = dk.slide("One fixed threshold for every patient fails",
                 "Alarm fatigue: a single SpO2 < 92% rule alarms constantly for a patient whose healthy baseline is 90%, "
                 "for example chronic lung disease. Centralising raw vitals to learn better rules creates privacy and bandwidth "
                 "problems. Our research question is the one at the bottom. Labels in this study are semi-synthetic: real or simulated "
                 "physiology with injected, labelled deterioration episodes, so numbers are not clinical performance.")
    dk.bullets(s, ["Static ward thresholds → constant false alarms → **alarm fatigue**",
                   "Patients differ: athlete HR 52, COPD SpO2 90, hypertensive SBP 150",
                   "Pooling raw vitals centrally raises **privacy** and **bandwidth** problems"], 0.7, 1.7, 12, 3.2, size=26)
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(5.0), Inches(11.9), Inches(1.6))
    box.fill.solid(); box.fill.fore_color.rgb = LIGHT; box.line.color.rgb = BLUE
    dk.text(s, ["**Research question**", "Can we match baseline accuracy while raw data stays local (federated and/or private)?"],
            0.95, 5.1, 11.4, 1.4, size=24, color=NAVY)

    # 3 architecture
    s = dk.slide("Architecture: raw vitals stay at the site",
                 "Two single-node Kafka clusters in KRaft mode. kafka-site holds raw vitals with one hour retention. A PySpark 3.5 "
                 "Structured Streaming job keeps per-patient state with applyInPandasWithState, serialised as JSON, and writes only "
                 "alerts to kafka-central: a salted-hash patient id, site, timestamp, score and a model tag. The same Python feature code "
                 "is used by training, evaluation, a Kafka-free runner and the Spark job, and a unit test proves serving equals offline "
                 "exactly. Federated rounds are simulated in-process; that is a stated limitation.")
    dk.image(s, "docs/architecture.png", 0.6, 1.55, w=12.1)
    dk.text(s, "Alerts carry no vitals  ·  one shared feature code path  ·  FL is simulated (not over Kafka)",
            0.7, 6.75, 12, 0.5, size=16, color=GREY)

    # 4 adaptive idea
    ex = "figures/fig_adaptive_synthetic.png"
    s = dk.slide("Idea: judge each patient against their own baseline",
                 "This is the example the whole study is about. This patient has a normal SpO2 of about 90 percent. The fixed 92 percent "
                 "threshold, orange dots, alarms essentially all the time. The adaptive baseline, blue, learns the patient's normal "
                 "and alarms only on the injected deterioration, shaded, and a few motion artefacts. Mechanism: per-patient EWMA mean "
                 "and variance, winsorised updates, slower learning while abnormal, population priors for cold start, minimum-scale floors, "
                 "NaN means no evidence. A real eICU trace tells the same story; see the report.", tag="Synthetic cohort (COPD patient)")
    dk.image(s, ex, 0.55, 1.45, w=8.4)
    dk.bullets(s, ["**Fixed 92 %**: alarms all day", "**Adaptive**: learns this patient's ~90 %",
                   "Winsorised, slower while abnormal, prior for cold start"], 9.1, 1.8, 3.9, 4.8, size=20)

    # 5/6 accuracy
    for ds in ([syn] + ([first] if first != syn else [])):
        h = H[ds]; d = D[ds]; n = 5 if ds == syn else 6
        s = dk.slide(f"Accuracy: adaptive features beat fixed thresholds",
                     f"{DS_NAME[ds]}. Static thresholds A and A2 produce {h['fa_A']:.1f} and {h['fa_A2']:.1f} false alarms per patient-day. "
                     f"The adaptive threshold alone, method C, brings this to {h['fa_C']:.2f}. Machine learning on adaptive features, D, has F1 "
                     f"{h['f1']['D']:.2f}. Mean and standard deviation over {d['n_seeds']} seeds, last 40 percent of each series held out. "
                     f"B versus D isolates the adaptive features: AUPRC difference {ci(h['D_B']['auprc'])}, F1 difference {ci(h['D_B']['f1'])}. "
                     "Report both honestly: at the tuned operating point the F1 gain is within noise even though ranking quality (AUPRC) improves. "
                     "Labels are injected episodes.", tag=DS_NAME[ds])
        dk.image(s, f"figures/fig_accuracy_{ds}.png", 0.5, 1.45, w=8.6)
        dk.stat(s, f"−{h['fa_cut_C_vs_A2']*100:.0f}%", "false alarms: adaptive threshold vs static + persistence", 9.4, 1.5, 3.4, GREEN)
        dk.stat(s, f"{h['f1']['D']:.2f}", f"F1, ML on adaptive features (static: {h['f1']['A2']:.2f})", 9.4, 3.2, 3.4, BLUE)
        dk.stat(s, f"{h['fa_A2']:.1f} → {h['fa_D']:.2f}", "false alarms / patient-day, A2 → D", 9.4, 4.9, 3.4, ORANGE)

    # 7 federated
    s = dk.slide("Federated matches centralised",
                 "FedAvg with full participation across non-IID sites. Raw rows never leave a site; only model weights move. "
                 "We ran enough rounds to converge: the training loss reaches the centralised optimum, and the table shows the paired "
                 "difference between F and D over seeds with a 95 percent confidence interval. With five seeds the intervals are wide; "
                 "we say indistinguishable, not identical. Local-only training E is shown for contrast.", tag="both datasets")
    dk.image(s, "figures/fig_fl_convergence.png", 0.5, 1.5, w=6.4)
    y = 1.6
    for ds in D:
        h = H[ds]
        dk.text(s, [f"**{DS_NAME[ds]}**", f"F1(F) − F1(D) = {ci(h['F_D']['f1'])}",
                    f"AUROC(F) − AUROC(D) = {ci(h['F_D']['auroc'])}",
                    f"converged in ~{h['rounds_conv']:.0f} rounds (ran {h['rounds_used']})"], 7.2, y, 5.8, 2.1, size=17,
                color=RGBColor(0x22, 0x22, 0x22))
        y += 2.4
    dk.text(s, "Mean [95% CI] of paired per-seed differences, n = 5.", 7.2, 6.55, 5.8, 0.4, size=13, color=GREY)

    # 8 privacy-utility
    s = dk.slide("Privacy costs little until the noise gets large",
                 "DP-SGD with per-record clipping, Gaussian noise and a Renyi accountant at delta 1e-5. Epsilon here is record-level, not "
                 "patient-level; one patient contributes hundreds of correlated rows, so patient-level protection is much weaker. "
                 "The green band is non-private FedAvg; the orange line is FedAvg with DP at five noise levels; the dashed line is the "
                 "centralised baseline. A simple membership-inference attack found no leakage even for the non-private models, "
                 "which is a sanity check, not a proof.", tag="both datasets")
    yy = 1.4
    for ds in D:
        dk.image(s, f"figures/fig_privacy_utility_{ds}.png", 0.9, yy, w=7.3)
        dk.text(s, DS_NAME[ds], 8.5, yy + 0.5, 4.5, 0.8, size=17, bold=True, color=BLUE)
        k = H[ds]["dp_keep"]
        if k:
            dk.text(s, f"No measurable F1 loss up to σ = {k['sigma']:g} (record-level ε = {eps_str(k['epsilon'])})", 8.5, yy + 1.2, 4.5, 1.2,
                    size=16, color=RGBColor(0x22, 0x22, 0x22))
        yy += 2.9
    dk.text(s, "ε is record-level (δ = 1e-5), not patient-level", 8.5, 6.8, 4.6, 0.4, size=13, color=ORANGE, bold=True)

    # 9 latency
    lat = S["latency"]; k = lat.get("kafka"); ip = lat.get("inprocess")
    s = dk.slide("Latency is set by the micro-batch trigger",
                 "Real end-to-end latency measured by the alert consumer: producer timestamp to consumer receipt, through Kafka, Spark and "
                 "Kafka again, at three event rates and three trigger intervals. Benchmarks ran on one laptop, one broker per cluster, Spark "
                 "local mode with two cores. In-process, one event takes about "
                 + (f"{ip['step_us']['p50']:.0f} microseconds. " if ip else "") +
                 "So Spark's micro-batch trigger dominates. For 5-minute vitals even a 5 second trigger is clinically negligible.",
                 tag="Synthetic replay")
    dk.image(s, "figures/fig_latency.png", 0.5, 1.45, w=9.0)
    if k:
        r1 = [r for r in k["runs"] if r["trigger"] == "1 second" and r["target_rate"] == 500]
        if r1:
            dk.stat(s, f"{r1[0]['latency_ms']['p50']/1000:.2f} s", "p50 end-to-end, 1 s trigger, 500 ev/s", 9.8, 1.5, 3.1, BLUE)
            dk.stat(s, f"{r1[0]['latency_ms']['p99']/1000:.2f} s", "p99 end-to-end, same run", 9.8, 3.2, 3.1, ORANGE)
    if ip:
        dk.stat(s, f"{ip['step_us']['p99']:.0f} µs", "p99 in-process, per event", 9.8, 4.9, 3.1, GREEN)

    # 10 cost
    cost = S.get("cost") or {}
    s = dk.slide("Only alerts and model updates leave the site",
                 "Bytes leaving the site per month for a scenario of 1000 patients, one sample per 5 minutes. Centralised raw streaming "
                 "versus alerts plus federated model updates plus threshold count tables. Bytes and CPU-seconds are measured; dollar "
                 "figures use the illustrative price table in the report: egress 9 cents per GB, 4 cents per vCPU-hour.",
                 tag=DS_NAME["eicu"] if "eicu" in cost else "scenario")
    dk.image(s, "figures/fig_cost.png", 0.5, 1.5, w=7.6)
    if cost:
        v = cost.get("eicu") or next(iter(cost.values()))
        dk.stat(s, f"{v['reduction_factor']:,.0f}×", "fewer bytes leave the site", 8.6, 1.6, 4.1, GREEN)
        dk.stat(s, fmt_bytes(v["raw_stream_bytes"]), "raw streaming / month", 8.6, 3.3, 4.1, ORANGE)
        dk.stat(s, fmt_bytes(v["federated_bytes"]), "alerts + FL updates / month", 8.6, 5.0, 4.1, BLUE)

    # 11 limitations
    s = dk.slide("Limitations",
                 "Be upfront. Epsilon is record-level. Federated learning is simulated in one process rather than run over Kafka. There is "
                 "no attack evaluation beyond one simple membership inference check. Labels are injected, so absolute accuracy is not clinical. "
                 "The model is a simple linear model. Thresholds are tuned on labelled data.")
    dk.bullets(s, ["**Record-level DP**, not patient-level",
                   "**FL simulated** in-process, not run over Kafka",
                   "Only a simple membership-inference check (no stronger attacks)",
                   "**Semi-synthetic labels**: injected episodes, not clinical truth",
                   "Simple linear model; thresholds tuned on labelled data",
                   "Small public demo; 5 seeds → wide intervals"], 0.8, 1.7, 11.8, 5.2, size=26)

    # 12 conclusion
    s = dk.slide("Conclusion",
                 "Answer to the research question: yes, within our statistical resolution and on injected-label benchmarks. "
                 "Adaptive thresholds cut false alarms; federated training on adaptive features matched centralised; record-level DP was "
                 "nearly free at moderate noise; and sending only alerts and model updates cuts bytes by orders of magnitude. "
                 "Next steps: validate on real annotated alarms and analyse patient-level privacy.")
    items = []
    for ds in D:
        h = H[ds]
        items.append(f"**{DS_NAME[ds]}:** adaptive threshold −{h['fa_cut_C_vs_A2']*100:.0f}% false alarms; "
                     f"F − D F1 = {ci(h['F_D']['f1'])}")
    items += ["Privacy noise is nearly free until σ becomes large (record-level ε)",
              "Raw vitals stay local; alerts + model updates only",
              "**Next:** real annotated alarms, patient-level privacy"]
    dk.bullets(s, items, 0.8, 1.7, 11.8, 5.2, size=24)
    dk.save(out)
    return out


def to_pdf(pptx_path):
    outdir = os.path.dirname(pptx_path)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, pptx_path],
                   check=True, capture_output=True, timeout=240)
    return pptx_path.replace(".pptx", ".pdf")


def main():
    print(build())


if __name__ == "__main__":
    main()
