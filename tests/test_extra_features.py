import numpy as np
from pvm import features as F


def test_static_mode_z_matches_prior_formula():
    st = F.new_state('static')
    z = F.update_state(st, [100, 97, 16, 120, 36.8])[0]
    assert abs(z - (100 - 80.0) / 14.0) < 1e-12


def test_all_missing_row_keeps_time_counter_advancing():
    st = F.new_state('adaptive')
    F.update_state(st, [float('nan')] * 5)
    assert st['t'] == 1
