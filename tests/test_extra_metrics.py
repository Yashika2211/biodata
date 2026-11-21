import numpy as np
from pvm import metrics as M


def test_add_counts_is_additive():
    a = dict(alarms=1, tp_alarms=1, episodes=2, detected=1, days=1.0)
    assert M.add_counts(a, a)['episodes'] == 4
