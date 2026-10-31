# Local monitoring

The local Compose stack includes Prometheus and Grafana. FastAPI exposes
Prometheus-format application metrics at `http://localhost:8000/metrics`;
Prometheus scrapes that endpoint every 15 seconds. The exporter is excluded
from its own HTTP request counters to avoid scrape-generated metric noise.

The provisioned `Infrastructure Overview` dashboard currently shows observed
API availability, request rate, response latency, and backend process CPU and
memory. It does not claim host or container measurements yet. Container
telemetry and log collection are separate upcoming Phase 2 increments.

Prometheus and Grafana are bound to loopback only at ports 9090 and 3000.
Grafana requires `GRAFANA_ADMIN_PASSWORD` in the root `.env` file. Generate a
local value with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste that value into `.env`; do not commit it. The configuration is local
development infrastructure, not a production-hardened monitoring stack.

Node Exporter is intentionally not configured: this project is developed on
Windows, and the Linux Node Exporter does not provide Windows host metrics.
Windows host telemetry will need an appropriate Windows exporter if it becomes
part of the local demonstration.
