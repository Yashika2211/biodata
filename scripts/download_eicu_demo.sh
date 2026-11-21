#!/usr/bin/env bash
# Download the open-access eICU-CRD demo files needed by the study.
set -euo pipefail
DEST="${1:-data/raw/eicu-demo}"
BASE="https://physionet.org/files/eicu-crd-demo/2.0.1"
mkdir -p "$DEST"
for f in vitalPeriodic.csv.gz patient.csv.gz; do
  [ -s "$DEST/$f" ] || curl -fL --retry 3 -o "$DEST/$f" "$BASE/$f"
done
ls -lh "$DEST"
