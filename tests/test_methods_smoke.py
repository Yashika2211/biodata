import numpy as np

from pvm import methods as MT
from pvm.data.synthetic import make_cohort


def test_all_methods_run_and_adaptive_beats_static_on_false_alarms():
    ps = make_cohort(48, 4, seed=21, days=3.0)
    res, ex = MT.run_methods(ps, fed_rounds=60, sigmas=(2.0, 128.0), dp_rounds=40)
    for k in ("A", "A2", "B", "C", "D", "E", "F", "G@2.0", "G@128.0"):
        assert k in res
        assert 0.0 <= res[k]["f1"] <= 1.0
    assert res["C"]["fa_per_day"] < res["A2"]["fa_per_day"]
    assert res["A2"]["fa_per_day"] <= res["A"]["fa_per_day"]
    assert res["G@128.0"]["epsilon"] < res["G@2.0"]["epsilon"]
    assert res["F"]["auroc"] > 0.6


def test_perfect_f1_is_a_red_flag():
    """No method should be near-perfect on this noisy benchmark."""
    ps = make_cohort(48, 4, seed=22, days=3.0)
    res, _ = MT.run_methods(ps, fed_rounds=40, which=("A", "A2", "C", "D"))
    assert max(r["f1"] for r in res.values()) < 0.95


def test_featurize_is_deterministic():
    ps = make_cohort(6, 2, seed=23, days=2.0)
    a = MT.featurize(ps, "adaptive"); b = MT.featurize(ps, "adaptive")
    assert all(np.array_equal(a[k], b[k]) for k in a)
