import numpy as np

from pvm import models as ML


def _toy(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 3))
    logit = 1.5 * X[:, 0] - 1.0 * X[:, 1] - 3.0
    y = (rng.random(n) < ML.sigmoid(logit)).astype(float)
    return X, y


def test_class_weights_balance_classes():
    wn, wp = ML.class_weights(pos=100, n=1000)
    assert abs(wn * 900 - wp * 100) < 1e-9


def test_fit_central_recovers_signs_and_gradient_is_small():
    X, y = _toy()
    cw = ML.class_weights(int(y.sum()), len(y))
    Xa = ML.aug(X)
    th = ML.fit_central(Xa, y, cw)
    assert th[0] > 0 > th[1]
    g = ML.record_grads(th, Xa, y, cw).sum(0) / len(y)
    g[:-1] += ML.L2 * th[:-1]
    assert np.linalg.norm(g) < 1e-4


def test_standardiser_from_aggregates_matches_pooled():
    X, _ = _toy(1000)
    parts = [ML.moments(X[:300]), ML.moments(X[300:700]), ML.moments(X[700:])]
    mean, sd = ML.standardiser(parts)
    assert np.allclose(mean, X.mean(0)) and np.allclose(sd, X.std(0))


def test_model_json_round_trip_and_scalar_score_equal():
    X, y = _toy(500)
    cw = ML.class_weights(int(y.sum()), len(y))
    th = ML.fit_central(ML.aug(X), y, cw)
    m = ML.Model(th, X.mean(0), X.std(0), tau=0.3, m=3)
    m2 = ML.Model.from_json(m.to_json())
    assert np.array_equal(m.score(X), m2.score(X))
    assert m.score_one(list(X[7])) == m.score(X[7:8])[0]
