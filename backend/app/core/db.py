from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import RequestContext

settings = get_settings()

if settings.supabase_db_url:
    engine = create_async_engine(settings.supabase_db_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
else:
    engine = None

async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False) if engine else None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_factory is None:
        raise RuntimeError("SUPABASE_DB_URL is not configured.")
    async with async_session_factory() as session:
        yield session


async def apply_rls_context(session: AsyncSession, context: RequestContext) -> None:
    claims = {
        "sub": str(context.user_id),
        "role": "authenticated",
        "tenant_id": str(context.tenant_id),
    }
    await session.execute(text("select set_config('request.jwt.claims', :claims, true)"), {"claims": json.dumps(claims)})
    await session.execute(text("select set_config('request.jwt.claim.sub', :sub, true)"), {"sub": str(context.user_id)})
    await session.execute(text("set local role authenticated"))

