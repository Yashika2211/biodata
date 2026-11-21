"""Cost model.  Every assumed price lives in PRICES (one place, used everywhere).

Prices are *illustrative* round numbers in the range of public cloud list
prices; they are assumptions, not measurements.  Bytes and CPU-seconds, in
contrast, are measured by the benchmarks.
"""
from __future__ import annotations

PRICES = {
    "egress_usd_per_gb": 0.09,        # data leaving the hospital network / cloud region
    "vcpu_usd_per_hour": 0.04,        # one vCPU on a general-purpose VM
    "storage_usd_per_gb_month": 0.023,
}

SCENARIO = {
    "patients": 1000,                 # monitored patients across all sites
    "days": 30,
    "sample_minutes": 5.0,            # eICU vitalPeriodic cadence
    "fl_rounds": 100,                 # rounds used by the federated model
    "fl_retrains_per_month": 1,
    "threshold_grid_points": 161,     # count table shared for threshold tuning
}


def scenario_costs(avg_event_bytes, avg_alert_bytes, alarms_per_patient_day,
                   cpu_s_per_million_events, n_sites=4, n_features=15,
                   scenario=None, prices=None):
    sc = dict(SCENARIO, **(scenario or {}))
    pr = dict(PRICES, **(prices or {}))
    events = sc["patients"] * sc["days"] * 1440.0 / sc["sample_minutes"]
    raw_bytes = events * avg_event_bytes
    alert_bytes = sc["patients"] * sc["days"] * alarms_per_patient_day * avg_alert_bytes
    d = n_features + 1
    model_bytes = sc["fl_retrains_per_month"] * (sc["days"] / 30.0) * sc["fl_rounds"] * n_sites * 2 * d * 8
    count_bytes = n_sites * sc["threshold_grid_points"] * 5 * 8
    fed_bytes = alert_bytes + model_bytes + count_bytes
    cpu_hours = events / 1e6 * cpu_s_per_million_events / 3600.0
    usd = lambda b: b / 1e9 * pr["egress_usd_per_gb"]
    return dict(
        events=events, raw_stream_bytes=raw_bytes, federated_bytes=fed_bytes,
        alert_bytes=alert_bytes, model_update_bytes=model_bytes, count_table_bytes=count_bytes,
        reduction_factor=raw_bytes / fed_bytes if fed_bytes else float("inf"),
        egress_usd_raw=usd(raw_bytes), egress_usd_federated=usd(fed_bytes),
        scoring_cpu_hours=cpu_hours, scoring_usd=cpu_hours * pr["vcpu_usd_per_hour"],
        scenario=sc, prices=pr)
