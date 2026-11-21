"""Kafka-free demo: stream one synthetic patient through the serving path.

    PYTHONPATH=src python examples/local_runner_demo.py

Uses the same ``pvm.serving`` code as the Spark job (JSON state between micro-batches).
"""
import numpy as np

from pvm import config as C
from pvm import models as ML
from pvm import serving as S
from pvm.data.synthetic import make_patient


def main(model_path="models/model.json"):
    model = ML.Model.from_json(open(model_path).read())
    p = make_patient("demo-patient", "site0", "copd", 4.0, np.random.default_rng(3))
    runner = S.LocalRunner(model, salt="demo-salt")
    alerts = []
    batch = 12                                   # one micro-batch = 1 hour of 5-minute samples
    for lo in range(p.split, p.T, batch):
        events = [dict(pid=p.pid, site=p.site, seq=k, ts=k * 300_000,
                       **{v: (None if np.isnan(p.X[k, j]) else float(p.X[k, j]))
                          for j, v in enumerate(C.VITALS)})
                  for k in range(lo, min(lo + batch, p.T))]
        a, _ = runner.process_batch(events)
        alerts += a
    print(f"{len(alerts)} alerts over {(p.T - p.split) * p.dt_min / 60:.0f} h; episodes in test region: "
          f"{[(s, e, k) for s, e, k in p.episodes if s >= p.split]}")
    for a in alerts[:5]:
        print(a)                                  # note: no vital values, hashed id only


if __name__ == "__main__":
    main()
