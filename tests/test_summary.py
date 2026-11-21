import numpy as np

from pvm import summary as SM


def test_mean_sd_ignores_nan_and_handles_inf_strings():
    v = SM.ms([1.0, 2.0, None, 3.0])
    assert v["n"] == 3 and abs(v["mean"] - 2.0) < 1e-12
    assert SM.ms(["inf", "inf"])["mean"] == float("inf")


def test_paired_difference_ci_contains_true_shift():
    rng = np.random.default_rng(0)
    a = (0.5 + rng.normal(0, 0.01, 5)).tolist()
    b = (0.4 + rng.normal(0, 0.01, 5)).tolist()
    p = SM.paired(a, b)
    assert p["ci95"][0] < 0.1 < p["ci95"][1] and p["n"] == 5


def test_paired_single_seed_has_no_ci():
    assert SM.paired([1.0], [0.5])["ci95"] is None
