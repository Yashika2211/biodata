"""Renyi-DP accountant for the (Poisson-)subsampled Gaussian mechanism.

Epsilon here is **record-level**: it bounds the influence of one training row
(one patient-time-step feature vector).  It is *not* patient-level privacy:
one patient contributes hundreds of correlated rows.

RDP of the subsampled Gaussian for integer orders follows Mironov, Talwar &
Zhang (2019), the integer-order expansion also used by Abadi et al. (2016):

    eps_alpha = 1/(alpha-1) * log sum_{k=0..alpha} C(alpha,k) (1-q)^(alpha-k) q^k
                                  * exp((k^2-k) / (2 sigma^2))

Conversion to (eps, delta)-DP uses the tighter bound of Balle et al. (2020).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.special import gammaln, logsumexp

ORDERS = list(range(2, 64)) + [80, 96, 128, 192, 256]


def _log_binom(n, k):
    return gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)


def rdp_subsampled_gaussian(q: float, sigma: float, alpha: int) -> float:
    """RDP at integer order ``alpha`` for one step."""
    if sigma <= 0:
        return math.inf
    if q == 0:
        return 0.0
    if q >= 1.0:
        return alpha / (2.0 * sigma ** 2)
    k = np.arange(alpha + 1)
    logs = (_log_binom(alpha, k) + (alpha - k) * math.log1p(-q) + k * math.log(q)
            + (k * k - k) / (2.0 * sigma ** 2))
    return float(logsumexp(logs) / (alpha - 1))


def compute_rdp(q: float, sigma: float, steps: int, orders=ORDERS):
    return np.array([steps * rdp_subsampled_gaussian(q, sigma, a) for a in orders])


def rdp_to_eps(rdp, delta: float, orders=ORDERS) -> float:
    best = math.inf
    for r, a in zip(rdp, orders):
        eps = r + math.log((a - 1) / a) - (math.log(delta) + math.log(a)) / (a - 1)
        best = min(best, eps)
    return max(best, 0.0)


def epsilon(q: float, sigma: float, steps: int, delta: float = 1e-5) -> float:
    """Record-level epsilon after ``steps`` DP-SGD steps."""
    if sigma <= 0:
        return math.inf
    return rdp_to_eps(compute_rdp(q, sigma, steps), delta)
