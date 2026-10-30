import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Boxes,
  CheckCircle2,
  Clock3,
  Rocket,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { DemoMetricChart } from "../components/dashboard/DemoMetricChart";
import { HealthOverview } from "../components/dashboard/HealthOverview";
import { MetricCard } from "../components/dashboard/MetricCard";
import { getApiErrorMessage } from "../services/api";
import { getDashboardOverview, getRecentDeployments, getRecentIncidents } from "../services/dashboard";
import type { DashboardOverview, DeploymentRecord, IncidentRecord } from "../types/api";

export default function Dashboard() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [incidents, setIncidents] = useState<IncidentRecord[]>([]);
  const [deployments, setDeployments] = useState<DeploymentRecord[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getDashboardOverview(), getRecentIncidents(), getRecentDeployments()])
      .then(([dashboard, recentIncidents, recentDeployments]) => {
        setOverview(dashboard);
        setIncidents(recentIncidents.slice(0, 5));
        setDeployments(recentDeployments.slice(0, 5));
      })
      .catch((requestError: unknown) =>
        setError(getApiErrorMessage(requestError, "Dashboard data could not be loaded.")),
      );
  }, []);

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.12em] text-brand">Operations overview</p>
          <h2 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink">Good to see you</h2>
          <p className="mt-1 text-sm text-slate-500">A clear view of your demo environment and platform status.</p>
        </div>
        <div className="inline-flex w-fit items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">
          <span className="h-2 w-2 rounded-full bg-amber-500" />
          Monitoring not connected
        </div>
      </section>

      {error && <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

      {!overview && !error ? (
        <div className="panel flex h-36 items-center justify-center text-sm text-slate-500">Loading dashboard data...</div>
      ) : overview ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Monitored resources" value={overview.total_monitored_resources} detail="Registered in the application database" icon={Boxes} accent="blue" />
            <MetricCard label="Healthy resources" value={overview.healthy_resources} detail="Status recorded in the database" icon={CheckCircle2} accent="green" />
            <MetricCard label="Active incidents" value={overview.open_incidents} detail="Open or acknowledged incidents" icon={AlertTriangle} accent="amber" />
            <MetricCard label="Recent deployments" value={overview.recent_deployments} detail="Database records from the last 7 days" icon={Rocket} accent="red" />
          </section>

          <section className="grid gap-4 xl:grid-cols-2">
            <DemoMetricChart metric="cpu" />
            <DemoMetricChart metric="memory" />
          </section>

          <section className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <HealthOverview
              healthy={overview.healthy_resources}
              warning={overview.warning_resources}
              critical={overview.critical_resources}
              unknown={Math.max(
                0,
                overview.total_monitored_resources -
                  overview.healthy_resources -
                  overview.warning_resources -
                  overview.critical_resources,
              )}
            />
            <div className="panel p-5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-ink">Recent activity</h3>
                  <p className="mt-1 text-xs text-slate-400">Latest recorded platform events</p>
                </div>
                <Clock3 size={17} className="text-slate-400" />
              </div>
              {overview.recent_activity.length === 0 ? (
                <EmptyList message="No platform activity recorded yet." />
              ) : (
                <div className="mt-4 divide-y divide-slate-100">
                  {overview.recent_activity.map((activity, index) => (
                    <div key={`${activity.action}-${activity.created_at}-${index}`} className="flex items-center gap-3 py-3 first:pt-1">
                      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600"><Activity size={15} /></span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-xs font-medium capitalize text-slate-700">{activity.action.replaceAll("_", " ")}</p>
                        <p className="mt-0.5 text-[10px] capitalize text-slate-400">{activity.resource_type}</p>
                      </div>
                      <time className="whitespace-nowrap text-[10px] text-slate-400">{new Date(activity.created_at).toLocaleString()}</time>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-2">
            <RecentIncidents incidents={incidents} />
            <RecentDeployments deployments={deployments} />
          </section>
          <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500">
            <span className="rounded bg-slate-100 p-1 text-slate-500"><ArrowUpRight size={13} /></span>
            Summary cards reflect database records. Trend charts are illustrative demo data and are not live infrastructure measurements.
          </div>
        </>
      ) : null}
    </div>
  );
}

function EmptyList({ message }: { message: string }) {
  return <p className="py-12 text-center text-xs text-slate-400">{message}</p>;
}

function RecentIncidents({ incidents }: { incidents: IncidentRecord[] }) {
  return (
    <section className="panel p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-ink">Recent incidents</h3>
        <Link to="/incidents" className="text-[11px] font-medium text-brand hover:text-blue-700">View all</Link>
      </div>
      {incidents.length === 0 ? (
        <p className="flex min-h-[115px] items-center justify-center text-center text-xs text-slate-400">No incident records in the database.</p>
      ) : (
        <div className="mt-3 divide-y divide-slate-100">
          {incidents.map((incident) => (
            <div key={incident.id} className="flex items-center gap-3 py-3">
              <span className={`h-2 w-2 shrink-0 rounded-full ${incident.severity === "critical" || incident.severity === "high" ? "bg-rose-500" : incident.severity === "medium" ? "bg-amber-500" : "bg-blue-400"}`} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-slate-700">{incident.title}</p>
                <p className="mt-0.5 text-[10px] capitalize text-slate-400">{incident.severity} · {incident.status}</p>
              </div>
              <time className="whitespace-nowrap text-[10px] text-slate-400">{new Date(incident.detected_at).toLocaleDateString()}</time>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function RecentDeployments({ deployments }: { deployments: DeploymentRecord[] }) {
  return (
    <section className="panel p-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-ink">Recent deployments</h3>
        <Link to="/deployments" className="text-[11px] font-medium text-brand hover:text-blue-700">View all</Link>
      </div>
      {deployments.length === 0 ? (
        <p className="flex min-h-[115px] items-center justify-center text-center text-xs text-slate-400">No deployment records in the database.</p>
      ) : (
        <div className="mt-3 divide-y divide-slate-100">
          {deployments.map((deployment) => (
            <div key={deployment.id} className="flex items-center gap-3 py-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600"><Rocket size={15} /></span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium text-slate-700">Version {deployment.version}</p>
                <p className="mt-0.5 text-[10px] capitalize text-slate-400">{deployment.environment} · {deployment.status}</p>
              </div>
              <time className="whitespace-nowrap text-[10px] text-slate-400">{new Date(deployment.created_at).toLocaleDateString()}</time>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
