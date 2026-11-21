# Experimental protocol

* **Split:** first 60 % of each patient's series = training and threshold tuning; last 40 % = held-out evaluation.
  The adaptive state keeps running across the boundary (as it would in deployment).
* **Episodes:** sepsis-like, hypoxia, shock, bradycardia/hypotension; 1.5–6 h; linear ramp over ~half the episode;
  placed separately in the train and test regions so none crosses the split.
* **Seeds:** 5 (fresh synthetic cohort, or resampled 85 % of eligible eICU stays with fresh episodes each).
  Ablations use the first 3 seeds.
* **Alarm tolerance:** 30 minutes. Persistence m = 3 (not for A). Alarms re-fire every 60 minutes while the condition holds.
* **Tuning:** the F1-maximising threshold from aggregate count tables on the training region (after a 2 h burn-in).
* **Federated:** FedAvg, full participation, 3 local full-batch steps per round, lr 0.3, up to 400 rounds; the centralised optimum
  is used only as a diagnostic to report rounds-to-converge (relative loss gap < 1e-3).
* **DP:** per-record clip 10, Poisson rate 0.02, 150 rounds x 3 steps, delta 1e-5, sigma in {0.5, 2, 8, 32, 128}.
