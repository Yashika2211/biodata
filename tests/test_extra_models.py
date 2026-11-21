import numpy as np
from pvm import models as ML


def test_sigmoid_is_stable_and_bounded():
    z = np.array([-1000.0, 0.0, 1000.0])
    s = ML.sigmoid(z)
    assert s[0] == 0.0 and s[1] == 0.5 and s[2] == 1.0
