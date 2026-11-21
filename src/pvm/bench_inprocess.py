"""In-process serving latency: one event through ``serving.step`` (no Kafka)."""
from __future__ import annotations

import json
import os
import time

import numpy as np

from . import config as C
from . import features as F
from . import models as ML
from . import serving as S
from .data import synthetic as SY


def run(n_events=200_000, model_path="models/model.json"):
    model = ML.Model.from_json(open(model_path).read())
    ps = SY.make_cohort(450, 4, seed=123)
    events = []
    for p in ps:
        for k in range(p.split, p.T):
            events.append((p.pid, p.X[k]))
    events = events[:n_events]
    states = {}
    lat = np.empty(len(events))
    c0 = time.process_time(); w0 = time.perf_counter()
    for i, (pid, x) in enumerate(events):
        t = time.perf_counter_ns()
        st = states.get(pid) or states.setdefault(pid, S.init_state(model))
        S.step(model, st, x)
        lat[i] = time.perf_counter_ns() - t
    cpu = time.process_time() - c0; wall = time.perf_counter() - w0
    # full path with JSON state (de)serialisation per event (what a stateless micro-batch pays)
    lat2 = []
    js = {}
    for pid, x in events[:20_000]:
        t = time.perf_counter_ns()
        st = F.state_from_json(js[pid]) if pid in js else S.init_state(model)
        S.step(model, st, x)
        js[pid] = F.state_to_json(st)
        lat2.append(time.perf_counter_ns() - t)
    pct = lambda a: {f"p{q}": float(np.percentile(a, q)) / 1000.0 for q in (50, 95, 99)}
    return dict(n_events=len(events), step_us=pct(lat), step_json_state_us=pct(lat2),
                throughput_eps=len(events) / wall,
                cpu_seconds_per_million_events=cpu / len(events) * 1e6)


def main():
    out = run()
    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/bench_inprocess.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
