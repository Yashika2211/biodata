# Presentation and viva guide — Yashika Bhatia

## 1. The project in one minute
Hospital monitors use one fixed threshold for everyone (e.g. "SpO2 < 92 %"), so a patient whose normal SpO2 is 90 %
alarms all day. I built a streaming system (Kafka + Spark Structured Streaming) that learns each patient's own baseline
and alarms only when the patient deviates from *their* normal. I then asked: **can it match a centralised baseline while
raw data stays at the hospital?** I compared eight methods (A–G) on a public dataset (eICU demo) and a synthetic one.

## 2. How to run it (live demo order)
```bash
cd "big data"
make test                     # 91 tests pass (30 s)
make up                       # starts two Kafka clusters (Docker must be running)
make local-demo               # Kafka-free demo: prints alerts with hashed ids, no vitals
# streaming demo (3 terminals, Java 17 needed):
export JAVA_HOME=$(brew --prefix openjdk@17) PYSPARK_PYTHON=$PWD/.venv-spark/bin/python PYTHONPATH=src
.venv-spark/bin/python -m pvm.stream.spark_job --emit-all &
.venv-spark/bin/python -m pvm.stream.consumer --idle 30 &
.venv-spark/bin/python -m pvm.stream.producer --rate 200 --events 3000 --patients 100
```
Full re-run of all experiments: `make experiments` (about 1 hour). Open `dist/report/report.pdf` and `dist/ppt/deck.pptx`.
If the live demo fails, show `figures/` and `results/summary.json` — never improvise numbers.

## 3. Speaking script (10–15 min, one block per slide)
1. **Title (30 s).** "My project asks whether a hospital can detect deteriorating patients in real time without sending raw data away."
2. **Problem (1 min).** Alarm fatigue; patients differ (athlete HR 52, COPD SpO2 90); pooling data raises privacy/bandwidth issues.
3. **Architecture (1.5 min).** Two Kafka clusters: site (raw vitals, 1 h retention) and central (alerts only). Spark keeps per-patient state
   as JSON and scores each event. Alerts hold only a salted-hash id, site, time, score, model tag. The same feature code runs in
   training and serving, and a test proves they match exactly.
4. **Adaptive baseline (1.5 min).** Show the COPD plot: fixed threshold 97 alarms in 4 days, adaptive 6. Explain EWMA mean/variance,
   judge-before-update, winsorising, slower learning while abnormal, prior for cold start, NaN = no evidence.
5. **Accuracy (2 min, two slides).** Static: ~8 false alarms/patient-day. Adaptive threshold: 81 % fewer (synthetic), 86 % fewer (eICU).
   ML on adaptive features F1 0.56 / 0.32. Say: injected labels, not clinical truth.
6. **Federated (1 min).** FedAvg matches centralised: F1 difference +0.005 [−0.003, +0.013]. "Indistinguishable with 5 seeds", not "identical".
7. **Privacy (1.5 min).** DP-SGD: clip, add noise, Rényi accountant. Free until large noise. ε is **record-level, not patient-level**.
8. **Latency (1 min).** ~1 s p50 at 1000 events/s on a laptop; microseconds per event in-process. Mention the unexplained low-rate anomaly honestly.
9. **Cost (1 min).** ~475× fewer bytes leave the site; prices are illustrative assumptions.
10. **Limitations (1 min)** and 11. **Conclusion (30 s).** Read the limitations yourself before the teacher does.

## 4. Questions teachers will ask — short answers
* *Why semi-synthetic?* Public vitals have no anomaly labels; injected labelled episodes is the standard workaround. Results are not clinical performance.
* *Why did you change the alarm metric?* An always-on alarm scored a fake-good F1 under "overlap" counting; now alarms re-fire hourly (tested).
* *Is federated really better?* No — it matches centralised; its benefit is that raw rows stay local.
* *Why does DP not hurt?* Each site has tens of thousands of rows and a small sampling rate; the ε is per record, much weaker than per patient.
* *Is FL really over Kafka?* Experiments use an in-process simulation; a demo (`fl_kafka.py`) runs it over Kafka and gives the identical model.
* *Why is B (fixed priors) sometimes similar in F1 to D?* On synthetic the F1 gain is within noise; AUROC/AUPRC improve. On eICU F1 improves by ~0.05 (CI excludes 0).

## 5. Advantages
Personalised thresholds (far fewer false alarms); raw data stays local; tiny model (16 parameters), explainable; microsecond scoring;
one shared code path (no train/serve skew); reproducible (everything regenerated from `summary.json`); honest statistics (5 seeds, paired CIs);
~475× less data leaves the site.

## 6. Disadvantages / limitations
Injected labels, not real annotated alarms; DP is record-level only; FL simulated in-process; only a weak membership-inference check;
linear model only; thresholds tuned on labelled data; small public sample with wide intervals; latency measured on one laptop, with an
undiagnosed anomaly at low rates; eICU invasive BP and temperature mostly missing; cold-start patients are judged against population priors.

## 7. Showing it to your data science teacher
Yes — it fits both courses. Big-data teacher: emphasise Kafka, Spark state, latency, cost. Data-science teacher: emphasise the evaluation
design (time-ordered split, no leakage, paired CIs, the metric loophole you found and fixed), the federated/DP accounting, ablations and limitations.
Tell both teachers it is the same project (check your course's policy on reusing work), and be ready to explain every number yourself.
