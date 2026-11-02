# Phase 2 Stage 1: Prometheus anomaly-to-incident pipeline

## What is implemented

This increment adds an authenticated, project-scoped API workflow:

1. Create a local project.
2. Register a project resource against a Prometheus job with at least one active,
   healthy target.
3. Query recent CPU, memory, request-rate, and HTTP 5xx-rate samples from
   Prometheus.
4. Score complete samples with scikit-learn Isolation Forest.
5. Persist newly flagged observations and link them to a resource-scoped incident.
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
create duplicate anomaly records. New anomalies for one resource reuse its OPEN
or ACKNOWLEDGED incident; different resources remain isolated, and RESOLVED
incidents are not reused. Each incident description includes observed features
and explicitly identifies the Isolation Forest score as a decision-function
score, not a probability.

Incident severity is classified independently from the Isolation Forest score.
The highest threshold crossed by any evidence sets severity:

| Severity | Process CPU (cores) | Process memory (bytes) | HTTP 5xx rate (requests/second) |
|---|---:|---:|---:|
| LOW | Below 0.5 | Below 536,870,912 | Below 0.1 |
| MEDIUM | 0.5 | 536,870,912 | 0.1 |
| HIGH | 1.0 | 1,073,741,824 | 1.0 |
| CRITICAL | 2.0 | 2,147,483,648 | 5.0 |

These are initial absolute thresholds for the currently collected process and
application metrics, not universal capacity limits. Configure them with
`ANOMALY_SEVERITY_{MEDIUM,HIGH,CRITICAL}_{CPU_CORES,MEMORY_BYTES,ERROR_RATE}`.
For example, `ANOMALY_SEVERITY_HIGH_CPU_CORES=1.5` changes the CPU HIGH
threshold. The HTTP 5xx signal is a request rate, not a percentage; total request
rate is retained as context and does not increase severity on its own. Thresholds
must be positive and strictly increase from MEDIUM through CRITICAL.

Detection persistence locks the resource row in the same database transaction
before checking timestamps or reusing an incident. This serializes concurrent
detection persistence for one resource on PostgreSQL's normal READ COMMITTED
isolation level. The project test suite uses SQLite, which does not enforce
`SELECT FOR UPDATE`; concurrent PostgreSQL behavior still requires integration
testing against PostgreSQL before being treated as verified.

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

The tests use an isolated in-memory SQLite database. The latest additive
Alembic migration is `20261102_0003`; do not rewrite earlier migration files or
apply this migration to a database without explicit approval.
