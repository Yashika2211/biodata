# FAQ

**Why are results labelled semi-synthetic?** Public vitals have no anomaly labels, so episodes are injected.

**Why 127.0.0.1 and not localhost?** IPv6 localhost is refused by Colima/Docker Desktop port forwarding on macOS.

**Why a second venv for Spark?** PySpark 3.5 applyInPandasWithState breaks with pandas 3; the Spark venv pins pandas 2.2.

**Is epsilon patient-level?** No. It is record-level (one patient-time-step). See docs/privacy.md.

**Why does low event rate show higher latency?** Observed in our sweep and not diagnosed; see the report.
