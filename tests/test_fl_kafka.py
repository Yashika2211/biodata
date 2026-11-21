"""Integration test: FedAvg over Kafka == in-process FedAvg. Skipped if Kafka is not up."""
import socket

import numpy as np
import pytest

from pvm import federated as FED
from pvm import methods as MT
from pvm.data.synthetic import make_cohort


def _kafka_up(host="127.0.0.1", port=9093):
    try:
        socket.create_connection((host, port), timeout=1).close()
        return True
    except OSError:
        return False


@pytest.mark.skipif(not _kafka_up(), reason="kafka-central not running (make up)")
def test_fedavg_over_kafka_equals_in_process():
    pytest.importorskip("kafka")
    from pvm.stream.fl_kafka import fedavg_over_kafka
    ps = make_cohort(24, 3, seed=31, days=2.0)
    fa = MT.featurize(ps, "adaptive")
    sites, mean, sd, cw, std = MT.prepare_global(ps, fa)
    sl = list(std.values())
    stats = fedavg_over_kafka(sl, cw, rounds=8)
    ref = FED.fedavg(sl, cw, rounds=8)
    assert np.allclose(stats["theta"], ref.theta, atol=1e-12)
    assert stats["bytes_up"] > 0
