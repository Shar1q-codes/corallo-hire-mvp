from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import jwt
from fastapi import Request
from jwt import PyJWKClient

from app.core.config import Settings
from app.core.errors import ApiProblem


@dataclass(slots=True)
class RequestContext:
    user_id: UUID
    tenant_id: UUID


def _parse_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise ApiProblem(
            status=401,
            title="Unauthorized",
            detail="Missing Authorization header.",
            type_="https://hdis.dev/problems/unauthorized",
        )
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise ApiProblem(
            status=401,
            title="Unauthorized",
            detail="Invalid Authorization header format.",
            type_="https://hdis.dev/problems/unauthorized",
        )
    return parts[1].strip()


def decode_jwt_claims(token: str, settings: Settings) -> dict[str, Any]:
    try:
        if settings.jwt_jwks_url:
            jwk_client = PyJWKClient(settings.jwt_jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token)
            options = {"verify_signature": True}
            kwargs: dict[str, Any] = {
                "algorithms": ["RS256", "ES256"],
                "options": options,
            }
            if settings.jwt_audience:
                kwargs["audience"] = settings.jwt_audience
            else:
                kwargs["options"] = {"verify_signature": True, "verify_aud": False}
            if settings.jwt_issuer:
                kwargs["issuer"] = settings.jwt_issuer
            return jwt.decode(token, signing_key.key, **kwargs)

        # MVP fallback when JWKS is not configured: parse claims only and fail closed on missing tenant/user.
        return jwt.decode(token, options={"verify_signature": False, "verify_aud": False, "verify_iss": False})
    except jwt.PyJWTError as exc:
        raise ApiProblem(
            status=401,
            title="Unauthorized",
            detail="Invalid authentication token.",
            type_="https://hdis.dev/problems/unauthorized",
        ) from exc


def build_request_context(authorization: str | None, settings: Settings) -> RequestContext:
    token = _parse_bearer_token(authorization)
    claims = decode_jwt_claims(token, settings)

    raw_user_id = claims.get("sub")
    raw_tenant_id = claims.get("tenant_id")
    if not raw_user_id or not raw_tenant_id:
        raise ApiProblem(
            status=401,
            title="Unauthorized",
            detail="Token is missing required tenant or user claim.",
            type_="https://hdis.dev/problems/unauthorized",
        )

    try:
        user_id = UUID(str(raw_user_id))
        tenant_id = UUID(str(raw_tenant_id))
    except ValueError as exc:
        raise ApiProblem(
            status=401,
            title="Unauthorized",
            detail="Token contains invalid tenant or user claim format.",
            type_="https://hdis.dev/problems/unauthorized",
        ) from exc

    return RequestContext(user_id=user_id, tenant_id=tenant_id)


def get_request_context(request: Request) -> RequestContext:
    context = getattr(request.state, "request_context", None)
    if context is None:
        raise ApiProblem(
            status=401,
            title="Unauthorized",
            detail="Missing tenant context.",
            type_="https://hdis.dev/problems/unauthorized",
        )
    return context

