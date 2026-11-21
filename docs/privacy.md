# Privacy mechanisms and what they do (not) protect

| Mechanism | Protects | Does not protect |
|---|---|---|
| Alerts carry only salted-hash id, site, ts, score, model | raw vitals and identifiers leaving the site | linkage by someone who knows the salt; timing side channels |
| 1 h retention on `kafka-site` | long-term raw storage | anything inside the retention window |
| FedAvg | raw rows never leave a site | model updates can leak information |
| DP-SGD (clip + Gaussian noise) | a single **record** (one patient-time-step) | a **patient** (hundreds of correlated records) |
| Count-table threshold tuning | rows (only aggregates shared) | aggregates are shared without noise |

## Accounting
Rényi-DP for the Poisson-subsampled Gaussian mechanism (integer-order expansion, Mironov–Talwar–Zhang 2019, as used by
Abadi et al. 2016), converted to (ε, δ) with the Balle et al. (2020) bound, δ = 1e-5. Every site uses the same sampling
rate `q`, so ε is identical across sites. **ε is record-level**; do not read it as patient-level.

## Attack check
`pvm.experiments.run_mia`: loss-threshold membership inference at the patient level (members vs held-out patients).
A weak attack; AUROC ~0.5 is a sanity check, not a proof.
