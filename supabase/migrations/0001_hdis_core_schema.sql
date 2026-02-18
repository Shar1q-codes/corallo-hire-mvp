-- HDIS MVP core schema.
-- This schema intentionally avoids ATS workflow semantics, ranking, scoring, and summaries.

create extension if not exists pgcrypto;

-- Centralized tenant/user helpers used by all RLS policies.
create or replace function public.app_current_tenant_id()
returns uuid
language plpgsql
stable
as $$
declare
  claims jsonb;
  raw_tenant text;
begin
  claims := auth.jwt();
  if claims is null then
    return null;
  end if;

  raw_tenant := claims ->> 'tenant_id';
  if raw_tenant is null or btrim(raw_tenant) = '' then
    return null;
  end if;

  return raw_tenant::uuid;
exception
  when others then
    return null;
end;
$$;

create or replace function public.app_current_user_id()
returns uuid
language sql
stable
as $$
  select auth.uid()
$$;

create table if not exists public.tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.workspaces (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  name text not null,
  created_at timestamptz not null default now(),
  created_by uuid not null
);

create table if not exists public.jobs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  title text not null,
  description text not null,
  recruiter_notes text,
  created_at timestamptz not null default now(),
  created_by uuid not null
);
comment on column public.jobs.recruiter_notes is
  'Non-authoritative recruiter context only; not used for workflow or outcome state.';

create table if not exists public.resumes (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  file_object_path text not null,
  original_filename text,
  mime_type text,
  size_bytes bigint,
  extracted_text text,
  created_at timestamptz not null default now(),
  created_by uuid not null
);

create table if not exists public.resume_job_evaluations (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  job_id uuid not null references public.jobs(id) on delete cascade,
  resume_id uuid not null references public.resumes(id) on delete cascade,
  status text not null check (status in ('created', 'completed', 'failed')),
  failure_reason_code text,
  idempotency_key text,
  created_at timestamptz not null default now(),
  created_by uuid not null
);

create unique index if not exists resume_job_evaluations_tenant_idempotency_key_uniq
  on public.resume_job_evaluations (tenant_id, idempotency_key)
  where idempotency_key is not null;

create table if not exists public.artifacts (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  job_id uuid not null references public.jobs(id) on delete cascade,
  resume_id uuid not null references public.resumes(id) on delete cascade,
  evaluation_id uuid not null references public.resume_job_evaluations(id) on delete cascade,
  artifact_type text not null check (
    artifact_type in ('intent_hypotheses', 'risk_signals', 'interview_guidance')
  ),
  schema_version int not null default 1,
  content_json jsonb not null,
  created_at timestamptz not null default now(),
  created_by uuid not null
);
comment on table public.artifacts is
  'Append-only artifact history for exactly three allowed artifact types.';

create table if not exists public.audit_log (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  actor_user_id uuid not null,
  entity_type text not null,
  entity_id uuid,
  action text not null,
  detail_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
comment on table public.audit_log is
  'Append-only immutable audit trail; updates/deletes are intentionally blocked by RLS.';

create index if not exists workspaces_tenant_workspace_idx
  on public.workspaces (tenant_id, id);
create index if not exists workspaces_tenant_created_at_idx
  on public.workspaces (tenant_id, created_at desc);

create index if not exists jobs_tenant_workspace_idx
  on public.jobs (tenant_id, workspace_id);
create index if not exists jobs_tenant_created_at_idx
  on public.jobs (tenant_id, created_at desc);

create index if not exists resumes_tenant_workspace_idx
  on public.resumes (tenant_id, workspace_id);
create index if not exists resumes_tenant_created_at_idx
  on public.resumes (tenant_id, created_at desc);

create index if not exists evaluations_tenant_workspace_idx
  on public.resume_job_evaluations (tenant_id, workspace_id);
create index if not exists evaluations_tenant_job_resume_created_idx
  on public.resume_job_evaluations (tenant_id, job_id, resume_id, created_at desc);

create index if not exists artifacts_tenant_workspace_idx
  on public.artifacts (tenant_id, workspace_id);
create index if not exists artifacts_tenant_job_resume_created_idx
  on public.artifacts (tenant_id, job_id, resume_id, created_at desc);
create index if not exists artifacts_tenant_evaluation_idx
  on public.artifacts (tenant_id, evaluation_id);

create index if not exists audit_log_tenant_created_idx
  on public.audit_log (tenant_id, created_at desc);

-- Cross-table tenant linkage is enforced with deferred constraint triggers.
create or replace function public.app_validate_tenant_linkage()
returns trigger
language plpgsql
as $$
begin
  if tg_table_name = 'jobs' then
    if not exists (
      select 1
      from public.workspaces w
      where w.id = new.workspace_id
        and w.tenant_id = new.tenant_id
    ) then
      raise exception 'Tenant mismatch for jobs.workspace_id % and jobs.tenant_id %', new.workspace_id, new.tenant_id
        using errcode = '23514';
    end if;
    return new;
  end if;

  if tg_table_name = 'resumes' then
    if not exists (
      select 1
      from public.workspaces w
      where w.id = new.workspace_id
        and w.tenant_id = new.tenant_id
    ) then
      raise exception 'Tenant mismatch for resumes.workspace_id % and resumes.tenant_id %', new.workspace_id, new.tenant_id
        using errcode = '23514';
    end if;
    return new;
  end if;

  if tg_table_name = 'resume_job_evaluations' then
    if not exists (
      select 1
      from public.workspaces w
      where w.id = new.workspace_id
        and w.tenant_id = new.tenant_id
    ) then
      raise exception 'Tenant mismatch for evaluations.workspace_id % and evaluations.tenant_id %', new.workspace_id, new.tenant_id
        using errcode = '23514';
    end if;

    if not exists (
      select 1
      from public.jobs j
      where j.id = new.job_id
        and j.tenant_id = new.tenant_id
        and j.workspace_id = new.workspace_id
    ) then
      raise exception 'Tenant/workspace mismatch for evaluations.job_id %', new.job_id
        using errcode = '23514';
    end if;

    if not exists (
      select 1
      from public.resumes r
      where r.id = new.resume_id
        and r.tenant_id = new.tenant_id
        and r.workspace_id = new.workspace_id
    ) then
      raise exception 'Tenant/workspace mismatch for evaluations.resume_id %', new.resume_id
        using errcode = '23514';
    end if;
    return new;
  end if;

  if tg_table_name = 'artifacts' then
    if not exists (
      select 1
      from public.resume_job_evaluations e
      where e.id = new.evaluation_id
        and e.tenant_id = new.tenant_id
        and e.workspace_id = new.workspace_id
        and e.job_id = new.job_id
        and e.resume_id = new.resume_id
    ) then
      raise exception 'Tenant/linkage mismatch for artifacts.evaluation_id %', new.evaluation_id
        using errcode = '23514';
    end if;
    return new;
  end if;

  return new;
end;
$$;

drop trigger if exists jobs_tenant_linkage_chk on public.jobs;
create constraint trigger jobs_tenant_linkage_chk
after insert or update on public.jobs
deferrable initially deferred
for each row
execute function public.app_validate_tenant_linkage();

drop trigger if exists resumes_tenant_linkage_chk on public.resumes;
create constraint trigger resumes_tenant_linkage_chk
after insert or update on public.resumes
deferrable initially deferred
for each row
execute function public.app_validate_tenant_linkage();

drop trigger if exists evaluations_tenant_linkage_chk on public.resume_job_evaluations;
create constraint trigger evaluations_tenant_linkage_chk
after insert or update on public.resume_job_evaluations
deferrable initially deferred
for each row
execute function public.app_validate_tenant_linkage();

drop trigger if exists artifacts_tenant_linkage_chk on public.artifacts;
create constraint trigger artifacts_tenant_linkage_chk
after insert or update on public.artifacts
deferrable initially deferred
for each row
execute function public.app_validate_tenant_linkage();
