"""Shared helpers for the report and the deck: formatting and headline numbers.

Nothing here contains a hand-typed result; every number is read from
``results/summary.json``.
"""
from __future__ import annotations

import json

DS_NAME = {"synthetic": "Synthetic cohort", "eicu": "eICU-CRD demo (+ injected episodes)"}
DS_SHORT = {"synthetic": "Synthetic", "eicu": "eICU demo"}
METHOD_NAME = {
    "A": "A  Static thresholds, instant",
    "A2": "A2 Static + persistence (m=3)",
    "B": "B  Centralised ML, fixed priors",
    "C": "C  Adaptive threshold (no learning)",
    "D": "D  Centralised ML, adaptive",
    "E": "E  Local-only per site",
    "F": "F  Federated (FedAvg), adaptive",
}


def load(path="results/summary.json"):
    return json.load(open(path))


def pm(v, nd=2):
    if v is None or v.get("mean") is None:
        return "n/a"
    return f"{v['mean']:.{nd}f} ± {v['sd']:.{nd}f}"


def num(x, nd=2):
    return "n/a" if x is None else f"{x:.{nd}f}"


def ci(p, nd=3):
    if not p or p.get("ci95") is None:
        return "n/a"
    return f"{p['mean']:+.{nd}f} [{p['ci95'][0]:+.{nd}f}, {p['ci95'][1]:+.{nd}f}]"


def fmt_bytes(b):
    for unit, d in (("GB", 1e9), ("MB", 1e6), ("kB", 1e3)):
        if b >= d:
            return f"{b / d:.1f} {unit}"
    return f"{b:.0f} B"


def eps_str(e):
    if e is None:
        return "n/a"
    return "∞" if e == "inf" else (f"{e:.2f}" if e >= 0.1 else f"{e:.3f}")


def headlines(S, ds):
    d = S["datasets"][ds]
    m = d["methods"]
    g = lambda k, x: m[k][x]["mean"]
    h = {}
    h["fa_A"], h["fa_A2"], h["fa_C"], h["fa_D"], h["fa_F"], h["fa_B"] = (g(k, "fa_per_day") for k in ("A", "A2", "C", "D", "F", "B"))
    h["fa_cut_C_vs_A2"] = 1 - h["fa_C"] / h["fa_A2"]
    h["fa_cut_D_vs_A2"] = 1 - h["fa_D"] / h["fa_A2"]
    h["f1"] = {k: g(k, "f1") for k in m}
    h["auroc"] = {k: g(k, "auroc") for k in m}
    h["auprc"] = {k: g(k, "auprc") for k in m}
    h["recall"] = {k: g(k, "recall") for k in m}
    p = d["paired"]
    h["F_D"] = p["F_minus_D"]; h["F_B"] = p["F_minus_B"]; h["D_B"] = p["D_minus_B"]
    h["fed_matches"] = all(
        (p["F_minus_D"][x]["ci95"][0] <= 0 <= p["F_minus_D"][x]["ci95"][1]) or abs(p["F_minus_D"][x]["mean"]) < 0.01
        for x in ("f1", "auroc", "auprc"))
    # privacy: strongest noise whose F1 is not worse than F by more than one paired sd
    keep = None
    for r in d["privacy_utility"]:
        pk = p[f"{r['key']}_minus_F"]["f1"]
        if pk["ci95"] is not None and pk["ci95"][1] >= -0.005 and pk["mean"] > -0.03:
            if keep is None or r["sigma"] > keep["sigma"]:
                keep = r
    h["dp_keep"] = keep
    h["dp_first_loss"] = next((r for r in sorted(d["privacy_utility"], key=lambda r: r["sigma"])
                               if p[f"{r['key']}_minus_F"]["f1"]["ci95"] is not None
                               and p[f"{r['key']}_minus_F"]["f1"]["ci95"][1] < -0.02), None)
    h["rounds_conv"] = d["federated"]["rounds_to_converge"]["mean"]
    h["rounds_used"] = d["federated"]["rounds_used"]
    h["loss_gap"] = d["federated"]["final_loss_gap"]["mean"]
    return h
