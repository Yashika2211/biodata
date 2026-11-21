"""Serving path: identical feature code, one event at a time.

``step`` is what the Spark job runs per event.  The only state is a JSON-able
dict (feature state + the alarm run counter), so it can be serialised between
micro-batches.  ``LocalRunner`` drives the same code without Kafka.
"""
from __future__ import annotations

import hashlib
import json

from . import config as C
from . import features as F
from . import metrics as M
from . import models as ML

REFIRE_SAMPLES = int(round(M.REFIRE_MIN / C.DT_MIN))


def pseudonym(pid: str, salt: str) -> str:
    """Salted hash of the patient id; the only identifier leaving the site."""
    return hashlib.sha256((salt + "|" + pid).encode()).hexdigest()[:16]


def init_state(model: ML.Model) -> dict:
    st = F.new_state(model.mode, model.alpha)
    st["run"] = 0
    return st


def step(model: ML.Model, state: dict, x, refire: int = REFIRE_SAMPLES):
    """Process one event. Returns (score, fired). Mutates ``state``."""
    feats = F.process_event(state, x)
    score = model.score_one(feats)
    if score > model.tau:
        state["run"] += 1
    else:
        state["run"] = 0
    fired = state["run"] >= model.m and (state["run"] - model.m) % refire == 0
    return score, fired


def make_alert(model, pid, site, ts_ms, score, salt, producer_ts_ms=None) -> dict:
    """Alert payload: salted-hash id, site, timestamp, score, model tag. No vitals."""
    a = {"pid_hash": pseudonym(pid, salt), "site": site, "ts": int(ts_ms),
         "score": round(float(score), 4), "model": model.tag}
    if producer_ts_ms is not None:
        a["producer_ts_ms"] = int(producer_ts_ms)     # for end-to-end latency only
    return a


def event_json(pid, site, seq, ts_ms, producer_ts_ms, x) -> str:
    d = {"pid": pid, "site": site, "seq": int(seq), "ts": int(ts_ms),
         "producer_ts_ms": int(producer_ts_ms)}
    for v, val in zip(C.VITALS, x):
        d[v] = None if val != val else float(val)
    return json.dumps(d, separators=(",", ":"))


class LocalRunner:
    """Kafka-free runner that mimics micro-batches with JSON state round trips."""

    def __init__(self, model: ML.Model, salt: str = "demo-salt"):
        self.model = model
        self.salt = salt
        self.states: dict[str, str] = {}

    def process_batch(self, events: list[dict]):
        """events: dicts with pid, site, seq, ts, vitals. Returns alerts, scores."""
        by_pid: dict[str, list] = {}
        for e in events:
            by_pid.setdefault(e["pid"], []).append(e)
        alerts, scores = [], {}
        for pid, evs in by_pid.items():
            evs.sort(key=lambda e: e["seq"])
            st = F.state_from_json(self.states[pid]) if pid in self.states else init_state(self.model)
            for e in evs:
                x = [e.get(v) for v in C.VITALS]
                x = [float("nan") if a is None else a for a in x]
                score, fired = step(self.model, st, x)
                scores[(pid, e["seq"])] = score
                if fired:
                    alerts.append(make_alert(self.model, pid, e["site"], e["ts"], score,
                                             self.salt, e.get("producer_ts_ms")))
            self.states[pid] = F.state_to_json(st)
        return alerts, scores
