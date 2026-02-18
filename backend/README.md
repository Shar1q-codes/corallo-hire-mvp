# HDIS Backend Skeleton

FastAPI backend skeleton for HDIS MVP with strict tenant-aware request handling and Supabase-backed persistence.

## Features
- FastAPI + SQLAlchemy async service structure.
- Tenant context middleware (fail closed on missing/invalid `tenant_id` claim).
- MVP routers only: health, workspaces, jobs, resumes, evaluations, artifacts.
- Supabase Storage upload + signed URL plumbing.
- RFC 9457-style problem details errors.

## Quickstart
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Configure environment:
   ```bash
   cp backend/.env.example backend/.env
   ```
4. Run API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Run from `backend/`.
5. Run tests:
   ```bash
   pytest -q
   ```

## Notes
- Database-level RLS remains authoritative for tenant isolation.
- Backend also applies tenant scoping in all repositories as defense-in-depth.
