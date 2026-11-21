#!/usr/bin/env bash
# Create topics on both clusters. Raw vitals: short retention (1 h) on kafka-site.
set -euo pipefail
KT=/opt/kafka/bin/kafka-topics.sh
NSITES="${NSITES:-4}"
for i in $(seq 0 $((NSITES-1))); do
  docker exec kafka-site $KT --bootstrap-server localhost:9092 --create --if-not-exists \
    --topic "vitals.raw.site${i}" --partitions 4 --config retention.ms=3600000
done
docker exec kafka-central $KT --bootstrap-server localhost:9093 --create --if-not-exists \
  --topic alerts.central --partitions 2
docker exec kafka-site $KT --bootstrap-server localhost:9092 --list
docker exec kafka-central $KT --bootstrap-server localhost:9093 --list
