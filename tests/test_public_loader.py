import gzip

import numpy as np
import pandas as pd

from pvm.data import public as PB


def _write(tmp_path, n_stays=3, T=700):
    rows = []
    rng = np.random.default_rng(0)
    for s in range(n_stays):
        for k in range(T):
            rows.append(dict(vitalperiodicid=len(rows), patientunitstayid=100 + s,
                             observationoffset=5 * k + (1 if k % 7 == 0 else 0),
                             temperature=np.nan, sao2=95 + rng.integers(-2, 3),
                             heartrate=80 + rng.integers(-5, 6), respiration=16,
                             systemicsystolic=np.nan if k % 2 else 120.0))
    df = pd.DataFrame(rows)
    with gzip.open(tmp_path / "vitalPeriodic.csv.gz", "wt") as f:
        df.to_csv(f, index=False)
    pt = pd.DataFrame(dict(patientunitstayid=[100 + s for s in range(n_stays)],
                           hospitalid=[1, 1, 2, 2, 3, 3, 4, 4][:n_stays]))
    with gzip.open(tmp_path / "patient.csv.gz", "wt") as f:
        pt.to_csv(f, index=False)


def test_loader_regrids_and_cleans(tmp_path):
    _write(tmp_path)
    series = PB.load_series(str(tmp_path))
    assert len(series) == 3
    sid, hid, X = series[0]
    assert X.shape == (700, 5)
    assert np.isnan(X[:, 4]).all()                 # temperature absent -> NaN
    assert 0.4 < np.isnan(X[:, 3]).mean() < 0.6    # SBP on every other bin


def test_loader_missing_file_message(tmp_path):
    try:
        PB.load_series(str(tmp_path))
    except FileNotFoundError as e:
        assert "data/README.md" in str(e)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_cohort_has_sites_and_valid_split(tmp_path):
    _write(tmp_path, n_stays=8)
    ps = PB.make_cohort(PB.load_series(str(tmp_path)), n_sites=2, seed=1, frac=1.0)
    assert {p.site for p in ps} == {"site0", "site1"}
    for p in ps:
        for s, e, _ in p.episodes:
            assert e <= p.split or s >= p.split
