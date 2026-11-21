import numpy as np

from pvm import features as F
from pvm import models as ML
from pvm import serving as S


def test_patients_do_not_share_state():
    model = ML.Model(np.zeros(16), np.zeros(15), np.ones(15), tau=99.0, m=3)
    r = S.LocalRunner(model)
    a = [dict(pid="a", site="s", seq=k, ts=k, hr=60, spo2=88, rr=20, sbp=130, temp=37.0) for k in range(200)]
    b = [dict(pid="b", site="s", seq=k, ts=k, hr=100, spo2=99, rr=12, sbp=100, temp=36.5) for k in range(5)]
    r.process_batch(a + b)
    sa, sb = F.state_from_json(r.states["a"]), F.state_from_json(r.states["b"])
    assert abs(sa["mu"][1] - 88) < 2 and abs(sb["mu"][1] - 99) > 0   # a adapted to 88; b still near prior
    assert sa["t"] == 200 and sb["t"] == 5


def test_out_of_order_events_in_a_batch_are_sorted():
    model = ML.Model(np.zeros(16), np.zeros(15), np.ones(15), tau=99.0, m=3)
    ev = [dict(pid="a", site="s", seq=k, ts=k, hr=70 + k, spo2=97, rr=16, sbp=120, temp=36.8) for k in range(10)]
    r1, r2 = S.LocalRunner(model), S.LocalRunner(model)
    r1.process_batch(ev); r2.process_batch(list(reversed(ev)))
    assert r1.states["a"] == r2.states["a"]
