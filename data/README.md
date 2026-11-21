# Data

Data files are **not** committed (and not shipped in `code.zip`).

## Public dataset: eICU Collaborative Research Database, demo v2.0.1

Open access on PhysioNet (no credentials needed):

```
make data            # runs scripts/download_eicu_demo.sh
```

or manually place these two files in `data/raw/eicu-demo/`:

* `vitalPeriodic.csv.gz`
* `patient.csv.gz`

from <https://physionet.org/content/eicu-crd-demo/2.0.1/>.

Columns used from `vitalPeriodic`: `patientunitstayid`, `observationoffset`
(minutes), `heartrate`, `sao2`, `respiration`, `systemicsystolic`, `temperature`.
`patient.csv` supplies `hospitalid`, which defines the (non-IID) sites.

The database has no independent anomaly labels; the study injects labelled
deterioration episodes into the real series (semi-synthetic protocol).
`systemicsystolic` (invasive BP) and `temperature` are sparse in
`vitalPeriodic`; missing values are treated as "no evidence".
