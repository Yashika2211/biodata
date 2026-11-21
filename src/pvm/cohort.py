"""Patient container and the semi-synthetic episode injector.

Every dataset (synthetic or public) becomes a list of :class:`Patient`.
Episodes are injected by :func:`inject_episodes` so that none crosses the
train/test boundary (first 60 % of each series trains, last 40 % tests).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import config as C

TRAIN_FRAC = 0.6

# Peak deviation from the patient's own baseline per episode kind.
EPISODE_EFFECTS = {
    "sepsis":   {"hr": 35, "rr": 8, "temp": 1.6, "sbp": -25, "spo2": -2},
    "hypoxia":  {"spo2": -9, "rr": 7, "hr": 20},
    "shock":    {"sbp": -45, "hr": 35, "rr": 4, "spo2": -3},
    "brady":    {"hr": -28, "sbp": -30},
}


@dataclass
class Patient:
    pid: str
    site: str
    X: np.ndarray                    # (T, 5) vitals, NaN = missing
    y: np.ndarray                    # (T,) 1 inside an injected episode
    ep_id: np.ndarray                # (T,) episode index or -1
    episodes: list = field(default_factory=list)   # (start, end, kind)
    dt_min: float = C.DT_MIN
    phenotype: str = ""
    artefact: np.ndarray | None = None

    @property
    def T(self) -> int:
        return len(self.X)

    @property
    def split(self) -> int:
        return int(self.T * TRAIN_FRAC)

    @property
    def days(self) -> float:
        return self.T * self.dt_min / 1440.0


def inject_episodes(X: np.ndarray, rng: np.random.Generator, dt_min: float,
                    rate_per_day: float = 0.4, sev_range=(0.45, 1.25)):
    """Inject labelled deterioration episodes into ``X`` (a copy is returned).

    Episodes are placed separately inside the train and test regions, so none
    can cross ``int(T * TRAIN_FRAC)``.  Each has a linear ramp over the first
    ~half of its length, then a plateau, then a short recovery.
    """
    X = X.copy()
    T = len(X)
    split = int(T * TRAIN_FRAC)
    y = np.zeros(T, dtype=np.int8)
    ep_id = -np.ones(T, dtype=np.int32)
    episodes = []
    spd = 1440.0 / dt_min
    warm = int(0.25 * spd)             # let the baseline settle first
    kinds = list(EPISODE_EFFECTS)
    for lo, hi in ((warm, split), (split + int(0.1 * spd), T)):
        n_expected = rate_per_day * (hi - lo) / spd
        k = rng.poisson(n_expected)
        occupied = np.zeros(T, dtype=bool)
        for _ in range(k):
            dur = int(rng.uniform(1.5, 6.0) * 60 / dt_min)
            if hi - lo < dur + 4:
                continue
            for _try in range(20):
                s = int(rng.integers(lo, hi - dur))
                e = s + dur
                if not occupied[max(lo, s - int(2 * 60 / dt_min)):e + int(2 * 60 / dt_min)].any():
                    break
            else:
                continue
            occupied[s:e] = True
            kind = kinds[int(rng.integers(len(kinds)))]
            sev = rng.uniform(*sev_range)
            ramp_n = max(2, int(dur * rng.uniform(0.4, 0.6)))
            rec_n = max(1, int(dur * 0.15))
            prof = np.ones(dur)
            prof[:ramp_n] = np.linspace(0.0, 1.0, ramp_n)
            prof[-rec_n:] = np.linspace(1.0, 0.3, rec_n)
            for v, delta in EPISODE_EFFECTS[kind].items():
                j = C.VITALS.index(v)
                seg = X[s:e, j] + sev * delta * prof
                lo_v, hi_v = C.VALID_RANGE[v]
                seg = np.clip(seg, lo_v + 0.5, hi_v - 0.0)
                if v == "spo2":
                    seg = np.minimum(seg, 100.0)
                X[s:e, j] = np.where(np.isnan(X[s:e, j]), np.nan, seg)
            idx = len(episodes)
            y[s:e] = 1
            ep_id[s:e] = idx
            episodes.append((s, e, kind))
    order = sorted(range(len(episodes)), key=lambda i: episodes[i][0])
    remap = {old: new for new, old in enumerate(order)}
    ep_id = np.array([remap.get(int(i), -1) if i >= 0 else -1 for i in ep_id], dtype=np.int32)
    episodes = [episodes[i] for i in order]
    return X, y, ep_id, episodes
