import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../lib/api";
import { formatProblem } from "../lib/errors";
import type { Job, Resume, Workspace } from "../lib/types";

export function WorkspaceDetailPage() {
  const { id = "" } = useParams();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobTitle, setJobTitle] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [jobNotes, setJobNotes] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canCreateJob = useMemo(() => jobTitle.trim() && jobDescription.trim().length >= 300, [jobTitle, jobDescription]);

  async function loadAll() {
    setError(null);
    try {
      const [w, j, r] = await Promise.all([
        api.getWorkspace(id),
        api.listJobsByWorkspace(id),
        api.listResumesByWorkspace(id)
      ]);
      setWorkspace(w);
      setJobs(j);
      setResumes(r);
    } catch (err) {
      setError(formatProblem(err));
    }
  }

  useEffect(() => {
    void loadAll();
  }, [id]);

  return (
    <section className="stack">
      <h1>{workspace?.name ?? "Workspace"}</h1>
      <div className="grid2">
        <article className="panel stack">
          <h2>Jobs</h2>
          <form
            className="stack"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await api.createJob(id, {
                  title: jobTitle,
                  description: jobDescription,
                  recruiter_notes: jobNotes || null
                });
                setJobTitle("");
                setJobDescription("");
                setJobNotes("");
                await loadAll();
              } catch (err) {
                setError(formatProblem(err));
              }
            }}
          >
            <input value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} placeholder="Title" required />
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Description (minimum 300 characters)"
              rows={6}
              required
            />
            <textarea
              value={jobNotes}
              onChange={(e) => setJobNotes(e.target.value)}
              placeholder="Recruiter notes (non-authoritative)"
              rows={4}
            />
            <button type="submit" disabled={!canCreateJob}>
              Create Job
            </button>
          </form>
          <ul className="list">
            {jobs.map((job) => (
              <li key={job.id}>
                <Link to={`/jobs/${job.id}`}>{job.title}</Link>
              </li>
            ))}
          </ul>
        </article>

        <article className="panel stack">
          <h2>Resumes</h2>
          <form
            className="row"
            onSubmit={async (e) => {
              e.preventDefault();
              if (!resumeFile) return;
              try {
                await api.uploadResume(id, resumeFile);
                setResumeFile(null);
                await loadAll();
              } catch (err) {
                setError(formatProblem(err));
              }
            }}
          >
            <input type="file" onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)} required />
            <button type="submit" disabled={!resumeFile}>
              Upload Resume
            </button>
          </form>
          <ul className="list">
            {resumes.map((resume) => (
              <li key={resume.id}>{resume.original_filename ?? resume.id}</li>
            ))}
          </ul>
        </article>
      </div>
      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
