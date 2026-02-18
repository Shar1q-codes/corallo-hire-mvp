# Incident Reporting and Logs

## What counts as an incident
- Any suspicion of cross-tenant data exposure.
- Any persisted forbidden language slip.
- Any validator bypass or unexpected acceptance.
- Any unexplained evaluation failure spike.

## What to collect immediately
- `request_id`
- `evaluation_id`
- `tenant_id`
- UTC timestamp and endpoint path

## Where to look
- Application logs (JSON structured logs including request correlation IDs).
- `/metrics` endpoint when enabled (`METRICS_ENABLED=true`) and authorized.
- Go/no-go outputs from `backend/scripts/run_go_no_go.py`.

## Immediate mitigation
1. Disable `/evaluations/{evaluation_id}/run` via feature flag or deployment guard.
2. If no feature flag exists, set run rate limit to zero for impacted tenant(s).
3. Preserve logs and append-only records.
4. Re-run leakage and drift gates before restoring run access.

## Reporting path
- Open incident ticket with severity, tenant impact, and collected IDs.
- Assign engineering owner and record containment time.
- Share post-incident summary in weekly review.
