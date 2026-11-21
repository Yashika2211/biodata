import numpy as np

from pvm import federated as FED
from pvm import models as ML


def test_fedavg_weights_sites_by_record_count():
    rng = np.random.default_rng(0)
    def site(n, shift):
        X = rng.normal(size=(n, 2)) + shift
        y = (rng.random(n) < 0.3).astype(float)
        return ML.aug(X), y
    big, small = site(3000, 0.0), site(300, 3.0)
    cw = (1.0, 1.0)
    r = FED.fedavg([big, small], cw, rounds=1, local_steps=1, lr=0.5)
    t_big = FED._local_full_batch(np.zeros(3), *big, cw, 1, 0.5, ML.L2)
    t_small = FED._local_full_batch(np.zeros(3), *small, cw, 1, 0.5, ML.L2)
    expect = (3000 * t_big + 300 * t_small) / 3300
    assert np.allclose(r.theta, expect)
