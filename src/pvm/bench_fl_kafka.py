"""Run FedAvg over Kafka topics on the synthetic cohort; record measured bytes and equality
with the in-process simulation -> results/fl_kafka.json."""
from __future__ import annotations

import json
import os

import numpy as np

from . import federated as FED
from . import methods as MT
from .data.synthetic import make_cohort
from .stream.fl_kafka import fedavg_over_kafka


def main(rounds=100):
    ps = make_cohort(160, 4, seed=0)
    fa = MT.featurize(ps, "adaptive")
    sites, mean, sd, cw, std = MT.prepare_global(ps, fa)
    sl = list(std.values())
    ref = FED.fedavg(sl, cw, rounds=rounds)
    st = fedavg_over_kafka(sl, cw, rounds=rounds)
    out = dict(rounds=rounds, sites=len(sl), parameters=int(sl[0][0].shape[1]),
               bytes_up_measured=st["bytes_up"], bytes_down_measured=st["bytes_down"],
               bytes_analytic_float64=ref.bytes_exchanged, seconds=st["seconds"],
               max_abs_diff_vs_in_process=float(np.max(np.abs(st["theta"] - ref.theta))))
    os.makedirs("results", exist_ok=True)
    json.dump(out, open("results/fl_kafka.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
