import numpy as np

from pvm.data import public as PB


def test_assign_sites_balances_patient_counts():
    hosp = np.repeat([1, 2, 3, 4, 5, 6], [40, 30, 25, 20, 15, 10])
    m = PB.assign_sites(hosp, 3)
    loads = {}
    for h, k in m.items():
        loads[k] = loads.get(k, 0) + int((hosp == h).sum())
    assert max(loads.values()) - min(loads.values()) <= 15
    assert set(m) == set(hosp)
