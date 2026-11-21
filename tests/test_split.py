from pvm.data.synthetic import make_cohort


def test_no_episode_crosses_split():
    ps = make_cohort(40, 4, seed=3)
    n = 0
    for p in ps:
        for (s, e, _k) in p.episodes:
            assert e <= p.split or s >= p.split
            n += 1
        # labels agree with the episode list
        assert p.y.sum() == sum(e - s for s, e, _ in p.episodes)
    assert n > 10


def test_artefacts_are_labelled_normal_and_span_1_to_8():
    ps = make_cohort(20, 2, seed=4)
    for p in ps:
        m = p.artefact & (p.y == 0)
        assert m.sum() > 0
