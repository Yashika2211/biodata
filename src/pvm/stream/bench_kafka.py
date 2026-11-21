"""End-to-end Kafka -> Spark -> Kafka latency at several event rates and triggers.

Requires ``docker compose up`` (+ topics) and the Spark venv.  Spark runs with
``--emit-all`` (one alert per event) so every event yields a latency sample.
Writes ``results/bench_kafka.json``.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time

from . import consumer as CONS
from . import producer as PROD


def _cpu_snapshot(proc):
    """{pid: cpu_seconds} for the Spark launcher and every descendant (JVM, Python workers)."""
    import psutil
    snap = {}
    try:
        p = psutil.Process(proc.pid)
        for q in [p] + p.children(recursive=True):
            try:
                t = q.cpu_times()
                snap[q.pid] = t.user + t.system
            except psutil.Error:
                pass
    except psutil.Error:
        pass
    return snap


def _cpu_delta(before, after):
    """CPU used between snapshots: pids present in both count their delta, new pids their total."""
    return sum(v - before.get(pid, 0.0) for pid, v in after.items())


def start_spark(trigger, cores, ckpt, log_path, model="models/model.json"):
    shutil.rmtree(ckpt, ignore_errors=True)
    env = dict(os.environ, PYSPARK_PYTHON=sys.executable)
    cmd = [sys.executable, "-m", "pvm.stream.spark_job", "--emit-all", "--trigger", trigger,
           "--cores", str(cores), "--checkpoint", ckpt, "--model", model]
    log = open(log_path, "w")
    proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
    for _ in range(180):
        time.sleep(1)
        if "STREAM STARTED" in open(log_path).read():
            break
    time.sleep(12)
    return proc


def run_one(patients, rate, events, since_pad=0.0):
    holder = {}
    since = int(time.time() * 1000)
    th = threading.Thread(target=lambda: holder.update(
        CONS.consume(expect=events, idle_timeout=25, since_ms=since, max_seconds=240)))
    th.start()
    time.sleep(3)
    prod = PROD.run(patients, "127.0.0.1:9092", rate, events)
    th.join()
    return prod, holder


def main():
    from ..experiments import Provider
    ap = argparse.ArgumentParser()
    ap.add_argument("--triggers", nargs="+", default=["500 milliseconds", "1 second", "5 seconds"])
    ap.add_argument("--rates", nargs="+", type=float, default=[50, 500, 2000])
    ap.add_argument("--seconds", type=float, default=30.0, help="duration of each paced run")
    ap.add_argument("--max-events", type=int, default=40000)
    ap.add_argument("--cores", type=int, default=2)
    ap.add_argument("--out", default="results/bench_kafka.json")
    a = ap.parse_args()
    ps = Provider("synthetic", n_patients=120).cohort(7)
    results = []
    for trig in a.triggers:
        proc = start_spark(trig, a.cores, "/tmp/pvm-bench-ck", "/tmp/pvm-bench-spark.log")
        PROD.run(ps, "127.0.0.1:9092", 100, 300)          # warm-up (not recorded)
        time.sleep(10)
        for rate in list(a.rates) + [0]:
            events = a.max_events if rate == 0 else int(rate * a.seconds)
            cpu0 = _cpu_snapshot(proc)
            prod, cons = run_one(ps, rate, events)
            cpu = _cpu_delta(cpu0, _cpu_snapshot(proc))
            row = dict(trigger=trig, target_rate=rate, cores=a.cores, events=events,
                       producer_rate=prod["rate"], avg_event_bytes=prod["avg_bytes"],
                       received=cons.get("n", 0), latency_ms={k: cons.get(k) for k in
                                                              ("p50", "p95", "p99", "mean", "max")},
                       throughput_eps=cons.get("throughput_eps"),
                       privacy_violations=cons.get("privacy_violations"),
                       spark_cpu_seconds=cpu,
                       # CPU per event is only meaningful when saturated (idle JVM time dominates otherwise)
                       cpu_seconds_per_million_events=(cpu / max(cons.get("n", 1), 1) * 1e6 if rate == 0 else None))
            print(json.dumps(row), flush=True)
            results.append(row)
            time.sleep(8)
        proc.terminate()
        try:
            proc.wait(20)
        except subprocess.TimeoutExpired:
            proc.kill()
        time.sleep(3)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(dict(runs=results, spark="PySpark 3.5.3 local[%d], Kafka apache/kafka 3.8.0 (Docker, 1 broker per cluster)" % a.cores),
              open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
