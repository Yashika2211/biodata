#!/usr/bin/env bash
# One-command live demo: starts Kafka, runs Spark, replays vitals, prints the alerts that reach the central cluster.
set -euo pipefail
cd "$(dirname "$0")/.."
export JAVA_HOME="${JAVA_HOME:-$(brew --prefix openjdk@17)}" PATH="$JAVA_HOME/bin:$PATH"
export PYSPARK_PYTHON="$PWD/.venv-spark/bin/python" PYTHONPATH=src
PY=.venv-spark/bin/python

command -v docker >/dev/null || { echo "Install Docker/Colima first"; exit 1; }
docker info >/dev/null 2>&1 || { echo "Starting Colima..."; colima start; }
echo "== 1/4 starting the two Kafka clusters =="
docker compose up -d && sleep 15 && scripts/create_topics.sh >/dev/null
echo "== 2/4 starting Spark streaming job (takes ~45 s) =="
rm -rf /tmp/pvm-demo-ck
$PY -W ignore -m pvm.stream.spark_job --trigger "1 second" --checkpoint /tmp/pvm-demo-ck > /tmp/pvm_spark.log 2>&1 &
SPARK=$!
trap 'kill $SPARK 2>/dev/null || true' EXIT
sleep 45
echo "== 3/4 listening on kafka-central for alerts =="
cat > /tmp/pvm_show.py <<'PYEOF'
import json, time
from kafka import KafkaConsumer
c = KafkaConsumer("alerts.central", bootstrap_servers="127.0.0.1:9093", auto_offset_reset="latest",
                  group_id=f"show-{time.time()}", value_deserializer=lambda b: json.loads(b.decode()),
                  consumer_timeout_ms=45000)
n = 0
for m in c:
    n += 1
    print("ALERT:", m.value, flush=True)
print("total alerts:", n)
PYEOF
$PY -W ignore /tmp/pvm_show.py &
sleep 4
echo "== 4/4 replaying 20000 vitals events (raw data -> kafka-site only) =="
$PY -W ignore -m pvm.stream.producer --rate 1500 --events 20000 --patients 160
wait %2 2>/dev/null || sleep 45
echo "Done. Alerts contain only a hashed id, site, time, score, model - never vitals."
