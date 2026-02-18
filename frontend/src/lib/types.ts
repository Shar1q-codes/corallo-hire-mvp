export type UUID = string;

export type Workspace = {
  id: UUID;
  tenant_id: UUID;
  name: string;
  created_at: string;
  created_by: UUID;
};

export type Job = {
  id: UUID;
  tenant_id: UUID;
  workspace_id: UUID;
  title: string;
  description: string;
  recruiter_notes: string | null;
  created_at: string;
  created_by: UUID;
};

export type Resume = {
  id: UUID;
  tenant_id: UUID;
  workspace_id: UUID;
  file_object_path: string;
  original_filename: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  extracted_text: string | null;
  created_at: string;
  created_by: UUID;
};

export type ResumeUploadOut = {
  resume_id: UUID;
  file_object_path: string;
};

export type Evaluation = {
  id: UUID;
  tenant_id: UUID;
  workspace_id: UUID;
  job_id: UUID;
  resume_id: UUID;
  status: "created" | "completed" | "failed";
  failure_reason_code: string | null;
  idempotency_key: string | null;
  created_at: string;
  created_by: UUID;
};

export type EvaluationRunResponse = {
  evaluation_id: UUID;
  status: "created" | "completed" | "failed";
  failure_reason_code?: string | null;
};

export type ArtifactStatus = {
  available: Record<string, boolean>;
  viewed: Record<string, string | null>;
  gates: {
    risk_signals_unlocked: boolean;
    interview_guidance_unlocked: boolean;
  };
};

export type ArtifactDetail = {
  artifact_type: "intent_hypotheses" | "risk_signals" | "interview_guidance";
  evaluation_id: UUID;
  content_json: Record<string, unknown>;
  created_at: string;
};

export type Ack = {
  id: UUID;
  tenant_id: UUID;
  workspace_id: UUID;
  job_id: UUID;
  resume_id: UUID;
  evaluation_id: UUID;
  acknowledgement_type: "counter_signal_ack" | "validation_gap_declaration" | "override_or_disagreement";
  subject_ref_type: "intent_item" | "risk_item" | "assumption_item" | "interview_focus_area" | "general";
  subject_ref_id: string | null;
  content_text: string;
  decision_mode: "validate_in_interview" | "skip_validation" | "disagree" | "accept_with_context";
  created_at: string;
  created_by: UUID;
};

export type ProblemDetail = {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: Array<Record<string, unknown>>;
};
