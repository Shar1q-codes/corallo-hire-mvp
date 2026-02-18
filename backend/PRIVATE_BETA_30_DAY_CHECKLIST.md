# Private Beta 30-Day Stability Checklist

## Daily 15-minute checks
- Verify API 5xx rate and top failing endpoints.
- Review `validator_failures_total` by `{role,code}` for spikes.
- Review `provider_errors_total` and `circuit_breaker_open_total`.
- Review `rate_limited_total` and identify affected tenants.
- Review `rls_denied_total` (should stay near zero for valid traffic).
- Review evaluation failure distribution (`evaluations_failed_total` vs completed).
- Check DB CPU and disk utilization in Supabase dashboard.

## Freeze rules during private beta
- No validator relaxations.
- No schema changes without migration plus full safety-gate pass.
- No new endpoints enabling ranking, summaries, comparisons, or outcomes.
- No bulk operations or cross-candidate processing.

## Rollback triggers
- Any cross-tenant leakage suite failure.
- Any persisted artifact containing forbidden decision/ranking/summary language.
- Circuit breaker held open continuously for more than 15 minutes.
- Evaluation failures above 20% for 60 minutes.

## Incident procedure
- Disable `/evaluations/{evaluation_id}/run` using feature flag or deployment rollback.
- Keep read-only access to existing artifacts.
- Preserve append-only audit logs and event history.
- Run go/no-go suite after mitigation before re-enabling run endpoint.
