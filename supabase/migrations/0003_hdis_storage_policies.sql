-- HDIS MVP storage isolation for resume files.
-- Object access is tenant-scoped by parsing object key paths and matching JWT tenant claim.

insert into storage.buckets (id, name, public)
values ('resumes', 'resumes', false)
on conflict (id) do update
set public = excluded.public;

create or replace function public.app_storage_uuid_segment(path text, segment_pos int)
returns uuid
language plpgsql
stable
as $$
declare
  raw_segment text;
begin
  raw_segment := split_part(path, '/', segment_pos);
  if raw_segment is null or btrim(raw_segment) = '' then
    return null;
  end if;
  return raw_segment::uuid;
exception
  when others then
    return null;
end;
$$;

create or replace function public.app_storage_object_tenant_id(path text)
returns uuid
language sql
stable
as $$
  select public.app_storage_uuid_segment(path, 2)
$$;

create or replace function public.app_storage_is_valid_resume_path(path text)
returns boolean
language plpgsql
stable
as $$
declare
  segment_count int;
begin
  segment_count := array_length(string_to_array(path, '/'), 1);
  if segment_count is distinct from 7 then
    return false;
  end if;

  if split_part(path, '/', 1) <> 'tenant' then
    return false;
  end if;

  if split_part(path, '/', 3) <> 'workspace' then
    return false;
  end if;

  if split_part(path, '/', 5) <> 'resume' then
    return false;
  end if;

  if public.app_storage_uuid_segment(path, 2) is null then
    return false;
  end if;
  if public.app_storage_uuid_segment(path, 4) is null then
    return false;
  end if;
  if public.app_storage_uuid_segment(path, 6) is null then
    return false;
  end if;
  if split_part(path, '/', 7) = '' then
    return false;
  end if;

  return true;
end;
$$;

alter table storage.buckets enable row level security;
alter table storage.objects enable row level security;

drop policy if exists storage_buckets_resumes_select on storage.buckets;
create policy storage_buckets_resumes_select
  on storage.buckets
  for select
  to authenticated
  using (id = 'resumes');

drop policy if exists storage_objects_resumes_select_tenant on storage.objects;
create policy storage_objects_resumes_select_tenant
  on storage.objects
  for select
  to authenticated
  using (
    bucket_id = 'resumes'
    and public.app_storage_is_valid_resume_path(name)
    and public.app_storage_object_tenant_id(name) = public.app_current_tenant_id()
  );

drop policy if exists storage_objects_resumes_insert_tenant on storage.objects;
create policy storage_objects_resumes_insert_tenant
  on storage.objects
  for insert
  to authenticated
  with check (
    bucket_id = 'resumes'
    and public.app_storage_is_valid_resume_path(name)
    and public.app_storage_object_tenant_id(name) = public.app_current_tenant_id()
  );

drop policy if exists storage_objects_resumes_update_denied on storage.objects;
create policy storage_objects_resumes_update_denied
  on storage.objects
  for update
  to authenticated
  using (false)
  with check (false);

drop policy if exists storage_objects_resumes_delete_denied on storage.objects;
create policy storage_objects_resumes_delete_denied
  on storage.objects
  for delete
  to authenticated
  using (false);

grant execute on function public.app_storage_uuid_segment(text, int) to authenticated;
grant execute on function public.app_storage_object_tenant_id(text) to authenticated;
grant execute on function public.app_storage_is_valid_resume_path(text) to authenticated;

grant select on storage.buckets to authenticated;
grant select, insert on storage.objects to authenticated;
