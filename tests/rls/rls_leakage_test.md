# HDIS RLS Leakage Test

## Purpose
Validate that tenant isolation is enforced by PostgreSQL RLS and tenant-linkage constraints, not by API code.

## Prerequisites
- Supabase project with migrations applied:
  - `supabase/migrations/0001_hdis_core_schema.sql`
  - `supabase/migrations/0002_hdis_rls_policies.sql`
  - `supabase/migrations/0003_hdis_storage_policies.sql`
  - Optional: `supabase/migrations/0004_hdis_leakage_test_setup.sql`
- Two authenticated users in Supabase Auth with different `tenant_id` JWT claims.
- Node.js 18+ for the Node test.

## Run SQL-only Test
1. Open Supabase SQL editor.
2. Run `tests/rls/rls_leakage_test.sql`.
3. Confirm you only see `PASS` notices and no `FAIL` exception.

Expected outcomes:
- Tenant B sees zero rows for tenant A IDs.
- Tenant B cross-tenant inserts fail.
- Tenant B cross-tenant updates/deletes affect zero rows.
- `artifacts` and `audit_log` reject mutations (append-only).

## Run Node Test
1. Install dependency:
   ```bash
   npm install @supabase/supabase-js
   ```
2. Set environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `USER_A_EMAIL`
   - `USER_A_PASSWORD`
   - `USER_B_EMAIL`
   - `USER_B_PASSWORD`
3. Run:
   ```bash
   node tests/rls/rls_leakage_test_node.mjs
   ```

Expected outcomes:
- Script prints PASS per test case.
- Final line prints `All RLS leakage tests passed.`.
