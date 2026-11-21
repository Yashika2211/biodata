import json

import numpy as np

from pvm import models as ML
from pvm import serving as S
from pvm.data.synthetic import make_cohort


def test_no_alert_ever_contains_a_vital_or_raw_id():
    ps = make_cohort(12, 2, seed=51, days=2.0)
    model = ML.Model(np.zeros(16), np.zeros(15), np.ones(15), tau=-1.0, m=1)   # alarms constantly
    runner = S.LocalRunner(model, salt="s")
    alerts = []
    for p in ps[:4]:
        evs = [dict(pid=p.pid, site=p.site, seq=k, ts=k, hr=p.X[k, 0], spo2=p.X[k, 1], rr=p.X[k, 2],
                    sbp=p.X[k, 3], temp=p.X[k, 4]) for k in range(60)]
        alerts += runner.process_batch(evs)[0]
    assert len(alerts) > 100
    blob = json.dumps(alerts)
    assert all(p.pid not in blob for p in ps)
    for a in alerts:
        assert set(a) <= {"pid_hash", "site", "ts", "score", "model", "producer_ts_ms"}
