-- Internal append-only storage for validated assumption role outputs.
-- This table is not user-facing and does not change the three external artifact types.

create table if not exists public.internal_assumption_outputs (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  job_id uuid not null references public.jobs(id) on delete cascade,
  resume_id uuid not null references public.resumes(id) on delete cascade,
  evaluation_id uuid not null references public.resume_job_evaluations(id) on delete cascade,
  schema_version int not null default 1,
  content_json jsonb not null,
  created_at timestamptz not null default now(),
  created_by uuid not null
);

create index if not exists internal_assumption_outputs_tenant_workspace_idx
  on public.internal_assumption_outputs (tenant_id, workspace_id);
create index if not exists internal_assumption_outputs_tenant_eval_idx
  on public.internal_assumption_outputs (tenant_id, evaluation_id);

create or replace function public.app_validate_internal_assumption_linkage()
returns trigger
language plpgsql
as $$
begin
  if not exists (
    select 1
    from public.resume_job_evaluations e
    where e.id = new.evaluation_id
      and e.tenant_id = new.tenant_id
      and e.workspace_id = new.workspace_id
      and e.job_id = new.job_id
      and e.resume_id = new.resume_id
  ) then
    raise exception 'Tenant/linkage mismatch for internal_assumption_outputs.evaluation_id %', new.evaluation_id
      using errcode = '23514';
  end if;
  return new;
end;
$$;

drop trigger if exists internal_assumption_outputs_tenant_linkage_chk on public.internal_assumption_outputs;
create constraint trigger internal_assumption_outputs_tenant_linkage_chk
after insert or update on public.internal_assumption_outputs
deferrable initially deferred
for each row
execute function public.app_validate_internal_assumption_linkage();

alter table public.internal_assumption_outputs enable row level security;
alter table public.internal_assumption_outputs force row level security;

drop policy if exists internal_assumption_outputs_select_tenant on public.internal_assumption_outputs;
create policy internal_assumption_outputs_select_tenant
  on public.internal_assumption_outputs
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists internal_assumption_outputs_insert_tenant_creator on public.internal_assumption_outputs;
create policy internal_assumption_outputs_insert_tenant_creator
  on public.internal_assumption_outputs
  for insert
  to authenticated
  with check (
    tenant_id = public.app_current_tenant_id()
    and created_by = public.app_current_user_id()
  );

drop policy if exists internal_assumption_outputs_update_denied on public.internal_assumption_outputs;
create policy internal_assumption_outputs_update_denied
  on public.internal_assumption_outputs
  for update
  to authenticated
  using (false)
  with check (false);

drop policy if exists internal_assumption_outputs_delete_denied on public.internal_assumption_outputs;
create policy internal_assumption_outputs_delete_denied
  on public.internal_assumption_outputs
  for delete
  to authenticated
  using (false);

grant select, insert on public.internal_assumption_outputs to authenticated;
