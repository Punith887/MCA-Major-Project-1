import type {
  DashboardOverview,
  DeploymentRecord,
  HostMetricsResponse,
  IncidentRecord,
} from "../types/api";
import { api } from "./api";

export async function getDashboardOverview(): Promise<DashboardOverview> {
  const response = await api.get<DashboardOverview>("/dashboard/overview");
  return response.data;
}

export async function getWindowsHostMetrics(
  signal?: AbortSignal,
): Promise<HostMetricsResponse> {
  const response = await api.get<HostMetricsResponse>("/monitoring/host-metrics", {
    params: { lookback_minutes: 60, step_seconds: 15 },
    signal,
  });
  return response.data;
}

export async function getRecentIncidents(): Promise<IncidentRecord[]> {
  const response = await api.get<IncidentRecord[]>("/incidents");
  return response.data;
}

export async function getRecentDeployments(): Promise<DeploymentRecord[]> {
  const response = await api.get<DeploymentRecord[]>("/deployments");
  return response.data;
}
