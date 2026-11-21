"""Generate every figure from data / results/summary.json.  Dataset on every title."""
from __future__ import annotations

import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from . import config as C
from . import features as F
from . import metrics as M

FIG = "figures"
DS_LABEL = {"synthetic": "Synthetic cohort", "eicu": "eICU-CRD demo + injected episodes"}
COL = {"A": "#9a9a9a", "A2": "#6b6b6b", "B": "#e69f00", "C": "#56b4e9", "D": "#0072b2",
       "E": "#cc79a7", "F": "#009e73", "G": "#d55e00"}
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 12, "axes.labelsize": 11, "figure.dpi": 100,
                     "savefig.dpi": 200, "savefig.bbox": "tight", "legend.frameon": False})


def _save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    p = os.path.join(FIG, name)
    fig.savefig(p)
    plt.close(fig)
    return p


# ----------------------------------------------------------------- architecture
def fig_architecture(path="docs/architecture.png"):
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.set_xlim(0, 11); ax.set_ylim(0, 4.6); ax.axis("off")

    def box(x, y, w, h, text, fc, ec="#333", fs=10, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08",
                                    fc=fc, ec=ec, lw=1.2))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                fontweight="bold" if bold else "normal", linespacing=1.25)

    def arrow(x0, y0, x1, y1, text="", dy=0.16):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", lw=1.5, color="#333"))
        if text:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, text, ha="center", fontsize=8.5, color="#333")

    ax.add_patch(FancyBboxPatch((0.1, 0.35), 7.3, 4.0, boxstyle="round,pad=0.03,rounding_size=0.1",
                                fc="#eef6fb", ec="#0072b2", lw=1.6, ls="--"))
    ax.text(0.3, 4.1, "SITE (raw vitals never leave)", fontsize=10.5, color="#0072b2", fontweight="bold")
    box(0.35, 2.0, 1.7, 1.2, "Producer\nreplays vitals\n+ producer ts", "#fff")
    box(2.55, 2.0, 1.9, 1.2, "kafka-site :9092\nvitals.raw.<site>\n(1 h retention)", "#fde9c8", bold=False)
    box(4.95, 2.0, 2.2, 1.2, "Spark Structured\nStreaming\nper-patient JSON state", "#d8f0e5")
    box(0.35, 0.55, 3.6, 0.95, "Local training\n(FedAvg / DP-SGD client)", "#e8e3f4")
    box(4.75, 3.45, 2.6, 0.55, "shared code path: offline == serving", "#fff", fs=8.5)
    ax.add_patch(FancyBboxPatch((8.0, 0.35), 2.9, 4.0, boxstyle="round,pad=0.03,rounding_size=0.1",
                                fc="#fdf1e8", ec="#d55e00", lw=1.6, ls="--"))
    ax.text(8.2, 4.1, "CENTRAL", fontsize=10.5, color="#d55e00", fontweight="bold")
    box(8.25, 2.0, 2.4, 1.2, "kafka-central :9093\nalerts.central\n(hashed id, score)", "#fde9c8")
    box(8.25, 0.55, 2.4, 0.95, "FL server (FedAvg)\n+ alert consumer", "#e8e3f4", fs=9.5)
    arrow(2.05, 2.6, 2.55, 2.6)
    arrow(4.45, 2.6, 4.95, 2.6)
    arrow(7.15, 2.6, 8.25, 2.6, "alerts only", dy=0.2)
    arrow(3.95, 1.0, 8.25, 1.0, "model updates / count tables", dy=0.15)
    return _save_to(fig, path)


def _save_to(fig, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


# ------------------------------------------------------- adaptive-threshold example
def _trace(p, j=1):
    st = F.new_state("adaptive")
    mu, sd, z = [], [], []
    for x in p.X:
        mu.append(st["mu"][j]); sd.append(max(math.sqrt(st["var"][j]), C.MIN_SCALE[C.VITALS[j]]))
        row = F.update_state(st, x)
        z.append(np.nan if row[j] is None else row[j])
    return np.array(mu), np.array(sd), np.array(z)


def plot_adaptive_example(p, title, fname, tau_z=3.5, thr=92.0, j=1):
    mu, sd, z = _trace(p, j)
    x = p.X[:, j]
    t_h = np.arange(p.T) * p.dt_min / 60.0
    stat = np.where(np.isnan(x), 0.0, (thr - x))         # >0 means below threshold
    s_flag = np.where(np.isnan(x), False, x < thr)
    a_flag = np.where(np.isnan(z), False, z < -tau_z)
    lo = int(2 * 60 / p.dt_min)
    n_static = sum(len(range(a + 2, b, 12)) for a, b in M.runs(s_flag[lo:], 3))
    n_adapt = sum(len(range(a + 2, b, 12)) for a, b in M.runs(a_flag[lo:], 3))
    days = p.T * p.dt_min / 1440.0
    fig, ax = plt.subplots(2, 1, figsize=(10, 5.6), sharex=True, gridspec_kw=dict(height_ratios=[2.2, 1]))
    a = ax[0]
    a.plot(t_h, x, color="#333", lw=0.9, label="SpO2 (%)")
    a.axhline(thr, color="#d55e00", lw=1.8, ls="--", label=f"fixed ward threshold ({thr:.0f}%)")
    a.plot(t_h, mu, color="#0072b2", lw=1.6, label="adaptive baseline")
    a.fill_between(t_h, mu - tau_z * sd, np.minimum(mu + tau_z * sd, 100.0), color="#0072b2", alpha=0.13,
                   label=f"adaptive band (±{tau_z} sd)")
    for s, e, k in p.episodes:
        a.axvspan(s * p.dt_min / 60, e * p.dt_min / 60, color="#d55e00", alpha=0.18, lw=0)
    a.scatter(t_h[s_flag], x[s_flag], s=7, color="#d55e00", zorder=3, label="below fixed threshold")
    a.axvline(p.split * p.dt_min / 60, color="#777", lw=1, ls=":")
    a.set_ylim(40, 103)
    a.text(p.split * p.dt_min / 60 + 0.6, 41.5, "held-out test →", fontsize=9, color="#555", va="bottom")
    a.set_ylabel("SpO2 (%)")
    a.set_title(f"{title}\nFixed threshold: {n_static} alarms in {days:.1f} days;  "
                f"adaptive: {n_adapt} alarm(s)  (shaded = injected deterioration episode)", fontsize=11)
    a.legend(loc="lower center", ncol=3, fontsize=8.5)
    b = ax[1]
    b.plot(t_h, z, color="#333", lw=0.8)
    b.axhline(-tau_z, color="#0072b2", ls="--", lw=1.4)
    b.set_ylim(-9, 4)
    b.set_ylabel("adaptive z (SpO2)"); b.set_xlabel("hours since start of series")
    for s, e, k in p.episodes:
        b.axvspan(s * p.dt_min / 60, e * p.dt_min / 60, color="#d55e00", alpha=0.18, lw=0)
    fig.tight_layout()
    return _save(fig, fname), dict(static_alarms=int(n_static), adaptive_alarms=int(n_adapt), days=float(days))


def fig_adaptive_examples():
    from .data import public as PB
    from .data import synthetic as SY
    out = {}
    rng = np.random.default_rng(5)
    best = None
    for sd in range(40):
        r = np.random.default_rng(sd)
        p = SY.make_patient("copd-demo", "site1", "copd", 4.0, r)
        ev = [e for e in p.episodes if e[2] == "hypoxia" and e[0] >= p.split]
        if ev:
            best = p
            break
    best = best or p
    out["synthetic"] = plot_adaptive_example(
        best, "Synthetic cohort — COPD-phenotype patient (normal SpO2 ≈ 90 %)", "fig_adaptive_synthetic.png")
    try:
        series = PB.load_series()
        cand = [(sid, h, X) for sid, h, X in series
                if 89.0 <= np.nanmedian(X[:, 1]) <= 91.5 and np.isnan(X[:, 1]).mean() < 0.1
                and np.nanpercentile(X[:, 1], 10) >= 87 and np.nanpercentile(X[:, 1], 90) <= 96.5]
        for seed in range(30):
            r = np.random.default_rng(seed)
            sid, h, X = cand[seed % len(cand)]
            from .cohort import Patient, inject_episodes
            Xi, y, ep, eps = inject_episodes(X, r, 5.0)
            if any(k in ("hypoxia", "shock", "sepsis") and s >= int(0.6 * len(X)) for s, e, k in eps):
                p = Patient(f"eicu-{sid}", "site0", Xi, y, ep, eps, 5.0)
                break
        out["eicu"] = plot_adaptive_example(
            p, "eICU-CRD demo (real SpO2 trace, injected episode) — patient whose normal SpO2 ≈ 90 %",
            "fig_adaptive_eicu.png")
    except FileNotFoundError:
        pass
    return out




# ------------------------------------------------------------ summary-driven figures
def _load(path="results/summary.json"):
    return json.load(open(path))


def _m(d, key, metric):
    v = d["methods"][key][metric]
    return v["mean"], v["sd"]


def fig_accuracy(S, ds):
    d = S["datasets"][ds]
    keys = ["A", "A2", "B", "C", "D", "E", "F", "G@8.0"]
    labels = ["A\nstatic", "A2\nstatic+m", "B\ncentral\nfixed", "C\nadaptive\nthreshold", "D\ncentral\nadaptive",
              "E\nlocal", "F\nfederated", "G\nFL+DP\n(σ=8)"]
    cols = [COL[k.split("@")[0]] for k in keys]
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
    for a, metric, ttl, log in ((ax[0], "f1", "Alarm-level F1 (higher is better)", False),
                                (ax[1], "fa_per_day", "False alarms per patient-day (lower is better)", True)):
        mu = [_m(d, k, metric)[0] for k in keys]
        sd = [_m(d, k, metric)[1] for k in keys]
        a.bar(range(len(keys)), mu, yerr=sd, color=cols, capsize=3, edgecolor="#222", lw=0.6)
        a.set_xticks(range(len(keys))); a.set_xticklabels(labels, fontsize=8.5)
        a.set_title(ttl)
        if log:
            a.set_yscale("log")
        for i, m_ in enumerate(mu):
            top = (m_ + sd[i]) * 1.12 if log else m_ + sd[i] + 0.012
            a.text(i, top, f"{m_:.2f}", ha="center", va="bottom", fontsize=8)
        if log:
            a.set_ylim(top=max(mu) * 2.6)
    fig.suptitle(f"{DS_LABEL[ds]} — mean ± sd over {d['n_seeds']} seeds, held-out last 40 % of each series", fontsize=11, y=1.02)
    fig.tight_layout()
    return _save(fig, f"fig_accuracy_{ds}.png")


def fig_privacy_utility(S, ds):
    d = S["datasets"][ds]
    pu = [r for r in d["privacy_utility"]]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.0))
    f1_ref = d["methods"]["F"]["f1"]; au_ref = d["methods"]["F"]["auroc"]
    for a, metric, ref, nm in ((ax[0], "f1", f1_ref, "Alarm-level F1"), (ax[1], "auroc", au_ref, "Sample-level AUROC")):
        eps = np.array([r["epsilon"] for r in pu]); mu = np.array([r[metric]["mean"] for r in pu])
        sd = np.array([r[metric]["sd"] for r in pu])
        a.errorbar(eps, mu, yerr=sd, marker="o", color=COL["G"], capsize=3, lw=1.8, label="G: FL + DP")
        for e, m_, r in zip(eps, mu, pu):
            a.annotate(f"σ={r['sigma']:g}", (e, m_), textcoords="offset points", xytext=(4, 8), fontsize=8.5)
        a.axhline(ref["mean"], color=COL["F"], lw=1.8, label="F: FedAvg, no DP (ε=∞)")
        a.axhspan(ref["mean"] - ref["sd"], ref["mean"] + ref["sd"], color=COL["F"], alpha=0.15, lw=0)
        base = d["methods"]["B"][metric]["mean"]
        a.axhline(base, color=COL["B"], lw=1.4, ls="--", label="B: centralised baseline")
        a.set_xscale("log"); a.set_xlabel("record-level ε  (δ = 1e-5; smaller = more private)")
        a.set_ylabel(nm); a.legend(fontsize=8.5, loc="lower right")
    fig.suptitle(f"{DS_LABEL[ds]} — privacy–utility (ε is record-level, not patient-level)", fontsize=11, y=1.02)
    fig.tight_layout()
    return _save(fig, f"fig_privacy_utility_{ds}.png")


def fig_fl_convergence(S):
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for ds, c in (("synthetic", "#0072b2"), ("eicu", "#d55e00")):
        if ds not in S["datasets"]:
            continue
        f = S["datasets"][ds]["federated"]
        curve = np.array(f["loss_curve"])
        opt = curve[-1, 1] - f["final_loss_gap"]["mean"]
        ax.plot(curve[:, 0], np.maximum(curve[:, 1] - opt, 1e-9), color=c, lw=1.8,
                label=f"{DS_LABEL[ds].split(' +')[0]} (≤1e-3 rel. at round {f['rounds_to_converge']['mean']:.0f})")
    ax.set_yscale("log"); ax.set_xlabel("FedAvg round"); ax.set_ylabel("training loss − centralised optimum")
    ax.axhline(1e-3 * 0.4, color="#777", ls=":", lw=1)
    ax.legend(fontsize=8.5); ax.set_title("Federated training reaches the centralised optimum (seed 0)")
    fig.tight_layout()
    return _save(fig, "fig_fl_convergence.png")


def fig_latency(S):
    k = S["latency"].get("kafka")
    if not k:
        return None
    runs = k["runs"]
    trig = ["500 milliseconds", "1 second", "5 seconds"]
    rates = sorted({r["target_rate"] for r in runs if r["target_rate"] > 0})
    fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2), gridspec_kw=dict(width_ratios=[2.2, 1]))
    w = 0.26
    pal = ["#9ecae1", "#4292c6", "#08519c"]
    for i, rate in enumerate(rates):
        xs, p50, p95, p99 = [], [], [], []
        for j, t in enumerate(trig):
            r = [r for r in runs if r["trigger"] == t and r["target_rate"] == rate]
            if r:
                xs.append(j + (i - 1) * w); l = r[0]["latency_ms"]
                p50.append(l["p50"]); p95.append(l["p95"]); p99.append(l["p99"])
        ax[0].bar(xs, p50, w, color=pal[i], edgecolor="#222", lw=0.6, label=f"{rate:g} events/s")
        ax[0].scatter(xs, p95, marker="_", s=260, color="#d55e00", zorder=3, lw=2, label="p95" if i == 0 else None)
        ax[0].scatter(xs, p99, marker="x", s=36, color="#222", zorder=3, label="p99" if i == 0 else None)
    ax[0].set_xticks(range(len(trig))); ax[0].set_xticklabels(["0.5 s", "1 s", "5 s"])
    ax[0].set_xlabel("micro-batch trigger interval"); ax[0].set_ylabel("end-to-end latency (ms), bars = p50")
    ax[0].set_yscale("log"); ax[0].legend(fontsize=8.5, ncol=2)
    ax[0].set_title("Kafka → Spark → Kafka latency (synthetic replay, 1 broker per cluster)")
    thr = []
    for t in trig:
        r = [r for r in runs if r["trigger"] == t and r["target_rate"] == 0]
        thr.append(r[0]["throughput_eps"] if r and r[0].get("throughput_eps") else 0)
    ax[1].bar(range(len(trig)), thr, color=COL["F"], edgecolor="#222", lw=0.6)
    for i, v in enumerate(thr):
        ax[1].text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
    ax[1].set_xticks(range(len(trig))); ax[1].set_xticklabels(["0.5 s", "1 s", "5 s"])
    ax[1].set_xlabel("trigger"); ax[1].set_ylabel("events / s"); ax[1].set_title("Max sustained throughput\n(local[2])")
    fig.tight_layout()
    return _save(fig, "fig_latency.png")


def fig_cost(S):
    c = S.get("cost") or {}
    if not c:
        return None
    ds = "eicu" if "eicu" in c else list(c)[0]
    v = c[ds]
    vals = [v["raw_stream_bytes"], v["federated_bytes"], v["alert_bytes"], v["model_update_bytes"]]
    labels = ["raw streaming\n(centralised)", "federated total\n(alerts+updates)", "  of which\nalerts", "  of which\nmodel updates"]
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    b = ax.bar(range(4), vals, color=[COL["B"], COL["F"], "#7fcdbb", "#c7e9c0"], edgecolor="#222", lw=0.6)
    ax.set_yscale("log"); ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=9)
    for i, x in enumerate(vals):
        ax.text(i, x * 1.15, f"{x/1e6:,.1f} MB" if x < 1e9 else f"{x/1e9:,.2f} GB", ha="center", fontsize=9)
    ax.set_ylabel("bytes leaving the site / month (log)")
    sc = v["scenario"]
    ax.set_title(f"{sc['patients']} patients, 1 sample/{sc['sample_minutes']:g} min, {sc['days']} days — "
                 f"{v['reduction_factor']:,.0f}× less data leaves", fontsize=10.5)
    ax.set_ylim(top=max(vals) * 8)
    fig.tight_layout()
    return _save(fig, "fig_cost.png")


def fig_ablations(S, ds):
    A = S["datasets"][ds].get("ablations")
    if not A:
        return None
    fig, ax = plt.subplots(2, 3, figsize=(13, 7))
    a = ax[0, 0]
    xs = sorted(A["alpha"], key=float)
    for k, c, nm in (("C", COL["C"], "C adaptive threshold"), ("D", COL["D"], "D centralised ML")):
        a.errorbar([float(x) for x in xs], [A["alpha"][x][k]["fa_per_day"]["mean"] for x in xs],
                   yerr=[A["alpha"][x][k]["fa_per_day"]["sd"] for x in xs], marker="o", color=c, label=nm, capsize=2)
    a.set_xscale("log"); a.set_xlabel("EWMA rate α"); a.set_ylabel("false alarms / patient-day"); a.legend(fontsize=8)
    a.set_title("(a) adaptation rate α: false alarms")
    a = ax[0, 1]
    for k, c, nm in (("C", COL["C"], "C"), ("D", COL["D"], "D")):
        a.errorbar([float(x) for x in xs], [A["alpha"][x][k]["f1"]["mean"] for x in xs],
                   yerr=[A["alpha"][x][k]["f1"]["sd"] for x in xs], marker="o", color=c, label=nm, capsize=2)
    a.set_xscale("log"); a.set_xlabel("EWMA rate α"); a.set_ylabel("F1"); a.set_title("(b) adaptation rate α: F1")
    a.legend(fontsize=8)
    a = ax[0, 2]
    xm = sorted(A["m"], key=int)
    for k, c, nm in (("A2", COL["A2"], "A2 static"), ("C", COL["C"], "C adaptive"), ("D", COL["D"], "D ML adaptive")):
        a.errorbar([int(x) for x in xm], [A["m"][x][k]["fa_per_day"]["mean"] for x in xm],
                   yerr=[A["m"][x][k]["fa_per_day"]["sd"] for x in xm], marker="o", color=c, label=nm, capsize=2)
    a.set_yscale("log"); a.set_xlabel("persistence m (consecutive samples)"); a.set_ylabel("false alarms / patient-day")
    a.set_title("(c) persistence m"); a.legend(fontsize=8)
    a = ax[1, 0]
    xc = sorted(A["clip"], key=float)
    a.errorbar([float(x) for x in xc], [A["clip"][x]["f1"]["mean"] for x in xc],
               yerr=[A["clip"][x]["f1"]["sd"] for x in xc], marker="o", color=COL["G"], capsize=2)
    a.axhline(S["datasets"][ds]["methods"]["F"]["f1"]["mean"], color=COL["F"], ls="--", label="F (no DP)")
    a.set_xscale("log"); a.set_xlabel("per-record clip norm C (σ = 8)"); a.set_ylabel("F1")
    a.set_title("(d) DP clipping bound"); a.legend(fontsize=8)
    a = ax[1, 1]
    xs_ = sorted(A["sites"], key=int)
    for k, c, nm in (("D", COL["D"], "D centralised"), ("E", COL["E"], "E local-only"), ("F", COL["F"], "F federated")):
        a.errorbar([int(x) for x in xs_], [A["sites"][x][k]["f1"]["mean"] for x in xs_],
                   yerr=[A["sites"][x][k]["f1"]["sd"] for x in xs_], marker="o", color=c, label=nm, capsize=2)
    a.set_xticks([int(x) for x in xs_]); a.set_xlabel("number of sites"); a.set_ylabel("F1")
    a.set_title("(e) number of sites"); a.legend(fontsize=8)
    a = ax[1, 2]
    xr = sorted(A["rounds"], key=int)
    a.plot([int(x) for x in xr], [A["rounds"][x]["f1"]["mean"] for x in xr], marker="o", color=COL["F"], label="F1")
    a.fill_between([int(x) for x in xr], [A["rounds"][x]["f1"]["mean"] - A["rounds"][x]["f1"]["sd"] for x in xr],
                   [A["rounds"][x]["f1"]["mean"] + A["rounds"][x]["f1"]["sd"] for x in xr], color=COL["F"], alpha=0.2)
    a.set_xscale("log"); a.set_xlabel("FedAvg rounds"); a.set_ylabel("F1"); a.set_title("(f) number of FL rounds")
    fig.suptitle(f"Ablations — {DS_LABEL[ds]} (mean ± sd over {A['alpha'][xs[0]]['C']['f1']['n']} seeds)", fontsize=12)
    fig.tight_layout()
    return _save(fig, f"fig_ablations_{ds}.png")


def make_all():
    fig_architecture()
    fig_adaptive_examples()
    S = _load()
    for ds in S["datasets"]:
        fig_accuracy(S, ds); fig_privacy_utility(S, ds); fig_ablations(S, ds)
    fig_fl_convergence(S); fig_latency(S); fig_cost(S)


if __name__ == "__main__":
    make_all()
