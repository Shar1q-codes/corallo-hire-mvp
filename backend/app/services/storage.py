from __future__ import annotations

import re
from uuid import UUID

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool

from app.core.supabase import get_supabase_client

BUCKET_NAME = "resumes"


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", filename.strip())
    return cleaned or "upload.bin"


def build_resume_object_path(tenant_id: UUID, workspace_id: UUID, resume_id: UUID, filename: str) -> str:
    safe_name = sanitize_filename(filename)
    return f"tenant/{tenant_id}/workspace/{workspace_id}/resume/{resume_id}/{safe_name}"


async def upload_resume_file(path: str, file: UploadFile) -> None:
    content = await file.read()
    content_type = file.content_type or "application/octet-stream"
    client = get_supabase_client()

    def _upload() -> None:
        client.storage.from_(BUCKET_NAME).upload(path, content, {"content-type": content_type})

    await run_in_threadpool(_upload)


async def create_signed_download_url(path: str, expires_in_seconds: int = 300) -> str:
    client = get_supabase_client()

    def _sign() -> str:
        response = client.storage.from_(BUCKET_NAME).create_signed_url(path, expires_in_seconds)
        signed_url = response.get("signedURL") or response.get("signedUrl")
        if not signed_url:
            raise RuntimeError("Failed to create signed URL.")
        if signed_url.startswith("http://") or signed_url.startswith("https://"):
            return signed_url
        return f"{client.supabase_url}/storage/v1{signed_url}"

    return await run_in_threadpool(_sign)

