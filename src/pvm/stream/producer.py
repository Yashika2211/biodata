"""Replay a cohort's test region into ``vitals.raw.<site>`` topics as JSON.

Every message carries ``producer_ts_ms`` (wall clock at send time) so the
alert consumer can compute true end-to-end latency.  ``ts`` is the simulated
event time (sample index * sampling interval).
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

from .. import config as C
from ..serving import event_json


def build_events(patients, n_events=None, region="test"):
    """Round-robin interleave patients in time order: yields (pid, site, seq, x)."""
    iters = []
    for p in patients:
        lo = p.split if region == "test" else 0
        iters.append(((p.pid, p.site, k, p.X[k]) for k in range(lo, p.T)))
    out = (e for group in itertools.zip_longest(*iters) for e in group if e is not None)
    return itertools.islice(out, n_events) if n_events else out


def run(patients, bootstrap, rate, n_events, warm_seqs=0, topic_prefix="vitals.raw"):
    from kafka import KafkaProducer
    prod = KafkaProducer(bootstrap_servers=bootstrap, linger_ms=5, batch_size=65536,
                         key_serializer=lambda k: k.encode(),
                         value_serializer=lambda v: v.encode(), acks=1)
    t0 = time.time()
    sent = 0
    nbytes = 0
    for pid, site, seq, x in build_events(patients, n_events):
        if rate:
            target = t0 + sent / rate
            lag = target - time.time()
            if lag > 0:
                time.sleep(lag)
        now = int(time.time() * 1000)
        msg = event_json(pid, site, seq, seq * int(C.DT_MIN * 60_000), now, x)
        prod.send(f"{topic_prefix}.{site}", key=pid, value=msg)
        nbytes += len(msg)
        sent += 1
    prod.flush()
    dur = time.time() - t0
    return dict(sent=sent, seconds=dur, rate=sent / dur, bytes=nbytes,
                avg_bytes=nbytes / max(sent, 1), t_start_ms=int(t0 * 1000))


def main():
    from ..experiments import Provider
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="synthetic", choices=["synthetic", "eicu"])
    ap.add_argument("--bootstrap", default="127.0.0.1:9092")
    ap.add_argument("--rate", type=float, default=200.0, help="events/s (0 = as fast as possible)")
    ap.add_argument("--events", type=int, default=20000)
    ap.add_argument("--patients", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    prov = Provider(a.dataset, n_patients=a.patients)
    ps = prov.cohort(a.seed)[:a.patients]
    print(json.dumps(run(ps, a.bootstrap, a.rate, a.events)))


if __name__ == "__main__":
    main()
