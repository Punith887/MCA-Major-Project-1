# Phase 1 scope and implementation notes

Phase 1 establishes the application, authentication, PostgreSQL schema, migrations,
API, and dashboard. Prometheus, Grafana, log ingestion, ML, RAG, Generative AI,
Kubernetes actions, and cloud deployment are not connected in this phase.

The registration endpoint assigns the least-privileged `viewer` role. An administrator
can be created intentionally through the local interactive CLI after database
migrations have run. Registration requests cannot assign their own role.

Dashboard summary counts come from application database records. Until a monitoring
integration exists, the CPU and memory charts use fixed illustrative data and are
explicitly labelled `DEMO DATA`.
