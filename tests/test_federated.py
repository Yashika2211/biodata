import numpy as np

from pvm import federated as FED
from pvm import methods as MT
from pvm import models as ML
from pvm.data.synthetic import make_cohort


def _setup():
    ps = make_cohort(48, 4, seed=5, days=3.0)
    fa = MT.featurize(ps, "adaptive")
    sites, mean, sd, cw, std = MT.prepare_global(ps, fa)
    sl = list(std.values())
    Xa = np.vstack([s[0] for s in sl]); y = np.concatenate([s[1] for s in sl])
    th = ML.fit_central(Xa, y, cw)
    return sl, cw, ML.objective(th, Xa, y, cw), th


def test_fedavg_reaches_centralised_optimum():
    sl, cw, L0, th = _setup()
    r = FED.fedavg(sl, cw, rounds=300, central_loss=L0)
    gap = r.loss_history[-1][1] - L0
    assert gap < 1e-3 * abs(L0)
    assert r.rounds_to_converge is not None and r.rounds_to_converge <= 300
    assert np.linalg.norm(r.theta - th) < 0.15 * max(1.0, np.linalg.norm(th))


def test_dp_noise_hurts_and_epsilon_reported():
    sl, cw, L0, _ = _setup()
    lo = FED.fedavg(sl, cw, rounds=60, dp_sigma=2.0, seed=1, central_loss=L0)
    hi = FED.fedavg(sl, cw, rounds=60, dp_sigma=200.0, seed=1, central_loss=L0)
    assert np.isfinite(lo.epsilon) and hi.epsilon < lo.epsilon
    assert hi.loss_history[-1][1] > lo.loss_history[-1][1]


def test_non_private_has_infinite_epsilon():
    sl, cw, L0, _ = _setup()
    assert FED.fedavg(sl, cw, rounds=2).epsilon == float("inf")
