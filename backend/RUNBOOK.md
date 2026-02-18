# HDIS MVP Runbook

## 1) Validator Failures Spike
- Check: `validator_failures_total{role,code}`, `role_attempts_total{role,attempt}`.
- Common causes: prompt drift, provider formatting changes, malformed JSON wrappers.
- Action: inspect failure-code distribution and schema paths; do not relax validator rules.

## 2) Provider Outage
- Check: `provider_errors_total`, `circuit_breaker_open_total`.
- Expected behavior: run endpoint returns deterministic `503` with circuit-breaker error type.
- Action: wait for provider recovery and retry; no partial rollback beyond append-only history.

## 3) RLS-Denied Increase
- Check: `rls_denied_total`.
- Common causes: missing/misconfigured `tenant_id` claim, role mismatch, policy drift.
- Action: verify auth claims, tenant context resolver, and Supabase RLS policies.

## 4) Rate-Limit Triggering
- Check: `rate_limited_total`.
- Common causes: concentrated tenant load or abuse.
- Action: tune per-tenant limits carefully; do not introduce batching or cross-candidate contexts.
