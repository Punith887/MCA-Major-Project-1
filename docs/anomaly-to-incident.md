# Phase 2 Stage 1: Prometheus anomaly-to-incident pipeline

## What is implemented

This increment adds an authenticated, project-scoped API workflow:

1. Create a local project.
2. Register a project resource against a Prometheus job with at least one active,
   healthy target.
3. Query recent CPU, memory, request-rate, and HTTP 5xx-rate samples from
   Prometheus.
4. Score complete samples with scikit-learn Isolation Forest.
5. Persist newly flagged observations and create linked medium-severity incidents.
6. List the current user's persisted anomalies and incidents.

The current Compose target, `aiops-backend`, exposes FastAPI process CPU and memory
and application HTTP request metrics. This increment does not provide Windows host
or container resource metrics.

## Local configuration

For Docker Compose, the backend connects to Prometheus at
`http://prometheus:9090` on the Compose network. For a backend run directly on
Windows, the default is `http://localhost:9090`. Override it with `PROMETHEUS_URL`
when using a different local endpoint.

Detector defaults are a 60-minute lookback, 30 minimum valid samples, and 0.05
contamination. They can be configured with `ANOMALY_LOOKBACK_MINUTES`,
`ANOMALY_MINIMUM_SAMPLES`, and `ANOMALY_CONTAMINATION`. At least 15 minutes of
history is required by configuration validation.

After updating the backend code, start or rebuild the local stack with
`docker compose up --build`; the existing startup migration is additive and does
not reset PostgreSQL data or volumes. Confirm Prometheus reports the
`aiops-backend` target as `UP` and allow enough real scrape history to accumulate
before requesting detection.

## API workflow

Use an authenticated account and the OpenAPI page at <http://localhost:8000/docs>:

- `POST /api/projects` with a name and optional description.
- `POST /api/monitoring/resources` with the returned `project_id` and a healthy
  Prometheus `prometheus_job` such as `aiops-backend`.
- `POST /api/anomalies/detect` with the returned `resource_id`.
- `GET /api/anomalies` and `GET /api/incidents` to inspect persisted results.

The response reports the actual sample and anomaly counts. Zero anomalies is a
valid result. Repeating detection against the same timestamped samples does not
create duplicate anomaly or incident records. Each incident description includes
the observed features and explicitly identifies the score as a decision-function
score, not a probability.

All project, resource, anomaly, and incident reads are scoped to projects owned by
the authenticated user. Creating a project also records a project-created audit
entry.

## Interpretation and limitations

Isolation Forest detects unusual observations in the queried window. It does not
forecast resource pressure, establish a future horizon, or estimate failure
probability. The contamination setting influences the expected outlier fraction
and is not an empirically measured false-positive rate. The current implementation
does not yet have a labeled production dataset, chronological model evaluation,
host/container telemetry, or an automated detection schedule.

Backend tests use explicitly synthetic Prometheus fixtures to prove the API and
storage path. They are test-only data and are not a live-system or production
performance result. For a live check, query the configured Prometheus instance and
report its observed sample and detection counts without injecting test records
into the persistent database.

## Focused tests

From the repository root, with the backend virtual environment active:

```powershell
pytest backend\tests\test_anomaly_detection.py backend\tests\test_prometheus_service.py backend\tests\test_api.py
```

The tests use an isolated in-memory SQLite database. The additive Alembic
migration is `20261031_0002`; do not rewrite the Phase 1 migration.
