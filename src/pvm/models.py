"""Class-weighted L2 logistic regression with federation-friendly pieces.

Everything is expressed through *sums* over records (gradient, loss, moments)
so each site can compute its part locally and share only aggregates.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np

from . import config as C

L2 = 1e-3


def sigmoid(z):
    return 0.5 * (1.0 + np.tanh(0.5 * z))


def moments(X: np.ndarray):
    """Aggregate statistics a site shares to build the standardiser."""
    return dict(n=len(X), s=X.sum(0), ss=(X ** 2).sum(0))


def standardiser(mom_list):
    n = sum(m["n"] for m in mom_list)
    s = sum(m["s"] for m in mom_list)
    ss = sum(m["ss"] for m in mom_list)
    mean = s / n
    sd = np.sqrt(np.maximum(ss / n - mean ** 2, 1e-12))
    return mean, np.maximum(sd, 1e-6)


def class_weights(pos: int, n: int):
    """Balanced weights from aggregate counts only."""
    pos = max(pos, 1)
    return n / (2.0 * (n - pos)), n / (2.0 * pos)     # (w_neg, w_pos)


def aug(X):
    return np.hstack([X, np.ones((len(X), 1))])


def record_grads(theta, Xa, y, cw):
    """Per-record gradients of the weighted log loss (N, d+1)."""
    p = sigmoid(Xa @ theta)
    wt = np.where(y == 1, cw[1], cw[0])
    return (wt * (p - y))[:, None] * Xa


def loss_sum(theta, Xa, y, cw):
    z = Xa @ theta
    wt = np.where(y == 1, cw[1], cw[0])
    # stable log(1+exp(z)) - y z
    return float(np.sum(wt * (np.logaddexp(0, z) - y * z)))


def objective(theta, Xa, y, cw, l2=L2):
    n = len(y)
    return loss_sum(theta, Xa, y, cw) / n + 0.5 * l2 * float(theta[:-1] @ theta[:-1])


def fit_central(Xa, y, cw, l2=L2):
    from scipy.optimize import minimize        # lazy: serving needs no scipy
    d = Xa.shape[1]
    n = len(y)

    def f(th):
        g = record_grads(th, Xa, y, cw).sum(0) / n
        g[:-1] += l2 * th[:-1]
        return objective(th, Xa, y, cw, l2), g

    res = minimize(f, np.zeros(d), jac=True, method="L-BFGS-B",
                   options=dict(maxiter=500, gtol=1e-9))
    return res.x


@dataclass
class Model:
    theta: np.ndarray                  # (d+1,) in standardised feature space
    mean: np.ndarray
    sd: np.ndarray
    tau: float = 0.0                   # logit threshold
    m: int = C.PERSISTENCE_M
    mode: str = "adaptive"
    alpha: float = C.ALPHA
    tag: str = C.MODEL_TAG
    meta: dict = field(default_factory=dict)

    def score(self, X):
        """Logit score for raw (unstandardised) features, shape (N, 15)."""
        # Sequential accumulation in feature order => bit-identical to
        # ``score_one`` (BLAS matmul would change the summation order).
        X = np.asarray(X, dtype=float)
        z = np.full(len(X), float(self.theta[-1]))
        for j in range(X.shape[1]):
            z = z + ((X[:, j] - self.mean[j]) / self.sd[j]) * self.theta[j]
        return z

    def score_one(self, f):
        """Pure-python score of one feature vector (used by serving)."""
        z = self.theta[-1]
        for j in range(len(f)):
            z += ((f[j] - self.mean[j]) / self.sd[j]) * self.theta[j]
        return float(z)

    def to_json(self):
        return json.dumps(dict(theta=self.theta.tolist(), mean=self.mean.tolist(),
                               sd=self.sd.tolist(), tau=self.tau, m=self.m,
                               mode=self.mode, alpha=self.alpha, tag=self.tag))

    @classmethod
    def from_json(cls, s):
        d = json.loads(s)
        return cls(theta=np.array(d["theta"]), mean=np.array(d["mean"]),
                   sd=np.array(d["sd"]), tau=d["tau"], m=d["m"], mode=d["mode"],
                   alpha=d["alpha"], tag=d["tag"])
