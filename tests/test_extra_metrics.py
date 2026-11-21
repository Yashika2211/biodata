import numpy as np
from pvm import metrics as M


def test_add_counts_is_additive():
    a = dict(alarms=1, tp_alarms=1, episodes=2, detected=1, days=1.0)
    assert M.add_counts(a, a)['episodes'] == 4


def test_precision_nan_without_alarms_and_f1_zero():
    out = M.summarise(dict(alarms=0, tp_alarms=0, episodes=3, detected=0, days=1.0), [])
    assert out['f1'] == 0.0 and np.isnan(out['precision'])


def test_runs_empty_and_all_true():
    assert M.runs(np.zeros(5, dtype=bool), 1) == []
    assert M.runs(np.ones(5, dtype=bool), 3) == [(0, 5)]
