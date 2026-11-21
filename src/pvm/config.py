"""Central constants: vitals, population priors, ward thresholds, defaults.

Units: HR bpm, SpO2 %, RR breaths/min, SBP mmHg, temperature degrees C.

Everything that more than one module needs lives here so that offline
training, evaluation, the local runner and the Spark job cannot drift apart.
"""
from __future__ import annotations

VITALS = ("hr", "spo2", "rr", "sbp", "temp")
NV = len(VITALS)

# Population priors (mean, sd) used for cold start and for the fixed
# normalisation of the centralised baseline (method B).
PRIOR_MEAN = {"hr": 80.0, "spo2": 96.5, "rr": 16.0, "sbp": 120.0, "temp": 36.9}
PRIOR_SD = {"hr": 14.0, "spo2": 2.0, "rr": 3.5, "sbp": 18.0, "temp": 0.45}

# Minimum scale (floor on the per-patient sd) per vital.
MIN_SCALE = {"hr": 4.0, "spo2": 1.0, "rr": 1.5, "sbp": 6.0, "temp": 0.2}

# Physiologically plausible ranges; anything outside is treated as missing.
VALID_RANGE = {
    "hr": (20.0, 250.0),
    "spo2": (50.0, 100.0),
    "rr": (4.0, 70.0),
    "sbp": (40.0, 280.0),
    "temp": (30.0, 43.0),
}

# Static ward thresholds (method A).  (low, high); None = not checked.
WARD_THRESHOLDS = {
    "hr": (50.0, 120.0),
    "spo2": (92.0, None),
    "rr": (10.0, 24.0),
    "sbp": (90.0, None),
    "temp": (35.5, 38.5),
}

# Adaptive-state hyper-parameters.
ALPHA = 0.02          # EWMA rate (per sample); at 5 min sampling ~ 4 h memory
PRIOR_COUNT = 12.0    # pseudo-observations carried by the population prior
WINSOR_K = 3.0        # winsorise updates at mean +/- K * sd
ABNORMAL_Z = 2.5      # |z| above this => "abnormal", learn slowly
SLOW_FACTOR = 0.1     # learning-rate multiplier while abnormal
WINDOW = 6            # samples in the windowed features (30 min at 5 min)

# Alarm rule.
PERSISTENCE_M = 3     # consecutive samples above threshold

# Sampling interval of the data (minutes).  eICU vitalPeriodic is 5 min.
DT_MIN = 5.0

FEATURE_NAMES = (
    [f"z_{v}" for v in VITALS]
    + [f"zmean_{v}" for v in VITALS]
    + [f"zmaxabs_{v}" for v in VITALS]
)
NF = len(FEATURE_NAMES)  # 15

MODEL_TAG = "lr-adaptive-v1"
