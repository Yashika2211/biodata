"""Threshold tuning from aggregate counts only.

Each site evaluates a fixed grid of thresholds on its own training region and
shares, per threshold, only (alarms, true-positive alarms, episodes, detected,
patient-days).  The coordinator sums them and picks the F1-maximising
threshold, so the same procedure works centrally and federatedly.
"""
from __future__ import annotations

import numpy as np

from . import metrics as M

BURN_IN = 24          # samples ignored at the start of a series when tuning
LOGIT_GRID = np.round(np.arange(-8.0, 8.01, 0.1), 3)
Z_GRID = np.round(np.arange(0.5, 8.01, 0.05), 3)


def site_counts(patients, scores, grid, m, tol_min=30.0):
    """Counts per grid point for one site's *training* region."""
    rows = []
    for tau in grid:
        tot = dict(M.ZERO_COUNTS)
        for p in patients:
            c, _ = M.patient_counts(scores[p.pid], p.episodes, BURN_IN, p.split,
                                    p.dt_min, tau, m, tol_min)
            tot = M.add_counts(tot, c)
        rows.append(tot)
    return rows


def choose_threshold(site_rows, grid):
    """Sum per-site count tables and return the F1-maximising threshold."""
    best, best_f1 = grid[len(grid) // 2], -1.0
    for i, tau in enumerate(grid):
        tot = dict(M.ZERO_COUNTS)
        for rows in site_rows:
            tot = M.add_counts(tot, rows[i])
        f1 = M.summarise(tot, [])["f1"]
        if f1 >= best_f1 - 1e-12:   # ties -> higher (more conservative) threshold
            best, best_f1 = float(tau), f1
    return best, best_f1


def tune(patients_by_site, scores, grid, m, tol_min=30.0):
    rows = [site_counts(ps, scores, grid, m, tol_min) for ps in patients_by_site]
    return choose_threshold(rows, grid)
