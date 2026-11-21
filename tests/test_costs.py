from pvm import costs as CO


def test_federated_sends_far_fewer_bytes_than_raw_streaming():
    r = CO.scenario_costs(avg_event_bytes=150, avg_alert_bytes=120, alarms_per_patient_day=2.0,
                          cpu_s_per_million_events=15.0)
    assert r["federated_bytes"] < r["raw_stream_bytes"] / 50
    assert r["egress_usd_federated"] < r["egress_usd_raw"]


def test_prices_are_in_one_place_and_overridable():
    a = CO.scenario_costs(150, 120, 2.0, 15.0)
    b = CO.scenario_costs(150, 120, 2.0, 15.0, prices={"egress_usd_per_gb": 0.18})
    assert abs(b["egress_usd_raw"] - 2 * a["egress_usd_raw"]) < 1e-12
