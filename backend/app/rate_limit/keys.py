from uuid import UUID


def tenant_run_key(tenant_id: UUID) -> str:
    return f"tenant:{tenant_id}:evaluation_run"

