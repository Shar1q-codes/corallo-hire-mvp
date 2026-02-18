import { Navigate, Route, Routes } from "react-router-dom";

import { RequireAuth } from "./components/RequireAuth";
import { AppLayout } from "./components/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { WorkspacesPage } from "./pages/WorkspacesPage";
import { WorkspaceDetailPage } from "./pages/WorkspaceDetailPage";
import { JobDetailPage } from "./pages/JobDetailPage";
import { EvaluationPage } from "./pages/EvaluationPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/workspaces" replace />} />
          <Route path="/workspaces" element={<WorkspacesPage />} />
          <Route path="/workspaces/:id" element={<WorkspaceDetailPage />} />
          <Route path="/jobs/:jobId" element={<JobDetailPage />} />
          <Route path="/evaluations/:evaluationId" element={<EvaluationPage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
