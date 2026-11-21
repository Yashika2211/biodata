import math

from pvm import privacy as P


def test_zero_noise_is_infinite_epsilon_and_zero_sampling_is_free():
    assert P.epsilon(0.05, 0.0, 100) == math.inf
    assert P.rdp_subsampled_gaussian(0.0, 1.0, 8) == 0.0


def test_epsilon_is_nonnegative_and_finite_for_reasonable_settings():
    for s in (0.5, 2, 8, 32, 128):
        e = P.epsilon(0.02, s, 450)
        assert 0.0 <= e < 1e4
