"""Alarm-level and sample-level metrics, all in real time units.

An *alarm event* fires when the score has been above ``tau`` for ``m``
consecutive samples.  While the condition keeps holding the alarm re-fires every
``refire_min`` minutes (a persistent alarm keeps sounding; an always-on alarm
must not count as a single event).  An alarm firing inside an episode padded by
``tol_min`` minutes is a true positive, otherwise a false alarm.  An episode is
*detected* if at least one alarm fires in its padded window; its delay runs from
the episode start to the first such firing (never negative).  Several alarms
inside one already-detected episode are merged (not counted again).

Counts are additive across patients and sites, so threshold tuning only ever
needs aggregate counts (works federatedly).
"""
from __future__ import annotations

import math

import numpy as np

ZERO_COUNTS = dict(alarms=0, tp_alarms=0, episodes=0, detected=0, days=0.0)
REFIRE_MIN = 60.0


def runs(flag: np.ndarray, m: int):
    """Return [(start, end_exclusive)] of runs of True with length >= m."""
    f = np.concatenate(([0], np.asarray(flag, dtype=np.int8), [0]))
    d = np.diff(f)
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    keep = (ends - starts) >= m
    return list(zip(starts[keep].tolist(), ends[keep].tolist()))


def patient_counts(score, episodes, lo, hi, dt_min, tau, m, tol_min=30.0,
                   refire_min=REFIRE_MIN):
    """Counts and delays for one patient on the sample range [lo, hi).

    ``alarms`` = false alarms + detected episodes (merged); ``tp_alarms`` =
    detected episodes.
    """
    tol = int(math.ceil(tol_min / dt_min))
    refire = max(1, int(round(refire_min / dt_min)))
    s = np.asarray(score[lo:hi], dtype=float)
    flag = np.where(np.isnan(s), False, s > tau)
    fires = []
    for a0, a1 in runs(flag, m):
        fires.extend(range(a0 + m - 1, a1, refire))
    eps = [(a - lo, b - lo) for (a, b, _k) in episodes if a >= lo and b <= hi]
    first = [None] * len(eps)
    fa = 0
    for f in fires:
        hit = False
        for i, (e0, e1) in enumerate(eps):
            if e0 - tol <= f < e1 + tol:
                hit = True
                if first[i] is None:
                    first[i] = f
        fa += 0 if hit else 1
    delays = [max(0, f - eps[i][0]) * dt_min for i, f in enumerate(first) if f is not None]
    det = len(delays)
    c = dict(alarms=fa + det, tp_alarms=det, episodes=len(eps), detected=det,
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
    from sklearn.metrics import average_precision_score, roc_auc_score   # lazy: serving needs no sklearn
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
