-- Optional helper objects/fixtures for local leakage testing.
-- This is test support only and not required for production runtime.

create schema if not exists test_support;

create or replace function test_support.set_auth_context(p_user_id uuid, p_tenant_id uuid)
returns void
language plpgsql
as $$
begin
  perform set_config(
    'request.jwt.claims',
    json_build_object(
      'sub', p_user_id::text,
      'role', 'authenticated',
      'tenant_id', p_tenant_id::text
    )::text,
    true
  );
  perform set_config('request.jwt.claim.sub', p_user_id::text, true);
  perform set_config('role', 'authenticated', true);
end;
$$;

create or replace function test_support.clear_auth_context()
returns void
language plpgsql
as $$
begin
  perform set_config('request.jwt.claims', '', true);
  perform set_config('request.jwt.claim.sub', '', true);
end;
$$;

-- Stable tenant fixtures used by tests.
insert into public.tenants (id, name)
values
  ('11111111-1111-4111-8111-111111111111', 'Tenant A'),
  ('22222222-2222-4222-8222-222222222222', 'Tenant B')
on conflict (id) do update
set name = excluded.name;
