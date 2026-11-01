# Phase 2 local monitoring setup

## Current scope

FastAPI exposes HTTP request count, response latency, and Python process metrics
at `/metrics`. Prometheus scrapes the backend and itself every 15 seconds.
Grafana provisions Prometheus as its default data source and loads the
`Infrastructure Overview` dashboard automatically.

Prometheus also scrapes the Windows Exporter at
`host.docker.internal:9182` under the `windows-exporter` job. The authenticated
`GET /api/monitoring/host-metrics` endpoint serves timestamped Windows host CPU
and physical-memory percentages to the React dashboard; the dashboard refreshes
these charts every 15 seconds. The browser only communicates with the backend,
not Prometheus. Configure the dashboard login before checking the charts, and
confirm the `windows-exporter` target is `UP` if live values are unavailable.

Windows host disk usage is a future extension. Per-volume values need a
deliberate volume-selection/display contract before they can be shown reliably.
Do not infer host metrics from the separate backend process metrics.

## Start locally

Run from the project root in PowerShell. Ensure `.env` exists and has non-
placeholder `POSTGRES_PASSWORD`, `SECRET_KEY`, and `GRAFANA_ADMIN_PASSWORD`
values. Generate local values with Python:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Start the services:

```powershell
docker compose up --build -d
docker compose ps
```

Expected: PostgreSQL, backend, Prometheus, and Grafana report healthy, and
frontend is running. The first run downloads images and builds the application.
Grafana also initializes its local database on first start, which can take
several minutes; wait for it to report healthy before opening the dashboard.

Open:

- Metrics exposition: <http://localhost:8000/metrics>
- Prometheus targets: <http://localhost:9090/targets> (`aiops-backend` should
  become `UP` after its first scrape)
- Grafana: <http://localhost:3000>, using `GRAFANA_ADMIN_USER` and
  `GRAFANA_ADMIN_PASSWORD` from `.env`
- Dashboard: <http://localhost:3000/d/aiops-infrastructure/aiops-infrastructure>

The metrics endpoint should return Prometheus text including
`http_requests_total` after requests have been made. The dashboard can take
one or two scrape intervals to show data.

## Troubleshooting

Run from the project root:

```powershell
docker compose logs backend
docker compose logs prometheus
docker compose logs grafana
docker compose ps
```

If `aiops-backend` is `DOWN`, confirm the backend is healthy and can be reached
on the Compose monitoring network. If Grafana cannot log in, inspect the
current local credentials in `.env`; do not publish them in screenshots or
commit them.

To stop services without deleting data:

```powershell
docker compose down
```

Prometheus and Grafana data are persisted in named Compose volumes. Do not use
`docker compose down -v` unless you explicitly intend to delete those volumes.

## Platform note

The Windows host exporter is external to Docker Compose; its scrape target is
configured in `monitoring/prometheus/prometheus.yml`. GCP deployment is
intentionally deferred to Phase 3.
