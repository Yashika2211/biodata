from pvm import privacy as P


def test_more_steps_never_reduce_rdp():
    a = P.compute_rdp(0.02, 4.0, 10); b = P.compute_rdp(0.02, 4.0, 100)
    assert (b >= a).all()
