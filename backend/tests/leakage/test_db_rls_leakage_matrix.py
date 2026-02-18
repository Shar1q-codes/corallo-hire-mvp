import os
import uuid

import asyncpg
import pytest

LIVE = os.getenv("LIVE_DB_LEAKAGE_TESTS", "").lower() == "true"
DB_URL = os.getenv("SUPABASE_DB_URL", "")
TENANT_A = os.getenv("LEAK_TEST_TENANT_A_ID", "")
TENANT_B = os.getenv("LEAK_TEST_TENANT_B_ID", "")
USER_A = os.getenv("LEAK_TEST_USER_A_ID", "")
USER_B = os.getenv("LEAK_TEST_USER_B_ID", "")


pytestmark = pytest.mark.skipif(
    not (LIVE and DB_URL and TENANT_A and TENANT_B and USER_A and USER_B),
    reason="Set LIVE_DB_LEAKAGE_TESTS=true and DB/JWT claim env vars to run live RLS leakage matrix.",
)


TABLES = [
    "tenants",
    "workspaces",
    "jobs",
    "resumes",
    "resume_job_evaluations",
    "artifacts",
    "internal_assumption_outputs",
    "human_acknowledgements",
    "decision_chain_events",
    "artifact_view_events",
]


def _claims(tenant_id: str, user_id: str) -> str:
    return '{"tenant_id":"%s","sub":"%s","role":"authenticated"}' % (tenant_id, user_id)


async def _table_exists(conn: asyncpg.Connection, table_name: str) -> bool:
    return bool(await conn.fetchval("select to_regclass($1)", f"public.{table_name}"))


async def _as_tenant_fetchval(conn: asyncpg.Connection, tenant_id: str, user_id: str, sql: str, *args):
    async with conn.transaction():
        await conn.execute("set local role authenticated")
        await conn.execute("select set_config('request.jwt.claims', $1, true)", _claims(tenant_id, user_id))
        return await conn.fetchval(sql, *args)


async def _as_tenant_fetch(conn: asyncpg.Connection, tenant_id: str, user_id: str, sql: str, *args):
    async with conn.transaction():
        await conn.execute("set local role authenticated")
        await conn.execute("select set_config('request.jwt.claims', $1, true)", _claims(tenant_id, user_id))
        return await conn.fetch(sql, *args)


async def _as_tenant_exec(conn: asyncpg.Connection, tenant_id: str, user_id: str, sql: str, *args):
    async with conn.transaction():
        await conn.execute("set local role authenticated")
        await conn.execute("select set_config('request.jwt.claims', $1, true)", _claims(tenant_id, user_id))
        return await conn.execute(sql, *args)


@pytest.mark.asyncio
async def test_db_rls_leakage_matrix() -> None:
    conn = await asyncpg.connect(DB_URL)
    try:
        ws_id = uuid.uuid4()
        job_id = uuid.uuid4()
        resume_id = uuid.uuid4()
        eval_id = uuid.uuid4()
        artifact_id = uuid.uuid4()

        # Baseline A-side inserts for core tables.
        await _as_tenant_exec(
            conn,
            TENANT_A,
            USER_A,
            """
            insert into workspaces (id, tenant_id, name, created_by)
            values ($1, $2, 'Leakage Matrix Workspace', $3)
            """,
            ws_id,
            TENANT_A,
            USER_A,
        )
        await _as_tenant_exec(
            conn,
            TENANT_A,
            USER_A,
            """
            insert into jobs (id, tenant_id, workspace_id, title, description, recruiter_notes, created_by)
            values ($1, $2, $3, 'Leakage Matrix Job', repeat('x', 320), null, $4)
            """,
            job_id,
            TENANT_A,
            ws_id,
            USER_A,
        )
        await _as_tenant_exec(
            conn,
            TENANT_A,
            USER_A,
            """
            insert into resumes (id, tenant_id, workspace_id, file_object_path, original_filename, mime_type, size_bytes, created_by)
            values ($1, $2, $3, $4, 'resume.txt', 'text/plain', 10, $5)
            """,
            resume_id,
            TENANT_A,
            ws_id,
            f"tenant/{TENANT_A}/workspace/{ws_id}/resume/{resume_id}/resume.txt",
            USER_A,
        )
        await _as_tenant_exec(
            conn,
            TENANT_A,
            USER_A,
            """
            insert into resume_job_evaluations (id, tenant_id, workspace_id, job_id, resume_id, status, created_by)
            values ($1, $2, $3, $4, $5, 'created', $6)
            """,
            eval_id,
            TENANT_A,
            ws_id,
            job_id,
            resume_id,
            USER_A,
        )
        await _as_tenant_exec(
            conn,
            TENANT_A,
            USER_A,
            """
            insert into artifacts (
              id, tenant_id, workspace_id, job_id, resume_id, evaluation_id,
              artifact_type, schema_version, content_json, created_by
            )
            values ($1, $2, $3, $4, $5, $6, 'intent_hypotheses', 1, '{"hypotheses":[]}'::jsonb, $7)
            """,
            artifact_id,
            TENANT_A,
            ws_id,
            job_id,
            resume_id,
            eval_id,
            USER_A,
        )

        # Optional table inserts if present in this branch state.
        if await _table_exists(conn, "internal_assumption_outputs"):
            await _as_tenant_exec(
                conn,
                TENANT_A,
                USER_A,
                """
                insert into internal_assumption_outputs (
                  tenant_id, workspace_id, job_id, resume_id, evaluation_id, schema_version, content_json, created_by
                ) values ($1, $2, $3, $4, $5, 1, '{"assumptions":[]}'::jsonb, $6)
                """,
                TENANT_A,
                ws_id,
                job_id,
                resume_id,
                eval_id,
                USER_A,
            )

        if await _table_exists(conn, "human_acknowledgements"):
            await _as_tenant_exec(
                conn,
                TENANT_A,
                USER_A,
                """
                insert into human_acknowledgements (
                  tenant_id, workspace_id, job_id, resume_id, evaluation_id,
                  acknowledgement_type, subject_ref_type, subject_ref_id,
                  content_text, decision_mode, created_by
                ) values (
                  $1, $2, $3, $4, $5,
                  'counter_signal_ack', 'risk_item', 'risk:1',
                  'Candidate shows conflicting signals requiring deeper validation during interview.',
                  'validate_in_interview', $6
                )
                """,
                TENANT_A,
                ws_id,
                job_id,
                resume_id,
                eval_id,
                USER_A,
            )

        if await _table_exists(conn, "decision_chain_events"):
            await _as_tenant_exec(
                conn,
                TENANT_A,
                USER_A,
                """
                insert into decision_chain_events (tenant_id, evaluation_id, actor_user_id, event_type, detail_json)
                values ($1, $2, $3, 'artifacts_viewed', '{"artifact_types":["intent_hypotheses"]}'::jsonb)
                """,
                TENANT_A,
                eval_id,
                USER_A,
            )

        if await _table_exists(conn, "artifact_view_events"):
            await _as_tenant_exec(
                conn,
                TENANT_A,
                USER_A,
                """
                insert into artifact_view_events (tenant_id, evaluation_id, user_id, artifact_type, detail_json)
                values ($1, $2, $3, 'intent_hypotheses', '{}'::jsonb)
                """,
                TENANT_A,
                eval_id,
                USER_A,
            )

        # Matrix checks for each existing table.
        for table_name in TABLES:
            if not await _table_exists(conn, table_name):
                continue

            # B should never read A rows.
            if table_name == "tenants":
                read_count = await _as_tenant_fetchval(
                    conn,
                    TENANT_B,
                    USER_B,
                    "select count(*) from tenants where id = $1",
                    TENANT_A,
                )
            else:
                read_count = await _as_tenant_fetchval(
                    conn,
                    TENANT_B,
                    USER_B,
                    f"select count(*) from {table_name} where tenant_id = $1",
                    TENANT_A,
                )
            assert read_count == 0, f"Cross-tenant SELECT leaked in {table_name}"

        # B insert linked to A workspace must fail.
        with pytest.raises(Exception):
            await _as_tenant_exec(
                conn,
                TENANT_B,
                USER_B,
                """
                insert into jobs (tenant_id, workspace_id, title, description, created_by)
                values ($1, $2, 'Bad Link', repeat('x', 320), $3)
                """,
                TENANT_B,
                ws_id,
                USER_B,
            )

        # B update/delete attempts on A ids should affect zero rows or error under RLS.
        updated = await _as_tenant_exec(
            conn,
            TENANT_B,
            USER_B,
            "update workspaces set name = 'forbidden' where id = $1",
            ws_id,
        )
        assert updated.endswith("UPDATE 0"), "Cross-tenant UPDATE affected rows"

        deleted = await _as_tenant_exec(
            conn,
            TENANT_B,
            USER_B,
            "delete from workspaces where id = $1",
            ws_id,
        )
        assert deleted.endswith("DELETE 0"), "Cross-tenant DELETE affected rows"

    finally:
        await conn.close()
