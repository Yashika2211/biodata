"""Alarm-level and sample-level metrics, all in real time units.

An *alarm* is a run of >= m consecutive samples with score > tau.  It fires
at the m-th sample of the run.  It is a true positive if its span overlaps an
episode padded by ``tol_min`` minutes, otherwise a false alarm.  An episode is
*detected* if at least one alarm overlaps it; its delay is measured from the
episode start to the first such alarm firing (never negative).

Counts are additive across patients and sites, so threshold tuning only ever
needs aggregate counts (works federatedly).
"""
from __future__ import annotations

import math

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

ZERO_COUNTS = dict(alarms=0, tp_alarms=0, episodes=0, detected=0, days=0.0)


def runs(flag: np.ndarray, m: int):
    """Yield (start, end_exclusive) of runs of True with length >= m."""
    out = []
    n = len(flag)
    i = 0
    while i < n:
        if flag[i]:
            j = i
            while j < n and flag[j]:
                j += 1
            if j - i >= m:
                out.append((i, j))
            i = j
        else:
            i += 1
    return out


def patient_counts(score, episodes, lo, hi, dt_min, tau, m, tol_min=30.0):
    """Counts and delays for one patient on the sample range [lo, hi)."""
    tol = int(math.ceil(tol_min / dt_min))
    s = np.asarray(score[lo:hi], dtype=float)
    flag = np.where(np.isnan(s), False, s > tau)
    al = runs(flag, m)
    eps = [(a, b) for (a, b, _k) in episodes if a >= lo and b <= hi]
    eps = [(a - lo, b - lo) for a, b in eps]
    tp = 0
    first_fire = {i: None for i in range(len(eps))}
    for (a0, a1) in al:
        fire = a0 + m - 1
        hit = False
        for i, (e0, e1) in enumerate(eps):
            if a0 < e1 + tol and a1 > e0 - tol:
                hit = True
                if first_fire[i] is None or fire < first_fire[i]:
                    first_fire[i] = fire
        tp += int(hit)
    delays = [max(0, f - eps[i][0]) * dt_min for i, f in first_fire.items() if f is not None]
    c = dict(alarms=len(al), tp_alarms=tp, episodes=len(eps), detected=len(delays),
             days=(hi - lo) * dt_min / 1440.0)
    return c, delays


def add_counts(a: dict, b: dict) -> dict:
    return {k: a[k] + b[k] for k in a}


def summarise(counts: dict, delays) -> dict:
    al, tp = counts["alarms"], counts["tp_alarms"]
    ne, nd = counts["episodes"], counts["detected"]
    prec = tp / al if al else float("nan")
    rec = nd / ne if ne else float("nan")
    f1 = (2 * prec * rec / (prec + rec)) if al and ne and (prec + rec) > 0 else 0.0
    return dict(precision=prec, recall=rec, f1=f1,
                fa_per_day=(al - tp) / counts["days"] if counts["days"] else float("nan"),
                delay_min=float(np.median(delays)) if len(delays) else float("nan"),
                alarms=al, episodes=ne)


def evaluate_alarms(patients, scores, tau, m, which="test", tol_min=30.0):
    """Aggregate alarm metrics over patients (scores: dict pid -> (T,) array)."""
    tot = dict(ZERO_COUNTS)
    delays = []
    for p in patients:
        lo, hi = (p.split, p.T) if which == "test" else (0, p.split)
        c, d = patient_counts(scores[p.pid], p.episodes, lo, hi, p.dt_min, tau, m, tol_min)
        tot = add_counts(tot, c)
        delays += d
    return summarise(tot, delays), tot


def sample_metrics(patients, scores, which="test"):
    ys, ss = [], []
    for p in patients:
        lo, hi = (p.split, p.T) if which == "test" else (0, p.split)
        s = np.asarray(scores[p.pid][lo:hi], dtype=float)
        ok = ~np.isnan(s)
        ys.append(p.y[lo:hi][ok]); ss.append(s[ok])
    y = np.concatenate(ys); s = np.concatenate(ss)
    if y.min() == y.max():
        return dict(auroc=float("nan"), auprc=float("nan"))
    return dict(auroc=float(roc_auc_score(y, s)), auprc=float(average_precision_score(y, s)))
