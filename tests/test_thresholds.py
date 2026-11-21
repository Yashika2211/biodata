import numpy as np

from pvm import thresholds as T
from pvm.data.synthetic import make_cohort


def _scores(ps, noise=0.5, seed=0):
    rng = np.random.default_rng(seed)
    return {p.pid: p.y * 3.0 + rng.normal(0, noise, p.T) for p in ps}


def test_tuning_with_aggregate_counts_equals_pooled_tuning():
    ps = make_cohort(24, 3, seed=2, days=3.0)
    sc = _scores(ps)
    by_site = {}
    for p in ps:
        by_site.setdefault(p.site, []).append(p)
    fed, _ = T.tune(list(by_site.values()), sc, T.LOGIT_GRID, 3)
    pooled, _ = T.tune([ps], sc, T.LOGIT_GRID, 3)
    assert fed == pooled


def test_good_scorer_gets_a_sensible_threshold():
    ps = make_cohort(24, 3, seed=2, days=3.0)
    sc = _scores(ps, noise=0.3)
    tau, f1 = T.tune([ps], sc, T.LOGIT_GRID, 3)
    assert 0.5 < tau < 3.0 and f1 > 0.5
