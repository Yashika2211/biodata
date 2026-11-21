import math

from pvm import privacy as P


def test_epsilon_decreases_with_noise():
    e = [P.epsilon(0.05, s, 500) for s in (0.6, 1.0, 2.0, 4.0, 8.0)]
    assert all(a > b for a, b in zip(e, e[1:]))


def test_epsilon_increases_with_steps_and_sampling_rate():
    assert P.epsilon(0.05, 1.0, 100) < P.epsilon(0.05, 1.0, 1000)
    assert P.epsilon(0.01, 1.0, 500) < P.epsilon(0.1, 1.0, 500)


def test_epsilon_decreases_with_larger_delta():
    assert P.epsilon(0.05, 1.0, 500, 1e-3) < P.epsilon(0.05, 1.0, 500, 1e-6)


def test_full_batch_matches_closed_form_rdp():
    # q=1: Gaussian mechanism, RDP = alpha / (2 sigma^2)
    assert math.isclose(P.rdp_subsampled_gaussian(1.0, 2.0, 8), 8 / 8.0)
    # subsampling can only help
    assert P.rdp_subsampled_gaussian(0.1, 2.0, 8) < P.rdp_subsampled_gaussian(1.0, 2.0, 8)


def test_known_regime_is_sane():
    # Abadi et al.-style setting (q=0.01, sigma=4, many steps) gives small eps
    e = P.epsilon(0.01, 4.0, 10000, 1e-5)
    assert 0.1 < e < 3.0
