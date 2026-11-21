from pvm.data.synthetic import make_cohort


def test_cohort_is_reproducible_per_seed():
    a = make_cohort(6, 2, seed=9, days=2.0); b = make_cohort(6, 2, seed=9, days=2.0)
    import numpy as np
    assert all(np.array_equal(x.X, y.X, equal_nan=True) for x, y in zip(a, b))
