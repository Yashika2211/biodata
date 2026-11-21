# Data notes

## eICU-CRD demo (public)
`vitalPeriodic.csv.gz` columns used: `patientunitstayid`, `observationoffset` (minutes), `heartrate`, `sao2`,
`respiration`, `systemicsystolic`, `temperature`. Offsets are rounded to 5-minute bins; gaps are NaN. Stays need
>= 600 samples (50 h), >= 80 % HR, >= 60 % SpO2 and >= 50 % RR coverage; series are capped at 1152 samples (4 days).
`systemicsystolic` (invasive) and `temperature` are mostly missing in this table.

## Synthetic cohort
See `src/pvm/data/synthetic.py`: six phenotypes, Dirichlet per-site mixes, AR(1) noise (phi 0.85), circadian drift,
2.5 artefacts/day of 1-8 samples labelled normal, random dropouts and probe-off bursts.
