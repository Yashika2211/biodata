import math

import numpy as np

from pvm import config as C
from pvm import features as F


def test_adaptive_state_learns_copd_baseline():
    """A patient whose normal SpO2 is ~90 stops looking abnormal."""
    rng = np.random.default_rng(0)
    st = F.new_state("adaptive")
    zs = []
    for _ in range(600):
        x = [80, 90 + rng.normal(0, 0.7), 16, 120, 36.8]
        F.update_state(st, x)
        zs.append(st["buf"][-1][1])
    assert abs(st["mu"][1] - 90) < 0.6
    assert abs(np.mean(zs[-100:])) < 0.6      # adapted
    assert zs[0] < -2.5                      # first sample is alarming vs prior


def test_static_mode_never_adapts():
    st = F.new_state("static")
    for _ in range(300):
        F.update_state(st, [80, 90, 16, 120, 36.8])
    assert st["buf"][-1][1] < -2.5


def test_nan_safety():
    st = F.new_state("adaptive")
    before = (list(st["mu"]), list(st["var"]), list(st["n"]))
    f = F.process_event(st, [float("nan")] * 5)
    assert all(math.isfinite(v) for v in f)
    assert f == [0.0] * C.NF
    assert (st["mu"], st["var"], st["n"]) == before    # no evidence, no update
    # implausible values are treated as missing too
    f = F.process_event(st, [999, 5, 500, 1, 10])
    assert f == [0.0] * C.NF


def test_state_json_round_trip_is_exact():
    rng = np.random.default_rng(1)
    st = F.new_state("adaptive")
    for _ in range(50):
        F.process_event(st, [80 + rng.normal(0, 3), 97, 16, 120, 36.8])
    st2 = F.state_from_json(F.state_to_json(st))
    assert st2 == st
    x = [85.0, 95.0, 18.0, 110.0, 37.2]
    assert F.process_event(st, x) == F.process_event(st2, x)


def test_winsorised_update_limits_outlier_influence():
    st = F.new_state("adaptive")
    for _ in range(200):
        F.update_state(st, [80, 97, 16, 120, 36.8])
    mu0 = st["mu"][0]
    F.update_state(st, [200, 97, 16, 120, 36.8])
    assert abs(st["mu"][0] - mu0) < 1.0


def test_window_features_shape_and_ranges():
    st = F.new_state("adaptive")
    f = None
    for k in range(20):
        f = F.process_event(st, [80 + k, 97, 16, 120, 36.8])
    assert len(f) == C.NF == 15
    assert all(m >= 0 for m in f[2 * C.NV:])          # max |z| is non-negative


def test_window_length_is_bounded():
    st = F.new_state("adaptive")
    for _ in range(100):
        F.update_state(st, [80, 97, 16, 120, 36.8])
    assert len(st["buf"]) == C.WINDOW


def test_current_z_uses_state_before_update():
    st = F.new_state("adaptive")
    for _ in range(100):
        F.update_state(st, [80, 97, 16, 120, 36.8])
    z = F.update_state(st, [140, 97, 16, 120, 36.8])[0]
    assert z > 5            # the outlier is judged against the old baseline


def test_slower_learning_while_abnormal():
    a, b = F.new_state("adaptive"), F.new_state("adaptive")
    for _ in range(150):
        F.update_state(a, [80, 97, 16, 120, 36.8]); F.update_state(b, [80, 97, 16, 120, 36.8])
    shift = [80, 97 - 6, 16, 120, 36.8]       # abnormal (large |z|)
    mild = [80, 97 - 1.0, 16, 120, 36.8]      # normal range
    for _ in range(20):
        F.update_state(a, shift); F.update_state(b, mild)
    moved_a, moved_b = 97 - a["mu"][1], 97 - b["mu"][1]
    # the abnormal shift is 6x larger but moves the baseline much less than 6x as far
    assert moved_a < 6 * moved_b
