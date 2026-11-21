# CLAUDE.md — conventions for this repo

Project: privacy-preserving patient-vitals monitoring (Kafka + Spark Structured Streaming).

## Layout
- `src/pvm/features.py` — the **only** feature/state code. Offline training, offline evaluation,
  the Kafka-free runner and the Spark job all call `features.process_event`. Never duplicate it.
- `src/pvm/serving.py` — `step()` (one event), alert builder, `LocalRunner`.
- `src/pvm/methods.py` — methods A, A2, B, C, D, E, F, G. `experiments.py` runs seeds/ablations.
- `src/pvm/summary.py` → `results/summary.json`. **All numbers in the report and deck come from it.**
  Never hand-type a result into text; change the generator instead.
- `src/pvm/stream/` — Kafka producer/consumer, Spark job, end-to-end benchmark.

## Rules
- Every table/figure names its dataset (`Synthetic cohort` or `eICU-CRD demo + injected episodes`).
- Never present synthetic results as results on the public dataset.
- Alerts leaving the site hold only: salted-hash id, site, ts, score, model tag (+ producer ts for latency).
- DP epsilon is **record-level**; always say so.
- A perfect score is a bug until proven otherwise (e.g. the always-on alarm loophole was fixed by re-firing alarms).
- Held-out = last 40 % of every series; training/tuning only sees the first 60 %; no episode crosses the split.
- Threshold tuning must use aggregate counts only (see `thresholds.py`).

## Environments
- `.venv` (Python 3.11): core + tests + figures + docs (`requirements.txt`).
- `.venv-spark` (Python 3.11, Java 17): Spark/Kafka (`requirements-spark.txt`; pandas must stay 2.2.x for PySpark 3.5).
- Kafka clients must use `127.0.0.1` (not `localhost`; IPv6 is refused under Colima/Docker Desktop on macOS).

## Commands
`make test`, `make up`, `make experiments`, `make figures`, `make docs`, `make dist`.

## Style
Small modules, type hints where cheap, pytest for every claim. Commit small, one idea per commit.
