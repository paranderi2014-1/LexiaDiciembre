-- Remove the original policy names before relying on the consolidated bucket policies.
drop policy if exists own_case_files_read on storage.objects;
drop policy if exists own_case_files_insert on storage.objects;
drop policy if exists own_case_files_delete on storage.objects;
