# Methodology

## Adaptive baseline
For each vital of each patient we keep an EWMA mean `mu` and variance `var`.
A sample `x` is scored first, then used to update the state:

```
z   = (x - mu) / max(sd, s_min)          # judged against the OLD baseline
x'  = clip(x, mu - 3 sd, mu + 3 sd)      # winsorised update
rate = max(alpha, 1 / (n + k0))          # prior pseudo-count k0 = 12 for cold start
rate *= 0.1 if |z| > 2.5                 # learn slowly while abnormal
```

NaN (missing or implausible) means *no evidence*: no state update, zero contribution to the model.

## Features and model
15 features: for each vital the current z, the mean z over the last 6 samples, and the max |z| over those samples.
Model: class-weighted L2 logistic regression on standardised features. Class weights and standardiser use aggregate
counts/moments only, so every statistic is federatable.

## Alarm definition
An alarm event fires when the score exceeds the threshold for `m` consecutive samples and re-fires hourly while the
condition persists (so an always-on alarm cannot count as one event). An alarm firing inside an episode padded by 30 min
is a true positive; an episode is detected if at least one alarm fires in its padded window; repeated alarms inside one
detected episode are merged. Delay = first firing minus episode start (never negative).

This definition replaced an earlier "span overlaps an episode" rule after we noticed an always-on alarm achieved
recall 1.0 and F1 ~0.6 with it — a perfect-looking score that was a metric loophole (see `tests/test_metrics.py`).
