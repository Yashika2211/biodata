# Streaming implementation notes

* Two single-node Kafka clusters (`apache/kafka:3.8.0`, KRaft). Advertised listeners use `127.0.0.1`
  (Colima/Docker Desktop on macOS refuse IPv6 `localhost`).
* Spark: `applyInPandasWithState`, output mode `append`, `GroupStateTimeout.NoTimeout`; state is one JSON string per patient.
* Events of a patient inside a micro-batch are sorted by `seq` before stepping the state.
* `--emit-all` writes one alert per event; used only to measure latency. Production mode alerts only when the alarm fires.
* PySpark 3.5 `applyInPandasWithState` needs pandas 2.2.x (pandas 3 turns the state-info row into floats and
  `RecordBatch.slice` fails). Pinned in `requirements-spark.txt`.
