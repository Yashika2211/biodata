import numpy as np

from pvm import config as C
from pvm import features as F
from pvm import metrics as M
from pvm import methods as MT
from pvm import models as ML
from pvm import serving as S
from pvm.data.synthetic import make_cohort


def _model(patients):
    fa = MT.featurize(patients, "adaptive")
    X, y = MT.train_rows(patients, fa)
    mean, sd = ML.standardiser([ML.moments(X)])
    cw = ML.class_weights(int(y.sum()), len(y))
    th = ML.fit_central(ML.aug((X - mean) / sd), y, cw)
    return ML.Model(th, mean, sd, tau=1.0, m=3), fa


def test_serving_scores_equal_offline_exactly_with_state_serialised():
    ps = make_cohort(6, 2, seed=11, days=2.0)
    model, fa = _model(ps)
    offline = model.score(fa[ps[0].pid])
    p = ps[0]
    rng = np.random.default_rng(0)
    runner = S.LocalRunner(model)
    got = {}
    i = 0
    while i < p.T:                       # random micro-batch sizes, state -> JSON -> state
        n = int(rng.integers(1, 40))
        evs = [dict(pid=p.pid, site=p.site, seq=k, ts=k,
                    **{v: (None if np.isnan(p.X[k, j]) else float(p.X[k, j]))
                       for j, v in enumerate(C.VITALS)}) for k in range(i, min(p.T, i + n))]
        _, sc = runner.process_batch(evs)
        got.update({k[1]: v for k, v in sc.items()})
        i += n
    serving = np.array([got[k] for k in range(p.T)])
    assert np.array_equal(serving, offline)            # bit-for-bit


def test_serving_alarms_equal_offline_alarms():
    ps = make_cohort(6, 2, seed=12, days=2.0)
    model, fa = _model(ps)
    p = ps[1]
    offline = model.score(fa[p.pid])
    model.tau = float(np.percentile(offline, 90))     # enough alarms to be a real test
    fires = []
    for a0, a1 in M.runs(offline > model.tau, model.m):
        fires += list(range(a0 + model.m - 1, a1, S.REFIRE_SAMPLES))
    st = S.init_state(model)
    got = []
    for k in range(p.T):
        st = F.state_from_json(F.state_to_json(st))     # serialise every event
        _, fired = S.step(model, st, p.X[k])
        if fired:
            got.append(k)
    assert got == fires and len(fires) > 0


def test_alert_contains_no_vitals_and_hashes_id():
    ps = make_cohort(4, 2, seed=13, days=1.0)
    model, _ = _model(ps)
    a = S.make_alert(model, "patient-42", "site0", 1000, 3.14159, "salt", 999)
    assert set(a) == {"pid_hash", "site", "ts", "score", "model", "producer_ts_ms"}
    assert "patient-42" not in str(a)
    assert S.pseudonym("p", "s1") != S.pseudonym("p", "s2")
