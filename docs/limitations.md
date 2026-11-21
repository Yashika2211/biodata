# Limitations (short form; the report has the full discussion)

1. DP is record-level, not patient-level.
2. Federated learning is simulated in one process, not run over Kafka.
3. Only a simple membership-inference check; no stronger attacks.
4. Labels are semi-synthetic (injected episodes).
5. Simple linear model.
6. Thresholds tuned on labelled data.
7. Small public sample; wide intervals; seeds resample the same real stays.
8. Latency measured on one laptop, single broker per cluster, Spark local mode.
