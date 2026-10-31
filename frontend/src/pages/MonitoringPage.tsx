import { Activity, ExternalLink, Plus, Server } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { getApiErrorMessage } from "../services/api";
import {
  createProject,
  listMonitoringResources,
  listProjects,
  registerMonitoringResource,
  type MonitoringResource,
  type ProjectRecord,
} from "../services/monitoring";

export default function MonitoringPage() {
  const [projects, setProjects] = useState<ProjectRecord[]>([]);
  const [resources, setResources] = useState<MonitoringResource[]>([]);
  const [projectName, setProjectName] = useState("");
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [prometheusJob, setPrometheusJob] = useState("aiops-backend");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function refresh() {
    const [nextProjects, nextResources] = await Promise.all([
      listProjects(),
      listMonitoringResources(),
    ]);
    setProjects(nextProjects);
    setResources(nextResources);
    setSelectedProjectId((current) =>
      nextProjects.some((project) => project.id === current)
        ? current
        : (nextProjects[0]?.id ?? ""),
    );
  }

  useEffect(() => {
    refresh()
      .catch((requestError: unknown) =>
        setError(getApiErrorMessage(requestError, "Monitoring data could not be loaded.")),
      )
      .finally(() => setLoading(false));
  }, []);

  async function handleCreateProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setSaving(true);
    try {
      const project = await createProject(projectName.trim());
      await refresh();
      setSelectedProjectId(project.id);
      setProjectName("");
      setNotice(`Project "${project.name}" created.`);
    } catch (requestError: unknown) {
      setError(getApiErrorMessage(requestError, "Project could not be created."));
    } finally {
      setSaving(false);
    }
  }

  async function handleRegisterResource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setNotice("");
    setSaving(true);
    try {
      const resource = await registerMonitoringResource(
        selectedProjectId,
        prometheusJob.trim(),
      );
      await refresh();
      setNotice(`Prometheus job "${resource.prometheus_job}" registered.`);
    } catch (requestError: unknown) {
      setError(getApiErrorMessage(requestError, "Prometheus resource could not be registered."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-medium uppercase tracking-[0.12em] text-brand">Local telemetry</p>
        <h2 className="mt-1.5 text-2xl font-semibold tracking-tight text-ink">Infrastructure monitoring</h2>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-500">
          Associate a healthy Prometheus scrape job with a local project before running
          anomaly detection. The current Compose job measures backend process and HTTP
          metrics, not Windows host or container resources.
        </p>
      </section>

      {error && <div role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
      {notice && <div role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div>}

      {loading ? (
        <div className="panel flex h-36 items-center justify-center text-sm text-slate-500">Loading monitoring data...</div>
      ) : (
        <>
          <section className="grid gap-4 xl:grid-cols-2">
            <form onSubmit={handleCreateProject} className="panel space-y-4 p-5">
              <div className="flex items-center gap-2">
                <Plus size={17} className="text-brand" />
                <h3 className="text-sm font-semibold text-ink">Create local project</h3>
              </div>
              <label className="block text-xs font-medium text-slate-600" htmlFor="project-name">
                Project name
              </label>
              <input
                id="project-name"
                required
                maxLength={160}
                value={projectName}
                onChange={(event) => setProjectName(event.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-brand"
                placeholder="Local AIOps project"
              />
              <button
                type="submit"
                disabled={saving || !projectName.trim()}
                className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Create project
              </button>
            </form>

            <form onSubmit={handleRegisterResource} className="panel space-y-4 p-5">
              <div className="flex items-center gap-2">
                <Activity size={17} className="text-brand" />
                <h3 className="text-sm font-semibold text-ink">Register Prometheus job</h3>
              </div>
              <label className="block text-xs font-medium text-slate-600" htmlFor="project-select">
                Project
              </label>
              <select
                id="project-select"
                required
                value={selectedProjectId}
                onChange={(event) => setSelectedProjectId(event.target.value)}
                disabled={projects.length === 0}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand disabled:bg-slate-50"
              >
                {projects.length === 0 ? (
                  <option value="">Create a project first</option>
                ) : (
                  projects.map((project) => (
                    <option key={project.id} value={project.id}>{project.name}</option>
                  ))
                )}
              </select>
              <label className="block text-xs font-medium text-slate-600" htmlFor="prometheus-job">
                Prometheus job name
              </label>
              <input
                id="prometheus-job"
                required
                maxLength={120}
                pattern="[A-Za-z0-9_.:-]+"
                value={prometheusJob}
                onChange={(event) => setPrometheusJob(event.target.value)}
                className="w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-brand"
              />
              <button
                type="submit"
                disabled={saving || !selectedProjectId || !prometheusJob.trim()}
                className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Verify and register
              </button>
            </form>
          </section>

          <section className="panel p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-ink">Registered resources</h3>
                <p className="mt-1 text-xs text-slate-400">Only resources belonging to your projects are listed.</p>
              </div>
              <a
                href="http://localhost:9090/targets"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-medium text-brand hover:text-blue-700"
              >
                Prometheus targets <ExternalLink size={13} />
              </a>
            </div>
            {resources.length === 0 ? (
              <p className="py-10 text-center text-xs text-slate-400">No Prometheus jobs registered yet.</p>
            ) : (
              <div className="mt-4 divide-y divide-slate-100">
                {resources.map((resource) => (
                  <div key={resource.id} className="flex items-center gap-3 py-3">
                    <span className="rounded-lg bg-blue-50 p-2 text-blue-600"><Server size={15} /></span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-slate-700">{resource.resource_name}</p>
                      <p className="mt-0.5 text-xs text-slate-400">Prometheus job · {resource.environment}</p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs capitalize text-slate-600">{resource.status}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
