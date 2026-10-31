# AI engine

`anomaly_detector.py` uses scikit-learn Isolation Forest to score aligned Prometheus
observations. Its anomaly score is the negated decision function, not a probability,
and it only detects unusual observations; it does not predict future failures.

The backend fetches real samples from the configured Prometheus service and persists
new anomaly results and linked incidents. Tests use synthetic observations only as
test fixtures and do not claim production accuracy.

Predictive risk models, GenAI provider adapters, RAG, and policy-controlled agents
remain future increments. Keep integrations behind backend services and validate
their inputs and outputs.
