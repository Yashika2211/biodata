"""Report section: results."""
from __future__ import annotations

import datetime

from docx.shared import Pt

from ..docs_common import (DS_NAME, DS_SHORT, METHOD_NAME, ci, eps_str, fmt_bytes, num, pm)
from .helpers import AUTHOR, TITLE, accuracy_rows, verdict


def add(doc, ctx):
    S, D, syn, eic, H, P = ctx.S, ctx.D, ctx.syn, ctx.eic, ctx.H, ctx.P
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
        def p50(t, r):
            x = [q for q in k["runs"] if q["trigger"] == t and q["target_rate"] == r]
            return x[0]["latency_ms"]["p50"] / 1000 if x else float("nan")
        doc.p(f"At 1000 events/s the p50 end-to-end latency was {p50('500 milliseconds', 1000):.1f} s (0.5 s trigger), "
              f"{p50('1 second', 1000):.1f} s (1 s) and {p50('5 seconds', 1000):.1f} s (5 s trigger); p99 was several seconds. "
              "Latency is the wait for the next micro-batch plus the batch's own processing time (Spark scheduling, Python worker, "
              "state store, Kafka write); with 160 patient keys on local[2] one batch takes roughly a second, so the trigger only "
              "matters once it exceeds that. The job saturates near 800–1000 events/s on this setup. "
              "**Unexplained anomaly:** the slowest p50 (4–5 s) occurred at the *lowest* rate (50 events/s) for the 0.5 s and 1 s triggers, "
              "which we did not diagnose (we suspect small-batch/idle-partition effects in the Kafka source, untested). "
              "The \"max\" throughput figures come from the consumer's first-to-last-message span and are unreliable for the 5 s trigger "
              "(one large batch). For 5-minute vitals, even multi-second latency is clinically negligible.")
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
    fk = S.get("fl_over_kafka")
    if fk:
        doc.p(f"**Federated communication over Kafka.** Running {fk['rounds']} FedAvg rounds with {fk['sites']} sites through "
              f"`fl.updates` / `fl.global` topics moved {fk['bytes_up_measured']/1e3:.0f} kB of site updates and "
              f"{fk['bytes_down_measured']/1e3:.0f} kB of global models (JSON-encoded; {fk['parameters']} parameters per message), "
              f"versus {fk['bytes_analytic_float64']/1e3:.0f} kB for the analytic float64 estimate used in the cost scenario, "
              f"and gave the same model as the in-process simulation (max |Δθ| = {fk['max_abs_diff_vs_in_process']:.1e}). "
              "Either way it is negligible next to raw streaming.")
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
