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
