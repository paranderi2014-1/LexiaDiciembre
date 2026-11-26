-- Private bucket for user-owned case documents.
-- Object names MUST begin with the authenticated user's UUID: <uid>/<filename>.
insert into storage.buckets (id, name, public, file_size_limit)
values ('lexia-case-files', 'lexia-case-files', false, 20971520)
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit;

-- Existing policies from the original export may already exist; use unique names.
create policy "lexia_case_files_user_read"
on storage.objects for select to authenticated
using (
  bucket_id = 'lexia-case-files'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "lexia_case_files_user_insert"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'lexia-case-files'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "lexia_case_files_user_update"
on storage.objects for update to authenticated
using (
  bucket_id = 'lexia-case-files'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
)
with check (
  bucket_id = 'lexia-case-files'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);

create policy "lexia_case_files_user_delete"
on storage.objects for delete to authenticated
using (
  bucket_id = 'lexia-case-files'
  and (storage.foldername(name))[1] = (select auth.uid()::text)
);
