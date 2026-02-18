import { ApiError } from "./errors";
import type {
  Ack,
  ArtifactDetail,
  ArtifactStatus,
  Evaluation,
  EvaluationRunResponse,
  Job,
  ProblemDetail,
  Resume,
  ResumeUploadOut,
  Workspace
} from "./types";

const apiBase = import.meta.env.VITE_API_BASE_URL;

if (!apiBase) {
  throw new Error("Missing VITE_API_BASE_URL");
}

type TokenProvider = () => Promise<string | null>;
type UnauthorizedHandler = () => void;

let tokenProvider: TokenProvider | null = null;
let unauthorizedHandler: UnauthorizedHandler | null = null;

export function configureApiAuth(provider: TokenProvider, onUnauthorized: UnauthorizedHandler): void {
  tokenProvider = provider;
  unauthorizedHandler = onUnauthorized;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  headers.set("Accept", "application/json");

  const token = tokenProvider ? await tokenProvider() : null;
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${apiBase}${path}`, {
    ...init,
    headers
  });

  if (res.status === 401) {
    unauthorizedHandler?.();
  }

  if (!res.ok) {
    let problem: ProblemDetail | undefined;
    try {
      problem = (await res.json()) as ProblemDetail;
    } catch {
      problem = undefined;
    }
    throw new ApiError(problem?.detail ?? `HTTP ${res.status}`, res.status, problem);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export const api = {
  listWorkspaces: () => request<Workspace[]>("/workspaces"),
  createWorkspace: (name: string) =>
    request<Workspace>("/workspaces", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name })
    }),
  getWorkspace: (workspaceId: string) => request<Workspace>(`/workspaces/${workspaceId}`),

  listJobsByWorkspace: (workspaceId: string) => request<Job[]>(`/workspaces/${workspaceId}/jobs`),
  createJob: (workspaceId: string, payload: Pick<Job, "title" | "description" | "recruiter_notes">) =>
    request<Job>(`/workspaces/${workspaceId}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),
  getJob: (jobId: string) => request<Job>(`/jobs/${jobId}`),
  updateJob: (
    jobId: string,
    payload: Partial<Pick<Job, "title" | "description" | "recruiter_notes">>
  ) =>
    request<Job>(`/jobs/${jobId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }),

  listResumesByWorkspace: (workspaceId: string) => request<Resume[]>(`/workspaces/${workspaceId}/resumes`),
  uploadResume: async (workspaceId: string, file: File): Promise<ResumeUploadOut> => {
    const form = new FormData();
    form.append("file", file);
    return request<ResumeUploadOut>(`/workspaces/${workspaceId}/resumes`, {
      method: "POST",
      body: form
    });
  },
  getResume: (resumeId: string) => request<Resume>(`/resumes/${resumeId}`),

  createEvaluation: (jobId: string, resumeId: string, idempotency_key: string | null = null) =>
    request<Evaluation>(`/jobs/${jobId}/resumes/${resumeId}/evaluations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idempotency_key })
    }),
  getEvaluation: (evaluationId: string) => request<Evaluation>(`/evaluations/${evaluationId}`),
  runEvaluation: (evaluationId: string) =>
    request<EvaluationRunResponse>(`/evaluations/${evaluationId}/run`, {
      method: "POST"
    }),

  getArtifactsStatus: (evaluationId: string) => request<ArtifactStatus>(`/evaluations/${evaluationId}/artifacts/status`),
  markArtifactViewed: (evaluationId: string, artifactType: string) =>
    request<{ ok: boolean; artifact_type: string; viewed_at: string }>(
      `/evaluations/${evaluationId}/artifacts/${artifactType}/viewed`,
      { method: "POST" }
    ),
  getArtifactByType: (evaluationId: string, artifactType: string) =>
    request<ArtifactDetail>(`/evaluations/${evaluationId}/artifacts/${artifactType}`),

  listAcknowledgements: (evaluationId: string) => request<Ack[]>(`/evaluations/${evaluationId}/acknowledgements`),
  createAcknowledgement: (
    evaluationId: string,
    payload: {
      acknowledgement_type: Ack["acknowledgement_type"];
      subject_ref_type: Ack["subject_ref_type"];
      subject_ref_id?: string | null;
      decision_mode: Ack["decision_mode"];
      content_text: string;
    }
  ) =>
    request<{ acknowledgement_id: string }>(`/evaluations/${evaluationId}/acknowledgements`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
};
