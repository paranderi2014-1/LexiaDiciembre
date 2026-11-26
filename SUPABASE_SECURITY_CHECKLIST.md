# LexIAParaguay — Supabase deployment and isolation checks

## Required project configuration

1. Create or select the intended Supabase project; do not paste service-role keys into the browser or commit them.
2. Set `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_PUBLISHABLE_KEY` in the server/deployment environment.
3. Configure the Google OAuth provider only if Google login is required. Add the deployed callback URL to Supabase Auth redirect allow-list and the Google OAuth client.
4. Apply migrations in `supabase/migrations/` in timestamp order (Supabase CLI `supabase db push` or SQL editor, after reviewing the target project).
5. Confirm `lexia-case-files` exists and is private. Upload paths must be `<authenticated-user-uuid>/<filename>`.
6. Configure SMTP, site URL, password-reset redirect URLs, and allowed origins before production.

## Data isolation design in this export

- `lexia_threads`: `user_id = auth.uid()` for all operations.
- `lexia_messages`: access is permitted only when the parent thread belongs to `auth.uid()`.
- `legal_cases`: `user_id = auth.uid()` for all operations.
- `case_entries`: access is permitted only when the parent case belongs to `auth.uid()`.
- `legal_library`: published rows are readable publicly; management is restricted to `has_role(auth.uid(), 'admin')`.
- `user_roles`: authenticated users can read only their own role row; no client-side write grant is issued.
- `lexia-case-files`: private bucket; top-level object folder must equal `auth.uid()`.

## Mandatory two-user negative test (run only in a non-production test project)

Create two test accounts A and B. Sign in separately and verify:

1. A creates a thread and a case; B cannot select, update, or delete either record by UUID.
2. B cannot read, insert, update, or delete messages under A's thread.
3. B cannot read, insert, update, or delete entries under A's case.
4. A can upload/read/delete `A_UUID/test.pdf`; B cannot access that object and cannot upload to `A_UUID/`.
5. An ordinary account cannot insert/update/delete `user_roles` or change itself to `admin`.
6. Anonymous users can read only published legal-library rows, never private cases or conversations.

Record the SQL/API request, user identity, expected result, actual result, and timestamp for each test. Do not declare isolation verified until all negative tests pass.

## Important

The migrations create schema and policies; they do not migrate existing Supabase users, Auth settings, database rows, Storage objects, SMTP settings, OAuth secrets, or project-level configuration. Those must be migrated separately from the source Supabase project with explicit authorization and a backup.
