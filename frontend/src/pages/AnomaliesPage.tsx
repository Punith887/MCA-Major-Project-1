import { Activity, AlertTriangle, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { getApiErrorMessage } from "../services/api";
import {
  detectResourceAnomalies,
  listAnomalies,
  listMonitoringResources,
  type AnomalyRecord,
  type DetectionResult,
  type MonitoringResource,
} from "../services/monitoring";

export default function AnomaliesPage() {
  const [resources, setResources] = useState<MonitoringResource[]>([]);
  const [anomalies, setAnomalies] = useState<AnomalyRecord[]>([]);
  const [selectedResourceId, setSelectedResourceId] = useState("");
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    const [nextResources, nextAnomalies] = await Promise.all([
      listMonitoringResources(),
      listAnomalies(),
    ]);
    setResources(nextResources);
    setAnomalies(nextAnomalies);
    setSelectedResourceId((current) =>
      nextResources.some((resource) => resource.id === current)
        ? current
        : (nextResources[0]?.id ?? ""),
    );
  }

  useEffect(() => {
    refresh()
      .catch((requestError: unknown) =>
        setError(getApiErrorMessage(requestError, "Anomaly data could not be loaded.")),
      )
      .finally(() => setLoading(false));
  }, []);

  async function runDetection() {
    setError("");
    setResult(null);
    setDetecting(true);
    try {
      const detection = await detectResourceAnomalies(selectedResourceId);
      setResult(detection);
      await refresh();
    } catch (requestError: unknown) {
      setError(getApiErrorMessage(requestError, "Anomaly detection could not be completed."));
    } finally {
      setDetecting(false);
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-brand">Observed metrics</p>
        <h2 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink">Anomaly detection</h2>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
          Isolation Forest scores collected Prometheus observations. An anomaly score
          is not a probability and this detector does not predict future failures.
        </p>
      </section>

      {error && <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

      <section className="panel flex flex-col gap-3 p-5 sm:flex-row sm:items-end">
        <div className="min-w-0 flex-1">
          <label className="mb-1.5 block text-xs font-medium text-slate-600" htmlFor="detection-resource">
            Registered Prometheus resource
          </label>
          <select
            id="detection-resource"
            value={selectedResourceId}
            onChange={(event) => setSelectedResourceId(event.target.value)}
            disabled={loading || resources.length === 0}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand disabled:bg-slate-50"
          >
            {resources.length === 0 ? (
              <option value="">Register a resource in Infrastructure Monitoring first</option>
            ) : (
              resources.map((resource) => (
                <option key={resource.id} value={resource.id}>
                  {resource.resource_name} · {resource.environment}
                </option>
              ))
            )}
          </select>
        </div>
        <button
          type="button"
          onClick={runDetection}
          disabled={loading || detecting || !selectedResourceId}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw size={15} className={detecting ? "animate-spin" : ""} />
          {detecting ? "Analysing metrics..." : "Run detection"}
        </button>
      </section>

      {result && (
        <section role="status" className="panel space-y-3 p-5">
          <h3 className="text-sm font-semibold text-ink">Detection run completed</h3>
          <p className="text-sm text-slate-600">
            Read {result.sample_count} samples over {result.lookback_minutes} minutes from
            {" "}{result.prometheus_job}. Found {result.anomaly_count} newly detected
            {" "}anomalies and created {result.incidents_created} linked incidents.
          </p>
          {result.anomalies.length === 0 && (
            <p className="text-xs text-slate-500">No new anomalies were persisted for this run.</p>
          )}
        </section>
      )}

      <section className="panel p-5">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-brand" />
          <h3 className="text-sm font-semibold text-ink">Persisted anomaly observations</h3>
        </div>
        {loading ? (
          <p className="py-10 text-center text-xs text-slate-400">Loading anomaly history...</p>
        ) : anomalies.length === 0 ? (
          <p className="py-10 text-center text-xs text-slate-400">No anomaly observations are recorded.</p>
        ) : (
          <div className="mt-4 divide-y divide-slate-100">
            {anomalies.map((anomaly) => (
              <article key={anomaly.id} className="flex flex-col gap-2 py-4 sm:flex-row sm:items-start">
                <span className="mt-0.5 rounded-lg bg-amber-50 p-2 text-amber-700"><AlertTriangle size={15} /></span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-700">{anomaly.resource}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {new Date(anomaly.detected_at).toLocaleString()} · {anomaly.status}
                    {anomaly.incident_id ? ` · Incident ${anomaly.incident_id}` : ""}
                  </p>
                  <p className="mt-1 break-words text-xs text-slate-500">
                    Observed features: {Object.entries(anomaly.detected_features)
                      .map(([name, value]) => `${name}=${value}`)
                      .join(", ")}
                  </p>
                </div>
                <span className="whitespace-nowrap rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-800">
                  Score {anomaly.anomaly_score.toFixed(5)} (not probability)
                </span>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
