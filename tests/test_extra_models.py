import numpy as np
from pvm import models as ML


def test_sigmoid_is_stable_and_bounded():
    z = np.array([-1000.0, 0.0, 1000.0])
    s = ML.sigmoid(z)
    assert s[0] == 0.0 and s[1] == 0.5 and s[2] == 1.0


def test_objective_decreases_along_lbfgs_solution():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(500, 3)); y = (X[:, 0] > 0).astype(float)
    cw = ML.class_weights(int(y.sum()), 500); Xa = ML.aug(X)
    th = ML.fit_central(Xa, y, cw)
    assert ML.objective(th, Xa, y, cw) < ML.objective(np.zeros(4), Xa, y, cw)
