import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { LoadingScreen } from "../common/LoadingScreen";

export function ProtectedRoute() {
  const { user, isLoading } = useAuth();
  if (isLoading) return <LoadingScreen />;
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}
