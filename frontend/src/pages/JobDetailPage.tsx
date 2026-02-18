import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { api } from "../lib/api";
import { formatProblem } from "../lib/errors";
import type { Job, Resume } from "../lib/types";

export function JobDetailPage() {
  const { jobId = "" } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState<Job | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [notes, setNotes] = useState("");
  const [selectedResumeId, setSelectedResumeId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const canSave = useMemo(() => title.trim() && description.trim().length >= 300, [title, description]);

  async function load() {
    setError(null);
    try {
      const j = await api.getJob(jobId);
      setJob(j);
      setTitle(j.title);
      setDescription(j.description);
      setNotes(j.recruiter_notes ?? "");
      const r = await api.listResumesByWorkspace(j.workspace_id);
      setResumes(r);
      setSelectedResumeId(r[0]?.id ?? "");
    } catch (err) {
      setError(formatProblem(err));
    }
  }

  useEffect(() => {
    void load();
  }, [jobId]);

  return (
    <section className="stack">
      <h1>Job Details</h1>

      <form
        className="panel stack"
        onSubmit={async (e) => {
          e.preventDefault();
          try {
            const updated = await api.updateJob(jobId, {
              title,
              description,
              recruiter_notes: notes || null
            });
            setJob(updated);
          } catch (err) {
            setError(formatProblem(err));
          }
        }}
      >
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
        </label>
        <label>
          Description
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={8} required />
        </label>
        <label>
          Recruiter notes (non-authoritative)
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={4} />
        </label>
        <button type="submit" disabled={!canSave}>
          Save Job
        </button>
      </form>

      <section className="panel stack">
        <h2>Start Evaluation</h2>
        <label>
          Resume
          <select value={selectedResumeId} onChange={(e) => setSelectedResumeId(e.target.value)}>
            {resumes.map((resume) => (
              <option key={resume.id} value={resume.id}>
                {resume.original_filename ?? resume.id}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          disabled={!selectedResumeId || running || !job}
          onClick={async () => {
            if (!job) return;
            setRunning(true);
            setError(null);
            try {
              const evaluation = await api.createEvaluation(job.id, selectedResumeId);
              await api.runEvaluation(evaluation.id);
              navigate(`/evaluations/${evaluation.id}`);
            } catch (err) {
              setError(formatProblem(err));
            } finally {
              setRunning(false);
            }
          }}
        >
          {running ? "Running..." : "Create and Run Evaluation"}
        </button>
      </section>

      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
