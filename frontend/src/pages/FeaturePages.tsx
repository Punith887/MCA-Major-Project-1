import { PagePlaceholder } from "../components/common/PagePlaceholder";

const descriptions: Record<string, string> = {
  Monitoring: "Resource inventory and Prometheus metric collection will be added in a later phase. No live telemetry is connected.",
  Logs: "Log ingestion, search, and incident correlation are planned for a later phase.",
  "Anomaly Detection": "Machine-learning anomaly detection is not implemented in Phase 1.",
  "Predictive Analytics": "Risk prediction and historical model evaluation are planned for a later phase.",
  Incidents: "Incident records are database-backed, but incident ingestion and management workflows are not implemented yet.",
  "AI Insights": "Generative AI analysis is not connected. No AI-generated incident findings are shown here.",
  "Knowledge Base": "Document ingestion, retrieval, and RAG answers are planned for a later phase.",
  "Autonomous Operations": "No infrastructure actions are available in Phase 1. Future actions will require allowlists and approval.",
  Deployments: "Deployment records are database-backed, but deployment integrations are not connected.",
  "Audit Logs": "Audit events are recorded for supported account activity. Searchable audit views are planned for a later phase.",
  Settings: "Account and platform administration workflows are planned for a later phase.",
};

export function FeaturePage({ title }: { title: string }) {
  return <PagePlaceholder title={title} description={descriptions[title] ?? "This section is not connected yet."} />;
}
