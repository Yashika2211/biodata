"""Aggregate raw per-seed results into ``results/summary.json``.

Everything in the report and deck is generated from this one file.
"""
from __future__ import annotations

import json
import os

import numpy as np
from scipy import stats

from . import config as C
from . import costs as CO

METRICS = ["precision", "recall", "f1", "fa_per_day", "delay_min", "auroc", "auprc"]
NAMES = {
    "A": "A  static thresholds (instant)",
    "A2": "A2 static + persistence",
    "B": "B  centralised, fixed priors",
    "C": "C  adaptive threshold (no learning)",
    "D": "D  centralised, adaptive features",
    "E": "E  local-only per site",
    "F": "F  federated (FedAvg), adaptive",
}


def _f(x):
    return float("inf") if x == "inf" else (np.nan if x is None else float(x))


def ms(vals):
    a = np.array([_f(v) for v in vals], dtype=float)
    a = a[~np.isnan(a)]
    if len(a) == 0:
        return dict(mean=None, sd=None, n=0)
    return dict(mean=float(a.mean()), sd=float(a.std(ddof=1)) if len(a) > 1 else 0.0, n=int(len(a)))


def paired(a_vals, b_vals):
    """Mean difference a-b over seeds with sd and a 95% t-interval."""
    d = np.array([_f(x) - _f(y) for x, y in zip(a_vals, b_vals)], dtype=float)
    d = d[~np.isnan(d)]
    n = len(d)
    if n < 2:
        return dict(mean=float(d.mean()) if n else None, sd=None, ci95=None, n=n)
    sd = float(d.std(ddof=1)); se = sd / np.sqrt(n)
    h = float(stats.t.ppf(0.975, n - 1) * se)
    return dict(mean=float(d.mean()), sd=sd, ci95=[float(d.mean() - h), float(d.mean() + h)], n=n)


def method_table(runs, keys):
    out = {}
    for k in keys:
        rows = [r[k] for r in runs if k in r]
        if not rows:
            continue
        out[k] = {m: ms([r.get(m) for r in rows]) for m in METRICS}
        for extra in ("tau", "epsilon", "rounds_to_converge", "loss_gap", "train_seconds", "bytes_exchanged"):
            if any(extra in r for r in rows):
                out[k][extra] = ms([r.get(extra) for r in rows])
    return out


def dataset_summary(raw):
    runs = raw["main"]
    sig_keys = sorted([k for k in runs[0] if k.startswith("G@")], key=lambda k: float(k[2:]))
    keys = ["A", "A2", "B", "C", "D", "E", "F"] + sig_keys
    S = {"label": raw["label"], "n_seeds": len(runs)}
    S["methods"] = method_table(runs, keys)
    S["cohort"] = {k: ms([r["_cohort"][k] for r in runs]) for k in runs[0]["_cohort"]}
    pairs = {"F_minus_D": ("F", "D"), "F_minus_B": ("F", "B"), "D_minus_B": ("D", "B"),
             "C_minus_A2": ("C", "A2"), "D_minus_C": ("D", "C"), "F_minus_E": ("F", "E")}
    for sk in sig_keys:
        pairs[f"{sk}_minus_F"] = (sk, "F")
    S["paired"] = {name: {m: paired([r[a][m] for r in runs], [r[b][m] for r in runs])
                          for m in ("f1", "auroc", "auprc", "fa_per_day", "recall", "precision")}
                   for name, (a, b) in pairs.items()}
    # privacy-utility curve
    S["privacy_utility"] = [dict(key=k, sigma=float(k[2:]),
                                 epsilon=S["methods"][k]["epsilon"]["mean"],
                                 f1=S["methods"][k]["f1"], auroc=S["methods"][k]["auroc"],
                                 auprc=S["methods"][k]["auprc"], fa_per_day=S["methods"][k]["fa_per_day"])
                            for k in sig_keys]
    # federated convergence
    S["federated"] = dict(
        rounds_used=int(runs[0]["F"]["rounds"]),
        rounds_to_converge=ms([r["F"].get("rounds_to_converge") for r in runs]),
        final_loss_gap=ms([r["F"].get("loss_gap") for r in runs]),
        loss_curve=[[int(a), float(b)] for a, b in runs[0]["_loss_curve"]],
        bytes_exchanged=ms([r["F"].get("bytes_exchanged") for r in runs]))
    # membership inference
    if raw.get("mia"):
        names = list(raw["mia"][0])
        S["mia_auroc"] = {n: ms([r[n] for r in raw["mia"]]) for n in names}
    # ablations
    ab = raw.get("ablations")
    if ab:
        A = {}
        A["alpha"] = {a: {k: {m: ms([r[k][m] for r in rs]) for m in ("f1", "fa_per_day", "auroc", "recall")}
                          for k in ("C", "D")} for a, rs in ab["alpha"].items()}
        A["m"] = {a: {k: {m: ms([r[k][m] for r in rs]) for m in ("f1", "fa_per_day", "recall", "delay_min")}
                      for k in ("A2", "C", "D")} for a, rs in ab["m"].items()}
        A["clip"] = {a: {m: ms([r[m] for r in rs]) for m in ("f1", "auroc", "fa_per_day", "epsilon")}
                     for a, rs in ab["clip"].items()}
        A["sites"] = {a: {k: {m: ms([r[k][m] for r in rs]) for m in ("f1", "auroc", "fa_per_day")}
                          for k in ("D", "E", "F")} for a, rs in ab["sites"].items()}
        A["rounds"] = {a: {m: ms([r[m] for r in rs]) for m in ("f1", "auroc", "fa_per_day", "final_loss")}
                       for a, rs in ab["rounds"].items()}
        S["ablations"] = A
    S["wall_seconds"] = raw.get("wall_seconds")
    return S


def build(results_dir="results"):
    out = {"datasets": {}, "protocol": dict(
        train_fraction=0.6, persistence_m=C.PERSISTENCE_M, alpha=C.ALPHA, window=C.WINDOW,
        dt_min=C.DT_MIN, tolerance_min=30, refire_min=60, delta=1e-5, dp_clip=10.0,
        dp_sampling_rate=0.02, dp_rounds=150, features=C.NF, vitals=list(C.VITALS))}
    for ds in ("synthetic", "eicu"):
        p = os.path.join(results_dir, f"raw_{ds}.json")
        if os.path.exists(p):
            out["datasets"][ds] = dataset_summary(json.load(open(p)))
    lat = {}
    p = os.path.join(results_dir, "bench_inprocess.json")
    if os.path.exists(p):
        lat["inprocess"] = json.load(open(p))
    p = os.path.join(results_dir, "bench_kafka.json")
    if os.path.exists(p):
        lat["kafka"] = json.load(open(p))
    out["latency"] = lat
    # cost: measured bytes + CPU, per dataset, from method D alarm rates
    cost = {}
    if lat.get("inprocess"):
        cpu_in = lat["inprocess"]["cpu_seconds_per_million_events"]
        kruns = (lat.get("kafka") or {}).get("runs", [])
        cpu_sp = [r["cpu_seconds_per_million_events"] for r in kruns if r["target_rate"] == 0 and r.get("received")]
        avg_ev = float(np.mean([r["avg_event_bytes"] for r in kruns])) if kruns else 146.0
        avg_alert = 118.0
        for ds, s in out["datasets"].items():
            m = s["methods"]["F"]
            alarms_day = m["fa_per_day"]["mean"] + m["recall"]["mean"] * s["cohort"]["test_episodes"]["mean"] / s["cohort"]["days"]["mean"] * 0.4
            cost[ds] = CO.scenario_costs(avg_ev, avg_alert, alarms_day, cpu_in)
            if cpu_sp:
                cost[ds]["spark_cpu_s_per_million_events"] = float(np.mean(cpu_sp))
                cost[ds]["scoring_usd_spark"] = cost[ds]["events"] / 1e6 * float(np.mean(cpu_sp)) / 3600 * CO.PRICES["vcpu_usd_per_hour"]
    out["cost"] = cost
    out["prices"] = CO.PRICES
    out["scenario"] = CO.SCENARIO
    json.dump(out, open(os.path.join(results_dir, "summary.json"), "w"), indent=1)
    return out


def main():
    s = build()
    print("datasets:", list(s["datasets"]))


if __name__ == "__main__":
    main()
