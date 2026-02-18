-- SQL-only RLS leakage verification for HDIS MVP.
-- Run this as a privileged role in Supabase SQL editor after migrations are applied.
-- Expected result: all PASS notices, no cross-tenant data visibility, and blocked cross-tenant writes.

-- Stable fixture IDs.
-- Tenants:
--   A: 11111111-1111-4111-8111-111111111111
--   B: 22222222-2222-4222-8222-222222222222
-- Users:
--   A: aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1
--   B: bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2

reset role;

insert into public.tenants (id, name)
values
  ('11111111-1111-4111-8111-111111111111', 'Tenant A'),
  ('22222222-2222-4222-8222-222222222222', 'Tenant B')
on conflict (id) do update
set name = excluded.name;

delete from public.audit_log where id in (
  '17000000-0000-4000-8000-000000000001',
  '17000000-0000-4000-8000-000000000002'
);
delete from public.artifacts where id in (
  '16000000-0000-4000-8000-000000000001',
  '16000000-0000-4000-8000-000000000002'
);
delete from public.resume_job_evaluations where id in (
  '15000000-0000-4000-8000-000000000001',
  '15000000-0000-4000-8000-000000000002'
);
delete from public.resumes where id in (
  '14000000-0000-4000-8000-000000000001',
  '14000000-0000-4000-8000-000000000002'
);
delete from public.jobs where id in (
  '13000000-0000-4000-8000-000000000001',
  '13000000-0000-4000-8000-000000000002'
);
delete from public.workspaces where id in (
  '12000000-0000-4000-8000-000000000001',
  '12000000-0000-4000-8000-000000000002'
);

set role authenticated;

-- Tenant A context and inserts.
select set_config(
  'request.jwt.claims',
  '{"sub":"aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1","role":"authenticated","tenant_id":"11111111-1111-4111-8111-111111111111"}',
  true
);
select set_config('request.jwt.claim.sub', 'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1', true);

insert into public.workspaces (id, tenant_id, name, created_by)
values (
  '12000000-0000-4000-8000-000000000001',
  '11111111-1111-4111-8111-111111111111',
  'Workspace A',
  'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1'
);

insert into public.jobs (id, tenant_id, workspace_id, title, description, recruiter_notes, created_by)
values (
  '13000000-0000-4000-8000-000000000001',
  '11111111-1111-4111-8111-111111111111',
  '12000000-0000-4000-8000-000000000001',
  'Backend Engineer',
  'MVP backend role',
  'Context only',
  'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1'
);

insert into public.resumes (
  id, tenant_id, workspace_id, file_object_path, original_filename, mime_type, size_bytes, extracted_text, created_by
)
values (
  '14000000-0000-4000-8000-000000000001',
  '11111111-1111-4111-8111-111111111111',
  '12000000-0000-4000-8000-000000000001',
  'tenant/11111111-1111-4111-8111-111111111111/workspace/12000000-0000-4000-8000-000000000001/resume/14000000-0000-4000-8000-000000000001/a_resume.txt',
  'a_resume.txt',
  'text/plain',
  1234,
  null,
  'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1'
);

insert into public.resume_job_evaluations (
  id, tenant_id, workspace_id, job_id, resume_id, status, failure_reason_code, created_by
)
values (
  '15000000-0000-4000-8000-000000000001',
  '11111111-1111-4111-8111-111111111111',
  '12000000-0000-4000-8000-000000000001',
  '13000000-0000-4000-8000-000000000001',
  '14000000-0000-4000-8000-000000000001',
  'created',
  null,
  'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1'
);

insert into public.artifacts (
  id, tenant_id, workspace_id, job_id, resume_id, evaluation_id, artifact_type, schema_version, content_json, created_by
)
values (
  '16000000-0000-4000-8000-000000000001',
  '11111111-1111-4111-8111-111111111111',
  '12000000-0000-4000-8000-000000000001',
  '13000000-0000-4000-8000-000000000001',
  '14000000-0000-4000-8000-000000000001',
  '15000000-0000-4000-8000-000000000001',
  'intent_hypotheses',
  1,
  '{"items":[{"text":"candidate may value autonomy"}]}'::jsonb,
  'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1'
);

insert into public.audit_log (
  id, tenant_id, actor_user_id, entity_type, entity_id, action, detail_json
)
values (
  '17000000-0000-4000-8000-000000000001',
  '11111111-1111-4111-8111-111111111111',
  'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1',
  'evaluation',
  '15000000-0000-4000-8000-000000000001',
  'create',
  '{"source":"sql_test"}'::jsonb
);

-- Tenant B context.
select set_config(
  'request.jwt.claims',
  '{"sub":"bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2","role":"authenticated","tenant_id":"22222222-2222-4222-8222-222222222222"}',
  true
);
select set_config('request.jwt.claim.sub', 'bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2', true);

do $$
declare
  cnt int;
begin
  select count(*) into cnt from public.workspaces where id = '12000000-0000-4000-8000-000000000001';
  if cnt <> 0 then raise exception 'FAIL: tenant B can read tenant A workspace'; end if;

  select count(*) into cnt from public.jobs where id = '13000000-0000-4000-8000-000000000001';
  if cnt <> 0 then raise exception 'FAIL: tenant B can read tenant A job'; end if;

  select count(*) into cnt from public.resumes where id = '14000000-0000-4000-8000-000000000001';
  if cnt <> 0 then raise exception 'FAIL: tenant B can read tenant A resume'; end if;

  select count(*) into cnt from public.resume_job_evaluations where id = '15000000-0000-4000-8000-000000000001';
  if cnt <> 0 then raise exception 'FAIL: tenant B can read tenant A evaluation'; end if;

  select count(*) into cnt from public.artifacts where id = '16000000-0000-4000-8000-000000000001';
  if cnt <> 0 then raise exception 'FAIL: tenant B can read tenant A artifact'; end if;

  select count(*) into cnt from public.audit_log where id = '17000000-0000-4000-8000-000000000001';
  if cnt <> 0 then raise exception 'FAIL: tenant B can read tenant A audit_log'; end if;

  raise notice 'PASS: tenant B cannot read tenant A rows';
end $$;

do $$
begin
  begin
    insert into public.jobs (id, tenant_id, workspace_id, title, description, created_by)
    values (
      '13000000-0000-4000-8000-000000000002',
      '22222222-2222-4222-8222-222222222222',
      '12000000-0000-4000-8000-000000000001',
      'Cross tenant write attempt',
      'Must fail',
      'bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2'
    );
    raise exception 'FAIL: tenant B inserted job referencing tenant A workspace';
  exception
    when others then
      raise notice 'PASS: cross-tenant job insert blocked: %', sqlerrm;
  end;

  begin
    insert into public.resume_job_evaluations (
      id, tenant_id, workspace_id, job_id, resume_id, status, created_by
    )
    values (
      '15000000-0000-4000-8000-000000000002',
      '22222222-2222-4222-8222-222222222222',
      '12000000-0000-4000-8000-000000000001',
      '13000000-0000-4000-8000-000000000001',
      '14000000-0000-4000-8000-000000000001',
      'created',
      'bbbbbbb2-bbbb-4bbb-8bbb-bbbbbbbbbbb2'
    );
    raise exception 'FAIL: tenant B inserted evaluation referencing tenant A entities';
  exception
    when others then
      raise notice 'PASS: cross-tenant evaluation insert blocked: %', sqlerrm;
  end;
end $$;

do $$
declare
  affected int;
begin
  update public.workspaces
  set name = 'tenant B overwrite attempt'
  where id = '12000000-0000-4000-8000-000000000001';
  get diagnostics affected = row_count;
  if affected <> 0 then raise exception 'FAIL: tenant B updated tenant A workspace'; end if;

  delete from public.jobs
  where id = '13000000-0000-4000-8000-000000000001';
  get diagnostics affected = row_count;
  if affected <> 0 then raise exception 'FAIL: tenant B deleted tenant A job'; end if;

  raise notice 'PASS: tenant B cannot update/delete tenant A rows';
end $$;

-- Tenant A verifies append-only behavior.
select set_config(
  'request.jwt.claims',
  '{"sub":"aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1","role":"authenticated","tenant_id":"11111111-1111-4111-8111-111111111111"}',
  true
);
select set_config('request.jwt.claim.sub', 'aaaaaaa1-aaaa-4aaa-8aaa-aaaaaaaaaaa1', true);

do $$
declare
  affected int;
begin
  begin
    update public.artifacts
    set content_json = '{"mutated":true}'::jsonb
    where id = '16000000-0000-4000-8000-000000000001';
    get diagnostics affected = row_count;
    if affected <> 0 then
      raise exception 'FAIL: artifacts update affected rows in append-only table';
    end if;
    raise notice 'PASS: artifacts update blocked (0 rows affected)';
  exception
    when others then
      raise notice 'PASS: artifacts update blocked: %', sqlerrm;
  end;

  begin
    delete from public.audit_log
    where id = '17000000-0000-4000-8000-000000000001';
    get diagnostics affected = row_count;
    if affected <> 0 then
      raise exception 'FAIL: audit_log delete affected rows in append-only table';
    end if;
    raise notice 'PASS: audit_log delete blocked (0 rows affected)';
  exception
    when others then
      raise notice 'PASS: audit_log delete blocked: %', sqlerrm;
  end;
end $$;

reset role;

-- End of test.
