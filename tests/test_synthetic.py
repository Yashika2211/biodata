import numpy as np

from pvm import config as C
from pvm.data import synthetic as SY


def test_phenotype_baselines_are_distinct():
    rng = np.random.default_rng(0)
    copd = SY.make_patient("a", "s", "copd", 3.0, rng)
    athl = SY.make_patient("b", "s", "athlete", 3.0, rng)
    assert np.nanmedian(copd.X[:, 1]) < 93 < np.nanmedian(athl.X[:, 1])
    assert np.nanmedian(athl.X[:, 0]) < np.nanmedian(copd.X[:, 0])


def test_missing_values_present_but_not_dominant():
    p = SY.make_patient("a", "s", "normal", 4.0, np.random.default_rng(1))
    frac = np.isnan(p.X).mean()
    assert 0.005 < frac < 0.25


def test_artefact_runs_have_realistic_lengths():
    rng = np.random.default_rng(2)
    lens = []
    for _ in range(30):
        mask, _ = SY._artefacts(1152, rng, 5.0, rate_per_day=6.0)
        run = 0
        for v in np.r_[mask, False]:
            if v:
                run += 1
            elif run:
                lens.append(run); run = 0
    assert max(lens) <= 8 * 3            # overlapping artefacts can merge, but stay short
    assert np.mean(np.array(lens) >= 3) > 0.3   # many survive a 3-sample persistence filter


def test_sites_are_non_iid():
    ps = SY.make_cohort(80, 4, seed=7)
    from collections import Counter
    mixes = {}
    for p in ps:
        mixes.setdefault(p.site, Counter())[p.phenotype] += 1
    top = [m.most_common(1)[0][0] for m in mixes.values()]
    assert len(set(top)) >= 2            # sites are dominated by different phenotypes


def test_ar1_noise_is_autocorrelated():
    p = SY.make_patient("a", "s", "normal", 4.0, np.random.default_rng(3), episode_rate=0.0)
    x = p.X[:, 0]
    x = x[~np.isnan(x)]
    x = x - np.mean(x)
    lag1 = np.corrcoef(x[:-1], x[1:])[0, 1]
    assert lag1 > 0.5


def test_dt_minutes_is_parameterised():
    p = SY.make_patient("a", "s", "normal", 1.0, np.random.default_rng(4), dt_min=1.0)
    assert p.T == 1440 and abs(p.days - 1.0) < 1e-9
