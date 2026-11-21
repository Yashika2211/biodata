# Reading the results

All numbers are produced by `make experiments` into `results/raw_<dataset>.json` and aggregated into
`results/summary.json`. The report and deck are generated from that file; nothing is typed by hand.

* `datasets.<name>.methods.<A..G>.<metric>` → `{mean, sd, n}` over seeds.
* `datasets.<name>.paired.<X_minus_Y>.<metric>` → mean difference with a t-based 95 % CI (`n = 5`, so intervals are wide).
* `datasets.<name>.privacy_utility` → the DP curve (σ, record-level ε, F1, AUROC, AUPRC).
* `datasets.<name>.ablations` → α, m, DP clip, number of sites, FL rounds (3 seeds).
* `latency.inprocess` / `latency.kafka` → serving latency and Kafka→Spark→Kafka end-to-end latency.
* `cost` → bytes leaving the site and illustrative dollar figures; every assumed price is in `src/pvm/costs.py`.
