import argparse
import os
import uuid

from supabase import create_client


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision tenant and first admin user for private beta.")
    parser.add_argument("--tenant-name", required=True)
    parser.add_argument("--admin-email", required=True)
    parser.add_argument("--admin-password", required=True)
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    db_url = os.getenv("SUPABASE_DB_URL")

    if not supabase_url or not service_role_key or not db_url:
        raise SystemExit("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and SUPABASE_DB_URL are required")

    client = create_client(supabase_url, service_role_key)
    tenant_id = str(uuid.uuid4())

    import asyncpg
    import asyncio

    async def _insert_tenant() -> None:
        conn = await asyncpg.connect(db_url)
        try:
            await conn.execute(
                "insert into tenants (id, name) values ($1::uuid, $2)",
                tenant_id,
                args.tenant_name,
            )
        finally:
            await conn.close()

    asyncio.run(_insert_tenant())

    user = client.auth.admin.create_user(
        {
            "email": args.admin_email,
            "password": args.admin_password,
            "email_confirm": True,
            "app_metadata": {"tenant_id": tenant_id},
        }
    )

    print("Provisioning complete")
    print(f"tenant_id={tenant_id}")
    print(f"user_id={user.user.id}")
    print("Reminder: run go/no-go before live usage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
