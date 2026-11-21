"""Alert consumer on kafka-central: end-to-end latency percentiles.

Latency = consumer receive time - producer timestamp stamped in the raw event.
Also asserts the privacy contract: no alert contains a vital value or raw id.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

ALLOWED = {"pid_hash", "site", "ts", "score", "model", "producer_ts_ms"}
VITAL_KEYS = {"hr", "spo2", "rr", "sbp", "temp", "pid"}


def percentiles(lat_ms):
    a = np.asarray(lat_ms, dtype=float)
    if len(a) == 0:
        return {}
    return dict(n=int(len(a)), p50=float(np.percentile(a, 50)), p95=float(np.percentile(a, 95)),
                p99=float(np.percentile(a, 99)), mean=float(a.mean()), max=float(a.max()))


def consume(bootstrap="127.0.0.1:9093", topic="alerts.central", expect=None,
            idle_timeout=15.0, since_ms=0, max_seconds=300.0):
    from kafka import KafkaConsumer
    c = KafkaConsumer(topic, bootstrap_servers=bootstrap, auto_offset_reset="latest",
                      enable_auto_commit=False, group_id=f"lat-{int(time.time()*1000)}",
                      value_deserializer=lambda b: json.loads(b.decode()),
                      fetch_max_wait_ms=20)
    lat, violations, first_t, last_t = [], 0, None, None
    t_start = last_msg = time.time()
    while True:
        recs = c.poll(timeout_ms=200)
        now_ms = time.time() * 1000
        for batch in recs.values():
            for r in batch:
                v = r.value
                if v.get("producer_ts_ms", 0) < since_ms:
                    continue
                if not set(v) <= ALLOWED or (set(v) & VITAL_KEYS):
                    violations += 1
                lat.append(now_ms - v["producer_ts_ms"])
                last_msg = time.time(); last_t = last_msg
                first_t = first_t or last_msg
        if expect and len(lat) >= expect:
            break
        if time.time() - last_msg > idle_timeout or time.time() - t_start > max_seconds:
            break
    c.close()
    out = percentiles(lat)
    out["privacy_violations"] = violations
    if first_t and last_t and last_t > first_t:
        out["throughput_eps"] = len(lat) / (last_t - first_t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", default="127.0.0.1:9093")
    ap.add_argument("--expect", type=int, default=None)
    ap.add_argument("--idle", type=float, default=15.0)
    a = ap.parse_args()
    print(json.dumps(consume(a.bootstrap, expect=a.expect, idle_timeout=a.idle)))


if __name__ == "__main__":
    main()
