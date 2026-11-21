"""FedAvg rounds carried over Kafka topics (communication is real, compute is one machine).

Sites publish their locally updated weights to ``fl.updates`` on **kafka-central**; the
server averages them (weighted by record count) and publishes the new global weights to
``fl.global``.  Raw rows never touch Kafka -- only model parameters do.

The result is bit-for-bit the in-process ``pvm.federated.fedavg`` (JSON floats round-trip
exactly and the server sums in site order), see ``tests/test_fl_kafka.py``.
"""
from __future__ import annotations

import json
import threading
import time
import uuid

import numpy as np

from .. import federated as FED
from .. import models as ML


def _producer(bootstrap):
    from kafka import KafkaProducer
    return KafkaProducer(bootstrap_servers=bootstrap, linger_ms=0,
                         value_serializer=lambda v: json.dumps(v).encode())


def _consumer(bootstrap, topic, timeout_s):
    from kafka import KafkaConsumer
    return KafkaConsumer(topic, bootstrap_servers=bootstrap, auto_offset_reset="earliest",
                         enable_auto_commit=False, group_id=f"fl-{uuid.uuid4().hex[:8]}",
                         value_deserializer=lambda b: json.loads(b.decode()),
                         consumer_timeout_ms=int(timeout_s * 1000))


def run_server(bootstrap, topics, n_sites, rounds, d, weights, stats, timeout_s=60):
    prod = _producer(bootstrap)
    cons = _consumer(bootstrap, topics["up"], timeout_s)
    theta = np.zeros(d)
    pending = {}
    for r in range(1, rounds + 1):
        msg = {"round": r, "theta": theta.tolist()}
        prod.send(topics["down"], msg); prod.flush()
        stats["bytes_down"] += len(json.dumps(msg)) * n_sites       # each site reads it
        got = {}
        t0 = time.time()
        while len(got) < n_sites:
            for m in cons:
                v = m.value
                pending.setdefault(v["round"], {})[v["site"]] = v["theta"]
                stats["bytes_up"] += len(json.dumps(v))
                if len(pending.get(r, {})) == n_sites:
                    break
            got = pending.get(r, {})
            if time.time() - t0 > timeout_s:
                raise TimeoutError(f"round {r}: only {len(got)}/{n_sites} updates")
        new = np.zeros(d)
        for s in range(n_sites):                                    # fixed order => deterministic
            new += weights[s] * np.array(got[s])
        theta = new
    prod.send(topics["down"], {"round": rounds + 1, "theta": theta.tolist(), "done": True}); prod.flush()
    stats["theta"] = theta


def run_site(bootstrap, topics, site_id, data, cw, rounds, local_steps, lr, l2, timeout_s=60):
    Xa, y = data
    prod = _producer(bootstrap)
    cons = _consumer(bootstrap, topics["down"], timeout_s)
    r_done = 0
    for m in cons:
        v = m.value
        if v.get("done") or v["round"] <= r_done:
            if v.get("done"):
                break
            continue
        theta = np.array(v["theta"])
        loc = FED._local_full_batch(theta, Xa, y, cw, local_steps, lr, l2)
        prod.send(topics["up"], {"round": v["round"], "site": site_id, "theta": loc.tolist()})
        prod.flush()
        r_done = v["round"]
        if r_done >= rounds:
            break


def fedavg_over_kafka(sites, cw, rounds=20, local_steps=3, lr=0.3, l2=ML.L2,
                      bootstrap="127.0.0.1:9093"):
    """Run FedAvg with every parameter exchange going through Kafka topics."""
    run = uuid.uuid4().hex[:8]
    topics = {"up": f"fl.updates.{run}", "down": f"fl.global.{run}"}
    d = sites[0][0].shape[1]
    ns = np.array([len(y) for _, y in sites], dtype=float)
    weights = ns / ns.sum()
    stats = {"bytes_up": 0, "bytes_down": 0}
    threads = [threading.Thread(target=run_site, args=(bootstrap, topics, i, sites[i], cw, rounds,
                                                       local_steps, lr, l2)) for i in range(len(sites))]
    srv = threading.Thread(target=run_server, args=(bootstrap, topics, len(sites), rounds, d, weights, stats))
    t0 = time.time()
    for t in threads:
        t.start()
    time.sleep(1.0)
    srv.start()
    srv.join()
    for t in threads:
        t.join(timeout=30)
    stats["seconds"] = time.time() - t0
    return stats
