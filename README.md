# Privacy-Preserving Patient Vitals Monitoring — a Kafka + Spark Streaming study

Stream patient vitals (heart rate, SpO2, respiratory rate, systolic BP, temperature), flag anomalies
instantly with **per-patient adaptive thresholds**, and test whether the system can **match baseline
accuracy while raw data stays local** (federated learning and record-level differential privacy).

## Quick start

```bash
make venv          # Python 3.11 venv (.venv) with core + Spark requirements
make test          # unit tests (pytest)
make data          # download the open eICU-CRD demo (PhysioNet, no credentials)
make up            # two Kafka (KRaft) clusters + topics via Docker Compose
make experiments   # full study on BOTH datasets (5 seeds, ablations) + benchmarks -> results/summary.json
make figures       # all figures -> figures/ and docs/architecture.png
make docs          # report (.docx/.pdf) and deck (.pptx), generated from results/summary.json
make dist          # dist/code.zip, dist/report.zip, dist/ppt.zip
```
