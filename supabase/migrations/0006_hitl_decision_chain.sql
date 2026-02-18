-- Step 5 HITL decision chain primitives.
-- These tables are append-only and do not store hiring outcomes or workflow states.

create table if not exists public.human_acknowledgements (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  workspace_id uuid not null references public.workspaces(id) on delete cascade,
  job_id uuid not null references public.jobs(id) on delete cascade,
  resume_id uuid not null references public.resumes(id) on delete cascade,
  evaluation_id uuid not null references public.resume_job_evaluations(id) on delete cascade,
  acknowledgement_type text not null check (
    acknowledgement_type in ('counter_signal_ack', 'validation_gap_declaration', 'override_or_disagreement')
  ),
  subject_ref_type text not null check (
    subject_ref_type in ('intent_item', 'risk_item', 'assumption_item', 'interview_focus_area', 'general')
  ),
  subject_ref_id text,
  content_text text not null,
  decision_mode text not null check (
    decision_mode in ('validate_in_interview', 'skip_validation', 'disagree', 'accept_with_context')
  ),
  created_at timestamptz not null default now(),
  created_by uuid not null
);

create index if not exists human_acknowledgements_tenant_eval_idx
  on public.human_acknowledgements (tenant_id, evaluation_id, created_at desc);

create table if not exists public.decision_chain_events (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references public.tenants(id) on delete restrict,
  evaluation_id uuid not null references public.resume_job_evaluations(id) on delete cascade,
  actor_user_id uuid not null,
  event_type text not null check (
    event_type in (
      'artifacts_viewed',
      'acknowledgement_recorded',
      'override_recorded',
      'final_decision_boundary_reached'
    )
  ),
  detail_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists decision_chain_events_tenant_eval_idx
  on public.decision_chain_events (tenant_id, evaluation_id, created_at asc);

create or replace function public.app_validate_human_ack_linkage()
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
    raise exception 'Tenant/linkage mismatch for human_acknowledgements.evaluation_id %', new.evaluation_id
      using errcode = '23514';
  end if;
  return new;
end;
$$;

create or replace function public.app_validate_decision_chain_event_linkage()
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
    raise exception 'Tenant/linkage mismatch for decision_chain_events.evaluation_id %', new.evaluation_id
      using errcode = '23514';
  end if;
  return new;
end;
$$;

drop trigger if exists human_acknowledgements_linkage_chk on public.human_acknowledgements;
create constraint trigger human_acknowledgements_linkage_chk
after insert or update on public.human_acknowledgements
deferrable initially deferred
for each row
execute function public.app_validate_human_ack_linkage();

drop trigger if exists decision_chain_events_linkage_chk on public.decision_chain_events;
create constraint trigger decision_chain_events_linkage_chk
after insert or update on public.decision_chain_events
deferrable initially deferred
for each row
execute function public.app_validate_decision_chain_event_linkage();

alter table public.human_acknowledgements enable row level security;
alter table public.human_acknowledgements force row level security;
alter table public.decision_chain_events enable row level security;
alter table public.decision_chain_events force row level security;

drop policy if exists human_acknowledgements_select_tenant on public.human_acknowledgements;
create policy human_acknowledgements_select_tenant
  on public.human_acknowledgements
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists human_acknowledgements_insert_tenant on public.human_acknowledgements;
create policy human_acknowledgements_insert_tenant
  on public.human_acknowledgements
  for insert
  to authenticated
  with check (tenant_id = public.app_current_tenant_id());

drop policy if exists human_acknowledgements_update_denied on public.human_acknowledgements;
create policy human_acknowledgements_update_denied
  on public.human_acknowledgements
  for update
  to authenticated
  using (false)
  with check (false);

drop policy if exists human_acknowledgements_delete_denied on public.human_acknowledgements;
create policy human_acknowledgements_delete_denied
  on public.human_acknowledgements
  for delete
  to authenticated
  using (false);

drop policy if exists decision_chain_events_select_tenant on public.decision_chain_events;
create policy decision_chain_events_select_tenant
  on public.decision_chain_events
  for select
  to authenticated
  using (tenant_id = public.app_current_tenant_id());

drop policy if exists decision_chain_events_insert_tenant on public.decision_chain_events;
create policy decision_chain_events_insert_tenant
  on public.decision_chain_events
  for insert
  to authenticated
  with check (tenant_id = public.app_current_tenant_id());

drop policy if exists decision_chain_events_update_denied on public.decision_chain_events;
create policy decision_chain_events_update_denied
  on public.decision_chain_events
  for update
  to authenticated
  using (false)
  with check (false);

drop policy if exists decision_chain_events_delete_denied on public.decision_chain_events;
create policy decision_chain_events_delete_denied
  on public.decision_chain_events
  for delete
  to authenticated
  using (false);

grant select, insert on public.human_acknowledgements to authenticated;
grant select, insert on public.decision_chain_events to authenticated;
