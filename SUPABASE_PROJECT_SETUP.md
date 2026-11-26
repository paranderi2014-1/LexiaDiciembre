# Supabase target setup — LexIAParaguay

Target project ref: `tgjyqtoaicrzkhzyoyop`
Project URL: `https://tgjyqtoaicrzkhzyoyop.supabase.co`

## Important status
The public Supabase gateway was reachable during the setup check, but both `/auth/v1/health` and `/rest/v1/` returned `401` because the request did not include an `apikey` header. This is expected for an unauthenticated probe and is **not** a database, Auth, migration, or RLS test. No credentials were supplied to this workspace.

## Safe deployment sequence
1. Confirm this is the intended project and create/verify a separate staging project before applying schema changes.
2. In the Supabase Dashboard, inspect existing tables and migration history. Back up the database and Storage first.
3. If the remote database already contains schema changes not represented here, capture them before pushing (for example, `supabase db pull --remote`). Do not blindly push migrations over an unknown schema.
4. From a trusted terminal, authenticate with the Supabase CLI, then run `supabase link --project-ref tgjyqtoaicrzkhzyoyop`.
5. Review the SQL under `supabase/migrations/`, then deploy to staging with `supabase db push --dry-run` if supported by the installed CLI, review the output, and only then `supabase db push`.
6. Verify tables, indexes, RLS policies, and the private `lexia-case-files` bucket in the Dashboard.
7. Run two-user negative tests: user A must not read, update, or delete user B's threads, messages, cases, case entries, or Storage objects. Test anonymous access too.
8. Only after staging passes should the same reviewed migration set be applied to production.

## Secrets
Set `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `OPENAI_API_KEY`, `FIRECRAWL_API_KEY`, and `MCP_ACCESS_TOKEN` in the selected hosting provider's server/environment secret manager. `SUPABASE_SERVICE_ROLE_KEY` (if actually needed by server code) must remain server-only. Never commit `.env`, keys, access tokens, database passwords, or service-role credentials. `VITE_*` variables are exposed to the browser and must contain only public configuration.

## CLI commands (trusted local terminal only)
```bash
supabase login
supabase link --project-ref tgjyqtoaicrzkhzyoyop
supabase migration list --linked
supabase db push --dry-run
# Review the dry-run output and backup before proceeding:
supabase db push
```

Do not run the final `db push` until the remote schema and migration history have been reviewed and a backup exists.
