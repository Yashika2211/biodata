import numpy as np

from pvm import config as C
from pvm.cohort import EPISODE_EFFECTS, inject_episodes


def _flat(T=1152):
    return np.tile(np.array([75.0, 97.0, 16.0, 120.0, 36.8]), (T, 1))


def test_injection_changes_only_episode_samples():
    X0 = _flat()
    X, y, ep, eps = inject_episodes(X0, np.random.default_rng(0), 5.0, rate_per_day=2.0)
    assert len(eps) > 0
    changed = np.any(X != X0, axis=1)
    assert not changed[y == 0].any()
    assert changed[y == 1].sum() > 0.5 * y.sum()


def test_ramp_starts_gently_and_peaks_later():
    X0 = _flat()
    X, y, ep, eps = inject_episodes(X0, np.random.default_rng(1), 5.0, rate_per_day=2.0)
    s, e, kind = eps[0]
    v = C.VITALS.index(next(iter(EPISODE_EFFECTS[kind])))
    dev = np.abs(X[s:e, v] - X0[s:e, v])
    assert dev[:3].max() < dev.max() * 0.5


def test_nan_stays_nan():
    X0 = _flat(); X0[300:400, :] = np.nan
    X, *_ = inject_episodes(X0, np.random.default_rng(2), 5.0, rate_per_day=3.0)
    assert np.isnan(X[300:400]).all()


def test_values_stay_physiologically_valid():
    X, *_ = inject_episodes(_flat(), np.random.default_rng(3), 5.0, rate_per_day=4.0)
    for j, v in enumerate(C.VITALS):
        lo, hi = C.VALID_RANGE[v]
        assert X[:, j].min() >= lo and X[:, j].max() <= hi
