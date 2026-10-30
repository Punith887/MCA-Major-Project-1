export type UserRole = "admin" | "devops_engineer" | "viewer";

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  user: User;
}

export interface ActivityItem {
  action: string;
  resource_type: string;
  created_at: string;
}

export interface DashboardOverview {
  data_source: "database";
  monitoring_connected: boolean;
  total_monitored_resources: number;
  healthy_resources: number;
  warning_resources: number;
  critical_resources: number;
  open_incidents: number;
  recent_deployments: number;
  recent_activity: ActivityItem[];
}

export interface IncidentRecord {
  id: string;
  title: string;
  severity: "low" | "medium" | "high" | "critical";
  status: "open" | "acknowledged" | "resolved";
  detected_at: string;
}

export interface DeploymentRecord {
  id: string;
  version: string;
  environment: string;
  status: string;
  created_at: string;
}

export interface ApiError {
  detail?: string;
}
