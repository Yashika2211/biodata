import numpy as np

from pvm import config as C
from pvm.data import synthetic as SY


def test_phenotype_baselines_are_distinct():
    rng = np.random.default_rng(0)
    copd = SY.make_patient("a", "s", "copd", 3.0, rng)
    athl = SY.make_patient("b", "s", "athlete", 3.0, rng)
    assert np.nanmedian(copd.X[:, 1]) < 93 < np.nanmedian(athl.X[:, 1])
    assert np.nanmedian(athl.X[:, 0]) < np.nanmedian(copd.X[:, 0])
