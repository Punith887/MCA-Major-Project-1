import { AlertTriangle } from "lucide-react";
import { useEffect, useState } from "react";
import { getApiErrorMessage } from "../services/api";
import { getRecentIncidents } from "../services/dashboard";
import type { IncidentRecord } from "../types/api";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getRecentIncidents()
      .then(setIncidents)
      .catch((requestError: unknown) =>
        setError(getApiErrorMessage(requestError, "Incident history could not be loaded.")),
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-brand">Detection outcomes</p>
        <h2 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink">Incidents</h2>
        <p className="mt-1 text-sm text-slate-500">Incidents created from anomaly observations in your local projects.</p>
      </section>
      {error && <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
      <section className="panel p-5">
        {loading ? (
          <p className="py-10 text-center text-xs text-slate-400">Loading incidents...</p>
        ) : incidents.length === 0 ? (
          <p className="py-10 text-center text-xs text-slate-400">No incident records are available.</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {incidents.map((incident) => (
              <article key={incident.id} className="flex items-start gap-3 py-4">
                <span className="rounded-lg bg-amber-50 p-2 text-amber-700"><AlertTriangle size={15} /></span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-700">{incident.title}</p>
                  <p className="mt-1 text-xs capitalize text-slate-500">
                    {incident.severity} · {incident.status} · {new Date(incident.detected_at).toLocaleString()}
                  </p>
                  {incident.description && (
                    <p className="mt-2 whitespace-pre-wrap break-words text-xs leading-5 text-slate-500">{incident.description}</p>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
