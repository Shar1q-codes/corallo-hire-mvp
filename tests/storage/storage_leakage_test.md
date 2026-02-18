# HDIS Storage Leakage Test

## Purpose
Validate `resumes` bucket isolation by tenant-scoped object path policies.

## Prerequisites
- Migrations applied through:
  - `supabase/migrations/0003_hdis_storage_policies.sql`
- Two authenticated users in different tenants (`tenant_id` in JWT claim).
- Node.js 18+.

## Environment Variables
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `USER_A_EMAIL`
- `USER_A_PASSWORD`
- `USER_B_EMAIL`
- `USER_B_PASSWORD`

## Run
1. Install dependency:
   ```bash
   npm install @supabase/supabase-js
   ```
2. Execute:
   ```bash
   node tests/storage/storage_leakage_test_node.mjs
   ```

Expected outcomes:
- User A uploads to `tenant/{tenantA}/workspace/{workspaceId}/resume/{resumeId}/{filename}`.
- User A can download own object.
- User B cannot download/list User A object.
- User B cannot upload into User A tenant path.
