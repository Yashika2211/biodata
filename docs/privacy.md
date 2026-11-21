# Privacy mechanisms and what they do (not) protect

| Mechanism | Protects | Does not protect |
|---|---|---|
| Alerts carry only salted-hash id, site, ts, score, model | raw vitals and identifiers leaving the site | linkage by someone who knows the salt; timing side channels |
| 1 h retention on `kafka-site` | long-term raw storage | anything inside the retention window |
| FedAvg | raw rows never leave a site | model updates can leak information |
| DP-SGD (clip + Gaussian noise) | a single **record** (one patient-time-step) | a **patient** (hundreds of correlated records) |
| Count-table threshold tuning | rows (only aggregates shared) | aggregates are shared without noise |
