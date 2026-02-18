import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth/AuthProvider";

export function RequireAuth() {
  const { session, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="page">Loading session...</div>;
  }

  if (!session) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
