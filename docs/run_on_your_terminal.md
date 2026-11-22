# Run it on your own terminal (macOS)

One-time setup (already done on this Mac): Docker via Colima, Java 17 (`brew install openjdk@17`), `uv`, then `make venv`.

```bash
cd "~/Desktop/big data"      # the project folder
make test                    # 1) tests (about 30 s) -> "90 passed, 1 skipped"
make local-demo              # 2) quick demo, no Kafka: prints a few alerts
scripts/demo.sh              # 3) full live demo: Kafka + Spark + alerts (about 2.5 min)
```
When finished: `make down` (stops Kafka) and `colima stop`.

Show the teacher: `open dist/report/report.pdf` and `open dist/ppt/deck.pptx`.
Troubleshooting: "Cannot connect to Docker" -> `colima start`; Java error -> `brew install openjdk@17`;
missing packages -> `make venv`.
