import { api } from "./api";

export interface ProjectRecord {
  id: string;
  name: string;
  description: string | null;
  environment: string;
  owner_id: string;
  created_at: string;
}

export interface MonitoringResource {
  id: string;
  project_id: string;
  resource_name: string;
  resource_type: string;
  prometheus_job: string | null;
  environment: string;
  status: "unknown" | "healthy" | "warning" | "critical";
  created_at: string;
}

export interface AnomalyRecord {
  id: string;
  resource_id: string;
  resource: string;
  incident_id: string | null;
  detected_at: string;
  anomaly_score: number;
  detected_features: Record<string, number>;
  severity: string;
  status: string;
  created_at: string;
}

export interface DetectionResult {
  resource_id: string;
  prometheus_job: string;
  sample_count: number;
  lookback_minutes: number;
  anomaly_count: number;
  incidents_created: number;
  anomalies: AnomalyRecord[];
}

export async function listProjects(): Promise<ProjectRecord[]> {
  const response = await api.get<ProjectRecord[]>("/projects");
  return response.data;
}

export async function createProject(name: string): Promise<ProjectRecord> {
  const response = await api.post<ProjectRecord>("/projects", { name });
  return response.data;
}

export async function listMonitoringResources(): Promise<MonitoringResource[]> {
  const response = await api.get<MonitoringResource[]>("/monitoring/resources");
  return response.data;
}

export async function registerMonitoringResource(
  projectId: string,
  prometheusJob: string,
): Promise<MonitoringResource> {
  const response = await api.post<MonitoringResource>("/monitoring/resources", {
    project_id: projectId,
    prometheus_job: prometheusJob,
  });
  return response.data;
}

export async function listAnomalies(): Promise<AnomalyRecord[]> {
  const response = await api.get<AnomalyRecord[]>("/anomalies");
  return response.data;
}

export async function detectResourceAnomalies(
  resourceId: string,
): Promise<DetectionResult> {
  const response = await api.post<DetectionResult>("/anomalies/detect", {
    resource_id: resourceId,
  });
  return response.data;
}
