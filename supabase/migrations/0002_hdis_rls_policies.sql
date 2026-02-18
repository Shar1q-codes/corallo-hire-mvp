-- HDIS MVP row-level security.
-- RLS is the primary tenant isolation barrier and is enforced at database level.

alter table public.tenants enable row level security;
alter table public.tenants force row level security;

alter table public.workspaces enable row level security;
alter table public.workspaces force row level security;

alter table public.jobs enable row level security;
alter table public.jobs force row level security;

alter table public.resumes enable row level security;
alter table public.resumes force row level security;

alter table public.resume_job_evaluations enable row level security;
alter table public.resume_job_evaluations force row level security;

alter table public.artifacts enable row level security;
alter table public.artifacts force row level security;

alter table public.audit_log enable row level security;
alter table public.audit_log force row level security;

drop policy if exists tenants_select_own on public.tenants;
create policy tenants_select_own
  on public.tenants
  for select
  to authenticated
  using (id = public.app_current_tenant_id());

-- No insert/update/delete policy on tenants for authenticated users.
-- Service role can manage tenants outside client-scope operations.

drop policy if exists workspaces_select_tenant on public.workspaces;
create policy workspaces_select_tenant
  on public.workspaces
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists workspaces_insert_tenant_creator on public.workspaces;
create policy workspaces_insert_tenant_creator
  on public.workspaces
  for insert
  to authenticated
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists workspaces_update_tenant_creator on public.workspaces;
create policy workspaces_update_tenant_creator
  on public.workspaces
  for update
  to authenticated
  using (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  )
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists workspaces_delete_tenant_creator on public.workspaces;
create policy workspaces_delete_tenant_creator
  on public.workspaces
  for delete
  to authenticated
  using (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists jobs_select_tenant on public.jobs;
create policy jobs_select_tenant
  on public.jobs
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists jobs_insert_tenant_creator on public.jobs;
create policy jobs_insert_tenant_creator
  on public.jobs
  for insert
  to authenticated
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists jobs_update_tenant_creator on public.jobs;
create policy jobs_update_tenant_creator
  on public.jobs
  for update
  to authenticated
  using (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  )
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists jobs_delete_tenant_creator on public.jobs;
create policy jobs_delete_tenant_creator
  on public.jobs
  for delete
  to authenticated
  using (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists resumes_select_tenant on public.resumes;
create policy resumes_select_tenant
  on public.resumes
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists resumes_insert_tenant_creator on public.resumes;
create policy resumes_insert_tenant_creator
  on public.resumes
  for insert
  to authenticated
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists resumes_update_tenant_creator on public.resumes;
create policy resumes_update_tenant_creator
  on public.resumes
  for update
  to authenticated
  using (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  )
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists resumes_delete_tenant_creator on public.resumes;
create policy resumes_delete_tenant_creator
  on public.resumes
  for delete
  to authenticated
  using (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists evaluations_select_tenant on public.resume_job_evaluations;
create policy evaluations_select_tenant
  on public.resume_job_evaluations
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists evaluations_insert_tenant_creator on public.resume_job_evaluations;
create policy evaluations_insert_tenant_creator
  on public.resume_job_evaluations
  for insert
  to authenticated
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists evaluations_update_tenant_creator on public.resume_job_evaluations;
create policy evaluations_update_tenant_creator
  on public.resume_job_evaluations
  for update
  to authenticated
  using (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  )
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists evaluations_delete_tenant_creator on public.resume_job_evaluations;
create policy evaluations_delete_tenant_creator
  on public.resume_job_evaluations
  for delete
  to authenticated
  using (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

-- Append-only table: read + insert only.
drop policy if exists artifacts_select_tenant on public.artifacts;
create policy artifacts_select_tenant
  on public.artifacts
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists artifacts_insert_tenant_creator on public.artifacts;
create policy artifacts_insert_tenant_creator
  on public.artifacts
  for insert
  to authenticated
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists artifacts_update_denied on public.artifacts;
create policy artifacts_update_denied
  on public.artifacts
  for update
  to authenticated
  using (false)
  with check (false);

drop policy if exists artifacts_delete_denied on public.artifacts;
create policy artifacts_delete_denied
  on public.artifacts
  for delete
  to authenticated
  using (false);

-- Append-only table: read + insert only.
drop policy if exists audit_log_select_tenant on public.audit_log;
create policy audit_log_select_tenant
  on public.audit_log
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists audit_log_insert_tenant_actor on public.audit_log;
create policy audit_log_insert_tenant_actor
  on public.audit_log
  for insert
  to authenticated
  with check (
    tenant_id = public.app_current_tenant_id()
    and actor_user_id = public.app_current_user_id()
  );

drop policy if exists audit_log_update_denied on public.audit_log;
create policy audit_log_update_denied
  on public.audit_log
  for update
  to authenticated
  using (false)
  with check (false);

drop policy if exists audit_log_delete_denied on public.audit_log;
create policy audit_log_delete_denied
  on public.audit_log
  for delete
  to authenticated
  using (false);

grant usage on schema public to authenticated;
grant execute on function public.app_current_tenant_id() to authenticated;
grant execute on function public.app_current_user_id() to authenticated;

grant select on public.tenants to authenticated;

grant select, insert, update, delete on public.workspaces to authenticated;
grant select, insert, update, delete on public.jobs to authenticated;
grant select, insert, update, delete on public.resumes to authenticated;
grant select, insert, update, delete on public.resume_job_evaluations to authenticated;

grant select, insert on public.artifacts to authenticated;
grant select, insert on public.audit_log to authenticated;
