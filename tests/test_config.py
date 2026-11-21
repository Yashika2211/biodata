from pvm import config as C


def test_priors_and_thresholds_are_consistent():
    for v in C.VITALS:
        lo, hi = C.VALID_RANGE[v]
        assert lo < C.PRIOR_MEAN[v] < hi and C.PRIOR_SD[v] > 0 and C.MIN_SCALE[v] > 0
        wl, wh = C.WARD_THRESHOLDS[v]
        assert (wl is None or wl > lo) and (wh is None or wh < hi)


def test_feature_names_match_count():
    assert len(C.FEATURE_NAMES) == C.NF == 3 * C.NV
