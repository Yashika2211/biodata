"""Spark Structured Streaming job: Kafka (site) -> per-patient state -> Kafka (central).

* Reads ``vitals.raw.*`` from the site cluster.
* ``applyInPandasWithState`` keeps the per-patient adaptive state, serialised as
  a JSON string (see ``pvm.features``), and scores events with the *same*
  ``pvm.serving.step`` used offline.
* Writes alerts to ``alerts.central`` on the central cluster.  Alerts carry only
  a salted-hash patient id, site, timestamp, score and model tag (never vitals).
  ``--emit-all`` emits one record per event (used to measure latency).
"""
from __future__ import annotations

import argparse
import os

from .. import config as C
from .. import features as F
from .. import models as ML
from .. import serving as S

OUT_DDL = ("pid_hash string, site string, ts long, score double, model string, "
           "producer_ts_ms long")
STATE_DDL = "json string"
IN_DDL = ("pid string, site string, seq long, ts long, producer_ts_ms long, "
          "hr double, spo2 double, rr double, sbp double, temp double")


def make_update_fn(model_json: str, salt: str, emit_all: bool):
    import pandas as pd

    def update(key, pdf_iter, state):
        model = ML.Model.from_json(model_json)           # cheap; per group per batch
        pid = key[0]
        st = F.state_from_json(state.get[0]) if state.exists else S.init_state(model)
        rows = []
        frames = [p for p in pdf_iter]
        if frames:
            pdf = pd.concat(frames).sort_values("seq")
            for e in pdf.itertuples(index=False):
                x = [getattr(e, v) for v in C.VITALS]
                score, fired = S.step(model, st, x)
                if fired or emit_all:
                    a = S.make_alert(model, pid, e.site, e.ts, score, salt, e.producer_ts_ms)
                    rows.append(a)
            state.update((F.state_to_json(st),))
        yield pd.DataFrame(rows, columns=["pid_hash", "site", "ts", "score", "model",
                                          "producer_ts_ms"])
    return update


def build(spark, a):
    from pyspark.sql import functions as fn
    from pyspark.sql.streaming.state import GroupStateTimeout

    model_json = open(a.model).read()
    salt = os.environ.get("PVM_SALT", "change-me-salt")
    raw = (spark.readStream.format("kafka")
           .option("kafka.bootstrap.servers", a.site_bootstrap)
           .option("subscribePattern", r"vitals\.raw\..*")
           .option("startingOffsets", a.starting_offsets)
           .option("maxOffsetsPerTrigger", a.max_offsets)
           .option("failOnDataLoss", "false").load())
    ev = (raw.select(fn.from_json(fn.col("value").cast("string"), IN_DDL).alias("e"))
          .select("e.*").where(fn.col("pid").isNotNull()))
    alerts = ev.groupBy("pid").applyInPandasWithState(
        make_update_fn(model_json, salt, a.emit_all), OUT_DDL, STATE_DDL,
        "append", GroupStateTimeout.NoTimeout)
    sink = alerts.select(fn.col("pid_hash").alias("key"),
                         fn.to_json(fn.struct(*alerts.columns)).alias("value"))
    w = (sink.writeStream.format("kafka")
         .option("kafka.bootstrap.servers", a.central_bootstrap)
         .option("topic", a.alerts_topic)
         .option("checkpointLocation", a.checkpoint))
    q = w.trigger(availableNow=True) if a.trigger == "once" else w.trigger(processingTime=a.trigger)
    return q.start()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/model.json")
    ap.add_argument("--site-bootstrap", default="127.0.0.1:9092")
    ap.add_argument("--central-bootstrap", default="127.0.0.1:9093")
    ap.add_argument("--alerts-topic", default="alerts.central")
    ap.add_argument("--checkpoint", default="/tmp/pvm-checkpoint")
    ap.add_argument("--trigger", default="1 second", help="micro-batch interval or 'once'")
    ap.add_argument("--max-offsets", type=int, default=200000)
    ap.add_argument("--starting-offsets", default="latest")
    ap.add_argument("--emit-all", action="store_true")
    ap.add_argument("--progress", action="store_true", help="print per-batch progress lines")
    ap.add_argument("--cores", default="2")
    ap.add_argument("--shuffle-partitions", default="4")
    a = ap.parse_args()
    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.appName("pvm-stream").master(f"local[{a.cores}]")
             .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3")
             .config("spark.sql.shuffle.partitions", a.shuffle_partitions)
             .config("spark.ui.enabled", "false")
             .config("spark.sql.streaming.stateStore.providerClass",
                     "org.apache.spark.sql.execution.streaming.state.HDFSBackedStateStoreProvider")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    q = build(spark, a)
    print("STREAM STARTED", flush=True)
    if a.progress:
        import time
        last = -1
        while q.isActive:
            pr = q.lastProgress
            if pr and pr["batchId"] != last:
                last = pr["batchId"]
                print("PROGRESS batch=%d rows=%d trigger_ms=%s" % (
                    last, pr["numInputRows"], pr.get("durationMs", {}).get("triggerExecution")), flush=True)
            time.sleep(0.3)
    q.awaitTermination()


if __name__ == "__main__":
    main()
