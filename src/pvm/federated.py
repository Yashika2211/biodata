"""Simulated federated training: FedAvg and DP-FedAvg (DP-SGD at each site).

The sites never exchange rows; each round a site receives the global theta,
runs ``local_steps`` gradient steps on its own data and returns its new theta.
The server averages weighted by site record counts.  (Simulated in-process;
see the report's Limitations.)

DP variant: every local step samples a Poisson batch (rate q), clips each
record's gradient to L2 norm <= clip, sums, adds N(0, (sigma*clip)^2) noise and
divides by the expected batch size.  Epsilon is record-level (see privacy.py)
and reported as the worst case over sites.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from . import models as ML
from . import privacy as P


@dataclass
class FedResult:
    theta: np.ndarray
    rounds: int
    loss_history: list = field(default_factory=list)
    central_loss: float = float("nan")
    epsilon: float = float("inf")          # worst case over sites; inf = non-private
    train_seconds: float = 0.0
    bytes_exchanged: int = 0
    rounds_to_converge: int | None = None


def _local_full_batch(theta, Xa, y, cw, steps, lr, l2):
    th = theta.copy()
    n = len(y)
    for _ in range(steps):
        g = ML.record_grads(th, Xa, y, cw).sum(0) / n
        g[:-1] += l2 * th[:-1]
        th -= lr * g
    return th


def _local_dp(theta, Xa, y, cw, steps, lr, l2, q, sigma, clip, rng):
    th = theta.copy()
    n = len(y)
    exp_b = max(q * n, 1.0)
    for _ in range(steps):
        mask = rng.random(n) < q
        if mask.any():
            g = ML.record_grads(th, Xa[mask], y[mask], cw)
            norms = np.linalg.norm(g, axis=1, keepdims=True)
            g = g / np.maximum(1.0, norms / clip)
            gs = g.sum(0)
        else:
            gs = np.zeros_like(th)
        gs = gs + rng.normal(0.0, sigma * clip, size=th.shape)
        grad = gs / exp_b
        grad[:-1] += l2 * th[:-1]
        th -= lr * grad
    return th


def fedavg(sites, cw, rounds=300, local_steps=3, lr=0.3, l2=ML.L2,
           dp_sigma=None, clip=10.0, q=0.02, delta=1e-5, seed=0,
           central_loss=None, tol=1e-3, record_every=1):
    """Train by FedAvg over ``sites`` = list of (Xa_standardised_aug, y).

    ``central_loss`` is used only as a *diagnostic* (rounds-to-converge).
    """
    rng = np.random.default_rng(seed)
    d = sites[0][0].shape[1]
    theta = np.zeros(d)
    ns = np.array([len(y) for _, y in sites], dtype=float)
    wts = ns / ns.sum()
    Xall = np.vstack([s[0] for s in sites]); yall = np.concatenate([s[1] for s in sites])
    res = FedResult(theta=theta, rounds=rounds)
    if central_loss is not None:
        res.central_loss = central_loss
    t0 = time.process_time()
    for r in range(1, rounds + 1):
        new = np.zeros(d)
        for w, (Xa, y) in zip(wts, sites):
            if dp_sigma is None:
                loc = _local_full_batch(theta, Xa, y, cw, local_steps, lr, l2)
            else:
                loc = _local_dp(theta, Xa, y, cw, local_steps, lr, l2, q, dp_sigma, clip, rng)
            new += w * loc
        theta = new
        if r % record_every == 0 or r == rounds:
            L = ML.objective(theta, Xall, yall, cw, l2)
            res.loss_history.append((r, L))
            if (central_loss is not None and res.rounds_to_converge is None
                    and L - central_loss <= tol * max(abs(central_loss), 1e-12)):
                res.rounds_to_converge = r
    res.theta = theta
    res.train_seconds = time.process_time() - t0
    # 8 bytes/float, theta down + theta up, per site, per round
    res.bytes_exchanged = int(rounds * len(sites) * 2 * d * 8)
    if dp_sigma is not None:
        # same q at every site => same epsilon at every site (so also the worst case)
        res.epsilon = float(P.epsilon(q, dp_sigma, rounds * local_steps, delta))
    return res
