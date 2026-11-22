# Easy-words presentation script (about 10 minutes) — Yashika Bhatia

Tip: speak slowly, point at the picture on each slide, and say "injected labels" whenever you quote accuracy.

**Slide 1 — Title.** "Good morning. My project is about watching patients' vital signs in real time and raising an alarm when
someone is getting worse — without sending their private data out of the hospital."

**Slide 2 — The problem.** "Hospital monitors use one fixed rule for everyone, for example 'alarm if oxygen is below 92'. But some patients,
like people with lung disease, normally have oxygen around 90. For them the alarm rings all day. Nurses then start ignoring alarms —
this is called alarm fatigue. My question: can we make smarter alarms and still keep patient data private?"

**Slide 3 — How the system works.** "Think of two post offices. The first one, at the hospital, receives the raw vital signs and keeps them
for only one hour. A program called Spark reads them live. The second post office, the central one, only receives alerts —
and those contain just a scrambled patient ID, the time and a score, never the actual vital signs. The same code is used for training and
for live running, and I wrote a test to prove both give exactly the same answers."

**Slide 4 — The main idea.** "Instead of one rule for everybody, the system learns each patient's own normal. In this picture the patient's normal
oxygen is 90. The orange dots are where the old fixed rule shouts: 97 alarms in four days. The blue band is this patient's own normal range,
and only 6 alarms fire — including the real emergency, the shaded part."

**Slides 5 and 6 — Accuracy.** "I tested on two datasets: a simulated one and a real public hospital dataset, eICU. The real hospital
vital signs are real, but the emergencies are injected by me, because public data has no emergency labels — so these are not clinical results.
The old fixed rule gives about 8 false alarms per patient per day. My adaptive rule cuts that by 81 percent on simulated data and 86 percent on the real data.
Adding a small machine-learning model on top improves detection further."

**Slide 7 — Federated learning.** "Federated learning means each hospital trains the model on its own data and only shares the model's numbers,
not the patient rows. The result is almost the same as pooling all the data: the difference is tiny and within the margin of error.
So we get the same accuracy and keep data local."

**Slide 8 — Privacy noise.** "To protect people even more, I add a little random noise during training — this is differential privacy.
Small and medium noise costs almost nothing in accuracy. Only very large noise hurts. One honest note: this protects a single data row,
not a whole patient."

**Slide 9 — Speed.** "In my test, an alert reaches the central server in about one second at 1000 events per second, on a laptop.
Scoring one event takes a few millionths of a second. For vitals measured every 5 minutes, that is fast enough."

**Slide 10 — Cost.** "Sending only alerts and model updates means about 475 times less data leaves the hospital than streaming everything.
The dollar figures use example prices, so treat them as illustrations."

**Slide 11 — Limitations.** "To be honest: the emergencies are injected, not real; the privacy protection is per row, not per patient;
the federated learning was simulated on one computer; and the model is simple."

**Slide 12 — Conclusion.** "Yes — smarter per-patient alarms mean far fewer false alarms, federated learning matches centralised learning,
privacy noise is cheap until it is large, and raw data stays at the hospital. Next step: test on real, nurse-confirmed alarms. Thank you."

## Run log (checked before sending to you)
* `make test`: 90 passed, 1 skipped (the skipped one needs Kafka; it passed separately once Kafka was up).
* Kafka-free demo: 3 alerts, hashed ids only.
* Live Kafka -> Spark -> Kafka run: 3000 events sent at 200/s, 3000 alerts received, **0 privacy violations**,
  p50 about 1.5 s, p95 about 5 s (a short cold run; the report's sweep has the steady-state numbers).
