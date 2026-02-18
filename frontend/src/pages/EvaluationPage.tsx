import { useEffect, useMemo, useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";

import { api } from "../lib/api";
import { formatProblem } from "../lib/errors";
import { gateLabel, isArtifactUnlocked } from "../lib/gates";
import type { Ack, ArtifactDetail, ArtifactStatus, Evaluation, Job, Resume, Workspace } from "../lib/types";

type ArtifactType = "intent_hypotheses" | "risk_signals" | "interview_guidance";

const labels: Record<ArtifactType, string> = {
  intent_hypotheses: "Intent Hypotheses",
  risk_signals: "Risk Signals",
  interview_guidance: "Interview Validation Guidance"
};

function JsonSection({ value }: { value: unknown }) {
  if (Array.isArray(value)) {
    return (
      <ul className="list">
        {value.map((item, idx) => (
          <li key={idx}>
            <JsonSection value={item} />
          </li>
        ))}
      </ul>
    );
  }
  if (value && typeof value === "object") {
    return (
      <div className="stack-sm">
        {Object.entries(value).map(([key, nested]) => (
          <div key={key}>
            <strong>{key}</strong>
            <JsonSection value={nested} />
          </div>
        ))}
      </div>
    );
  }
  return <span>{String(value)}</span>;
}

export function EvaluationPage() {
  const { evaluationId = "" } = useParams();
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [resume, setResume] = useState<Resume | null>(null);
  const [status, setStatus] = useState<ArtifactStatus | null>(null);
  const [selected, setSelected] = useState<ArtifactType>("intent_hypotheses");
  const [artifact, setArtifact] = useState<ArtifactDetail | null>(null);
  const [acks, setAcks] = useState<Ack[]>([]);
  const [ackType, setAckType] = useState<Ack["acknowledgement_type"]>("counter_signal_ack");
  const [subjectType, setSubjectType] = useState<Ack["subject_ref_type"]>("general");
  const [subjectRefId, setSubjectRefId] = useState("");
  const [decisionMode, setDecisionMode] = useState<Ack["decision_mode"]>("validate_in_interview");
  const [contentText, setContentText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const artifactTypes: ArtifactType[] = ["intent_hypotheses", "risk_signals", "interview_guidance"];

  async function loadContext() {
    setError(null);
    try {
      const evalRow = await api.getEvaluation(evaluationId);
      setEvaluation(evalRow);
      const [w, j, r] = await Promise.all([
        api.getWorkspace(evalRow.workspace_id),
        api.getJob(evalRow.job_id),
        api.getResume(evalRow.resume_id)
      ]);
      setWorkspace(w);
      setJob(j);
      setResume(r);
      const [s, a] = await Promise.all([api.getArtifactsStatus(evaluationId), api.listAcknowledgements(evaluationId)]);
      setStatus(s);
      setAcks(a);
    } catch (err) {
      setError(formatProblem(err));
    }
  }

  useEffect(() => {
    void loadContext();
  }, [evaluationId]);

  const viewed = useMemo(() => status?.viewed ?? {}, [status]);

  async function openArtifact(type: ArtifactType) {
    setError(null);
    try {
      await api.markArtifactViewed(evaluationId, type);
      const [detail, refreshed] = await Promise.all([
        api.getArtifactByType(evaluationId, type),
        api.getArtifactsStatus(evaluationId)
      ]);
      setSelected(type);
      setArtifact(detail);
      setStatus(refreshed);
    } catch (err) {
      setError(formatProblem(err));
    }
  }

  async function submitAck(e: FormEvent) {
    e.preventDefault();
    if (contentText.trim().length < 30) {
      setError("Acknowledgement content must be at least 30 characters.");
      return;
    }

    try {
      await api.createAcknowledgement(evaluationId, {
        acknowledgement_type: ackType,
        subject_ref_type: subjectType,
        subject_ref_id: subjectRefId.trim() ? subjectRefId.trim() : null,
        decision_mode: decisionMode,
        content_text: contentText.trim()
      });
      setContentText("");
      setSubjectRefId("");
      setAcks(await api.listAcknowledgements(evaluationId));
    } catch (err) {
      setError(formatProblem(err));
    }
  }

  return (
    <section className="stack">
      <h1>Evaluation</h1>
      <div className="panel">
        <p>
          <strong>Workspace:</strong> {workspace?.name ?? "-"}
        </p>
        <p>
          <strong>Job:</strong> {job?.title ?? "-"}
        </p>
        <p>
          <strong>Resume:</strong> {resume?.original_filename ?? resume?.id ?? "-"}
        </p>
        <p>
          <strong>Status:</strong> {evaluation?.status ?? "-"}
        </p>
      </div>

      <section className="panel stack">
        <h2>Artifacts</h2>
        <div className="row wrap">
          {artifactTypes.map((type) => {
            const unlocked = isArtifactUnlocked(type, viewed);
            return (
              <button key={type} type="button" disabled={!unlocked} onClick={() => void openArtifact(type)}>
                {labels[type]}
              </button>
            );
          })}
        </div>

        <div className="stack-sm">
          {artifactTypes.map((type) => {
            const unlocked = isArtifactUnlocked(type, viewed);
            return (
              <p key={type} className={unlocked ? "ok" : "muted"}>
                {labels[type]}: {unlocked ? "Unlocked" : `Locked. ${gateLabel(type)}`}
              </p>
            );
          })}
        </div>

        <h3>{labels[selected]}</h3>
        {artifact ? <JsonSection value={artifact.content_json} /> : <p className="muted">Select a viewed artifact to display.</p>}
      </section>

      <section className="panel stack">
        <h2>Acknowledgements (Human Notes)</h2>
        <form className="stack" onSubmit={submitAck}>
          <label>
            acknowledgement_type
            <select value={ackType} onChange={(e) => setAckType(e.target.value as Ack["acknowledgement_type"])}>
              <option value="counter_signal_ack">counter_signal_ack</option>
              <option value="validation_gap_declaration">validation_gap_declaration</option>
              <option value="override_or_disagreement">override_or_disagreement</option>
            </select>
          </label>

          <label>
            subject_ref_type
            <select value={subjectType} onChange={(e) => setSubjectType(e.target.value as Ack["subject_ref_type"])}>
              <option value="general">general</option>
              <option value="intent_item">intent_item</option>
              <option value="risk_item">risk_item</option>
              <option value="assumption_item">assumption_item</option>
              <option value="interview_focus_area">interview_focus_area</option>
            </select>
          </label>

          <label>
            subject_ref_id (optional)
            <input value={subjectRefId} onChange={(e) => setSubjectRefId(e.target.value)} />
          </label>

          <label>
            decision_mode
            <select value={decisionMode} onChange={(e) => setDecisionMode(e.target.value as Ack["decision_mode"])}>
              <option value="validate_in_interview">validate_in_interview</option>
              <option value="skip_validation">skip_validation</option>
              <option value="disagree">disagree</option>
              <option value="accept_with_context">accept_with_context</option>
            </select>
          </label>

          <label>
            content_text
            <textarea
              value={contentText}
              onChange={(e) => setContentText(e.target.value)}
              rows={5}
              minLength={30}
              maxLength={2000}
              required
            />
          </label>
          <button type="submit">Create Acknowledgement</button>
        </form>

        <ul className="list">
          {acks.map((ack) => (
            <li key={ack.id}>
              <p>
                <strong>{ack.acknowledgement_type}</strong> | {ack.subject_ref_type} | {ack.decision_mode}
              </p>
              <p>{ack.content_text}</p>
            </li>
          ))}
        </ul>
      </section>

      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
