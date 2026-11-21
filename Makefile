PY ?= .venv/bin/python
SPARKPY ?= .venv-spark/bin/python
JAVA_HOME ?= $(shell brew --prefix openjdk@17 2>/dev/null)
export PYTHONPATH := src
export JAVA_HOME

.PHONY: venv data test up down topics experiments figures docs dist spark-job bench clean

venv:
	uv venv --python 3.11 .venv && uv pip install --python .venv/bin/python -r requirements.txt psutil
	uv venv --python 3.11 .venv-spark && uv pip install --python .venv-spark/bin/python -r requirements-spark.txt scipy scikit-learn matplotlib

data:
	scripts/download_eicu_demo.sh

test:
	$(PY) -m pytest -q

up:
	docker compose up -d
	scripts/create_topics.sh

down:
	docker compose down -v

experiments:
	$(PY) -m pvm.experiments --dataset synthetic --seeds 5
	$(PY) -m pvm.experiments --dataset eicu --seeds 5
	$(PY) -m pvm.bench_inprocess
	$(PY) -m pvm.bench_fl_kafka
	PYSPARK_PYTHON=$(SPARKPY) $(SPARKPY) -W ignore -m pvm.stream.bench_kafka
	$(PY) -m pvm.summary

figures:
	$(PY) -m pvm.figures

docs:
	$(PY) -m pvm.make_report
	$(PY) -m pvm.make_deck

dist:
	$(PY) scripts/make_dist.py

clean:
	rm -rf results/*.json figures/*.png dist

bench-kafka:
	PYSPARK_PYTHON=$(SPARKPY) $(SPARKPY) -W ignore -m pvm.stream.bench_kafka

local-demo:
	$(PY) examples/local_runner_demo.py

all: test experiments figures docs dist
