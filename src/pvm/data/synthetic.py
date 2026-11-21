"""Synthetic cohort generator (several phenotypes, non-IID sites).

Real physiology it mimics: patient-specific baselines (COPD patients live at
SpO2 ~90 %, athletes at HR ~52), AR(1) within-patient noise, circadian drift,
missing values / probe-off bursts, and benign motion artefacts of 1-8 samples
that are labelled *normal*.
"""
from __future__ import annotations

import numpy as np

from .. import config as C
from ..cohort import Patient, inject_episodes

# phenotype -> baseline (hr, spo2, rr, sbp, temp)
PHENOTYPES = {
    "normal":       (75, 97.0, 16, 120, 36.8),
    "athlete":      (52, 98.0, 13, 110, 36.6),
    "copd":         (88, 90.0, 20, 125, 36.8),
    "hypertensive": (78, 96.0, 16, 152, 36.8),
    "tachycardic":  (105, 96.0, 18, 118, 36.9),
    "low_bp":       (70, 97.0, 15, 96, 36.7),
}
JITTER_SD = np.array([4.0, 0.7, 1.0, 6.0, 0.12])     # between-patient spread
NOISE_SD = np.array([4.5, 0.9, 1.3, 6.0, 0.15])      # within-patient (stationary)
CIRC_AMP = np.array([4.0, 0.3, 1.0, 5.0, 0.25])
PHI = 0.85


def site_mixes(n_sites: int, rng: np.random.Generator, concentration: float = 0.5):
    """Per-site phenotype probabilities (Dirichlet => non-IID sites)."""
    k = len(PHENOTYPES)
    return rng.dirichlet(np.full(k, concentration), size=n_sites)


def _artefacts(T, rng, dt_min, rate_per_day=2.5):
    mask = np.zeros(T, dtype=bool)
    delta = np.zeros((T, C.NV))
    n = rng.poisson(rate_per_day * T * dt_min / 1440.0)
    for _ in range(n):
        L = int(rng.integers(1, 9))
        s = int(rng.integers(0, max(1, T - L)))
        mask[s:s + L] = True
        for j in rng.choice(C.NV, size=int(rng.integers(1, 3)), replace=False):
            v = C.VITALS[j]
            mag = {"hr": rng.uniform(25, 60), "spo2": -rng.uniform(6, 14),
                   "rr": rng.uniform(8, 18), "sbp": rng.choice([-1, 1]) * rng.uniform(25, 50),
                   "temp": rng.choice([-1, 1]) * rng.uniform(0.8, 1.5)}[v]
            delta[s:s + L, j] += mag * rng.uniform(0.8, 1.2)
    return mask, delta


def make_patient(pid: str, site: str, phenotype: str, days: float,
                 rng: np.random.Generator, dt_min: float = C.DT_MIN,
                 episode_rate: float = 0.4) -> Patient:
    T = int(days * 1440 / dt_min)
    base = np.array(PHENOTYPES[phenotype], dtype=float) + rng.normal(0, 1, C.NV) * JITTER_SD
    t_h = np.arange(T) * dt_min / 60.0
    phase = rng.uniform(-2, 2)
    circ = CIRC_AMP * np.sin(2 * np.pi * (t_h[:, None] - 14 + phase) / 24.0)
    innov = NOISE_SD * np.sqrt(1 - PHI ** 2)
    noise = np.zeros((T, C.NV))
    noise[0] = rng.normal(0, NOISE_SD)
    eps = rng.normal(0, 1, (T, C.NV)) * innov
    for t in range(1, T):
        noise[t] = PHI * noise[t - 1] + eps[t]
    X = base + circ + noise
    # clinical-style rounding (monitors report integers / 0.1 C)
    X[:, [0, 1, 2, 3]] = np.round(X[:, [0, 1, 2, 3]])
    X[:, 4] = np.round(X[:, 4], 1)
    X[:, 1] = np.minimum(X[:, 1], 100.0)
    X, y, ep, episodes = inject_episodes(X, rng, dt_min, rate_per_day=episode_rate)
    # benign motion artefacts (label stays 0 unless inside an episode)
    amask, adelta = _artefacts(T, rng, dt_min)
    X = X + adelta
    X[:, 1] = np.minimum(X[:, 1], 100.0)
    # missing values: random dropouts and probe-off bursts
    miss = rng.random((T, C.NV)) < 0.015
    for _ in range(rng.poisson(2.0 * days)):
        s = int(rng.integers(0, T)); L = int(rng.integers(3, 25))
        j = rng.choice(C.NV, size=int(rng.integers(1, C.NV + 1)), replace=False)
        miss[s:s + L, j] = True
    X[miss] = np.nan
    return Patient(pid=pid, site=site, X=X, y=y, ep_id=ep, episodes=episodes,
                   dt_min=dt_min, phenotype=phenotype, artefact=amask)


def make_cohort(n_patients: int = 160, n_sites: int = 4, days: float = 4.0,
                seed: int = 0, dt_min: float = C.DT_MIN,
                concentration: float = 0.5, episode_rate: float = 0.4):
    rng = np.random.default_rng(seed)
    names = list(PHENOTYPES)
    mixes = site_mixes(n_sites, rng, concentration)
    patients = []
    for i in range(n_patients):
        s = i % n_sites
        ph = names[int(rng.choice(len(names), p=mixes[s]))]
        patients.append(make_patient(f"syn{seed}-{i:04d}", f"site{s}", ph, days,
                                     rng, dt_min, episode_rate))
    return patients
