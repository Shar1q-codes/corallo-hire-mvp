# Tenant Setup and User Provisioning

## Prerequisites
- Supabase project access with service role credentials.
- Backend env configured (`backend/.env.example` as baseline).
- Python environment with backend dependencies installed.

## Step 1: Create tenant and first user
Use the provisioning helper:

```bash
python backend/scripts/provision_tenant.py \
  --tenant-name "Firm 1" \
  --admin-email "owner@firm1.example" \
  --admin-password "REPLACE_WITH_STRONG_PASSWORD"
```

Expected result:
- A `tenants` row is created.
- A user is created in Supabase Auth.
- User `app_metadata.tenant_id` is set.

This script is provisioning-only and uses service role for setup; normal app operations remain RLS-enforced.

## Step 2: Verify tenant claim
- Sign in as the created user.
- Decode JWT and confirm `tenant_id` claim matches tenant UUID.

## Step 3: Create first workspace, job, resume
Using API with that user token:
1. `POST /workspaces`
2. `POST /workspaces/{workspace_id}/jobs`
3. `POST /workspaces/{workspace_id}/resumes`

## Step 4: Verify RLS and isolation
Run go/no-go checks:

```bash
python backend/scripts/run_go_no_go.py
```

For live isolation gates, set:
- `LIVE_DB_LEAKAGE_TESTS=true`
- `LIVE_API_TESTS=true`
- `LIVE_STORAGE_TESTS=true`

## Step 5: Key rotation and access revoke
- Rotate `SUPABASE_SERVICE_ROLE_KEY` and any leaked API tokens.
- Revoke user sessions from Supabase Auth.
- Disable compromised users and issue replacement credentials.
- Re-run go/no-go before resuming `/evaluations/{evaluation_id}/run`.

## Related docs
- `docs/private_beta/02_safe_usage_rules_for_recruiters.md`
- `docs/private_beta/05_incident_reporting_and_logs.md`
- `backend/PRIVATE_BETA_30_DAY_CHECKLIST.md`
