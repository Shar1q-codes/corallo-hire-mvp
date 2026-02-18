-- Artifact consumption evidence table.
-- This is read-path gating metadata, not workflow state.

create table if not exists public.artifact_view_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  evaluation_id uuid not null references public.resume_job_evaluations(id) on delete cascade,
  user_id uuid not null,
  artifact_type text not null check (
    artifact_type in ('intent_hypotheses', 'risk_signals', 'interview_guidance')
  ),
  viewed_at timestamptz not null default now(),
  detail_json jsonb not null default '{}'::jsonb
);

create index if not exists artifact_view_events_tenant_eval_user_artifact_idx
  on public.artifact_view_events (tenant_id, evaluation_id, user_id, artifact_type, viewed_at desc);

create or replace function public.app_validate_artifact_view_linkage()
returns trigger
language plpgsql
as $$
begin
  if not exists (
    select 1
    from public.resume_job_evaluations e
    where e.id = new.evaluation_id
      and e.tenant_id = new.tenant_id
  ) then
    raise exception 'Tenant/linkage mismatch for artifact_view_events.evaluation_id %', new.evaluation_id
      using errcode = '23514';
  end if;
  return new;
end;
$$;

drop trigger if exists artifact_view_events_linkage_chk on public.artifact_view_events;
create constraint trigger artifact_view_events_linkage_chk
after insert or update on public.artifact_view_events
deferrable initially deferred
for each row
execute function public.app_validate_artifact_view_linkage();

alter table public.artifact_view_events enable row level security;
alter table public.artifact_view_events force row level security;

drop policy if exists artifact_view_events_select_tenant on public.artifact_view_events;
create policy artifact_view_events_select_tenant
  on public.artifact_view_events
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists artifact_view_events_insert_tenant on public.artifact_view_events;
create policy artifact_view_events_insert_tenant
  on public.artifact_view_events
  for insert
  to authenticated
  with check (tenant_id = public.app_current_tenant_id());

drop policy if exists artifact_view_events_update_denied on public.artifact_view_events;
create policy artifact_view_events_update_denied
  on public.artifact_view_events
  for update
  to authenticated
  using (false)
  with check (false);

drop policy if exists artifact_view_events_delete_denied on public.artifact_view_events;
create policy artifact_view_events_delete_denied
  on public.artifact_view_events
  for delete
  to authenticated
  using (false);

grant select, insert on public.artifact_view_events to authenticated;
