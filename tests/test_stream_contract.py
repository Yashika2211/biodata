import json

import numpy as np

from pvm import config as C
from pvm import serving as S
from pvm.data.synthetic import make_cohort
from pvm.stream import consumer as CONS
from pvm.stream import producer as PROD


def test_event_json_has_spark_schema_fields():
    msg = json.loads(S.event_json("p1", "site0", 7, 2100000, 1700000000000, [80, 97, 16, float("nan"), 36.8]))
    assert set(msg) == {"pid", "site", "seq", "ts", "producer_ts_ms", *C.VITALS}
    assert msg["sbp"] is None and msg["hr"] == 80.0


def test_producer_interleaves_patients_and_uses_test_region_only():
    ps = make_cohort(5, 2, seed=41, days=2.0)
    ev = list(PROD.build_events(ps, n_events=10))
    assert [e[0] for e in ev[:5]] == [p.pid for p in ps]          # round robin over patients
    assert all(e[2] >= next(p for p in ps if p.pid == e[0]).split for e in ev)


def test_consumer_percentiles_and_contract():
    out = CONS.percentiles([10, 20, 30, 40, 1000])
    assert out["p50"] == 30 and out["p99"] > 900 and out["n"] == 5
    assert CONS.percentiles([]) == {}
    ok = {"pid_hash": "x", "site": "s", "ts": 1, "score": 1.0, "model": "m", "producer_ts_ms": 2}
    assert set(ok) <= CONS.ALLOWED and not (set(ok) & CONS.VITAL_KEYS)
    assert {"hr"} & CONS.VITAL_KEYS and not ({"hr", "pid_hash"} <= CONS.ALLOWED)
