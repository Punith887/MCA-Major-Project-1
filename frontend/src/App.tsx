import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";
import { AppLayout } from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import { FeaturePage } from "./pages/FeaturePages";
import Login from "./pages/Login";
import Register from "./pages/Register";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="monitoring" element={<FeaturePage title="Monitoring" />} />
          <Route path="logs" element={<FeaturePage title="Logs" />} />
          <Route path="anomalies" element={<FeaturePage title="Anomaly Detection" />} />
          <Route path="predictions" element={<FeaturePage title="Predictive Analytics" />} />
          <Route path="incidents" element={<FeaturePage title="Incidents" />} />
          <Route path="ai-insights" element={<FeaturePage title="AI Insights" />} />
          <Route path="knowledge" element={<FeaturePage title="Knowledge Base" />} />
          <Route path="operations" element={<FeaturePage title="Autonomous Operations" />} />
          <Route path="deployments" element={<FeaturePage title="Deployments" />} />
          <Route path="audit" element={<FeaturePage title="Audit Logs" />} />
          <Route path="settings" element={<FeaturePage title="Settings" />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
