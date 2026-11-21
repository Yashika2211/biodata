import numpy as np

from pvm import metrics as M


def test_runs_min_length():
    f = np.array([1, 1, 0, 1, 1, 1, 0, 1], dtype=bool)
    assert M.runs(f, 3) == [(3, 6)]
    assert M.runs(f, 2) == [(0, 2), (3, 6)]


def test_counts_tp_fa_and_delay():
    # dt=5 min, episode [20,40); alarm at 24..30 (fires at 26), false alarm at 60..64
    s = np.zeros(100)
    s[24:30] = 1; s[60:64] = 1
    c, d = M.patient_counts(s, [(20, 40, "x")], 0, 100, 5.0, 0.5, 3, tol_min=30)
    assert (c["alarms"], c["tp_alarms"], c["episodes"], c["detected"]) == (2, 1, 1, 1)
    assert d == [(26 - 20) * 5.0]
    assert abs(c["days"] - 100 * 5 / 1440) < 1e-12


def test_tolerance_padding_and_early_alarm_has_zero_delay():
    s = np.zeros(100); s[16:20] = 1       # ends 20 = ep start, tol 30 min = 6 samples
    c, d = M.patient_counts(s, [(22, 40, "x")], 0, 100, 5.0, 0.5, 3, tol_min=30)
    assert c["tp_alarms"] == 1 and d == [0.0]


def test_nan_scores_never_alarm():
    s = np.full(50, np.nan)
    c, _ = M.patient_counts(s, [], 0, 50, 5.0, 0.0, 1)
    assert c["alarms"] == 0


def test_summarise_and_sample_metrics():
    out = M.summarise(dict(alarms=4, tp_alarms=3, episodes=6, detected=3, days=2.0), [10, 20, 30])
    assert out["precision"] == 0.75 and out["recall"] == 0.5
    assert out["fa_per_day"] == 0.5 and out["delay_min"] == 20.0


def test_always_on_alarm_refires_and_is_not_a_single_event():
    """An alarm that never clears must keep counting (1 per hour = 12 samples)."""
    s = np.ones(288)                                   # one day at 5 min
    c, _ = M.patient_counts(s, [], 0, 288, 5.0, 0.5, 3)
    assert c["alarms"] == 24                           # ~24 false alarms / day


def test_always_on_alarm_cannot_game_recall_or_precision():
    s = np.ones(288)
    c, d = M.patient_counts(s, [(100, 120, "x")], 0, 288, 5.0, 0.5, 3)
    assert c["detected"] == 1 and c["alarms"] > 10      # many false alarms too
    assert c["tp_alarms"] == 1
