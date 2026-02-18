from fastapi import APIRouter

from app.routers.artifacts import router as artifacts_router
from app.routers.evaluations import router as evaluations_router
from app.routers.evaluations_run import router as evaluations_run_router
from app.routers.health import router as health_router
from app.routers.hitl import router as hitl_router
from app.routers.jobs import router as jobs_router
from app.routers.resumes import router as resumes_router
from app.routers.workspaces import router as workspaces_router


def api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router, tags=["health"])
    router.include_router(workspaces_router, tags=["workspaces"])
    router.include_router(jobs_router, tags=["jobs"])
    router.include_router(resumes_router, tags=["resumes"])
    router.include_router(evaluations_router, tags=["evaluations"])
    router.include_router(evaluations_run_router, tags=["evaluations"])
    router.include_router(hitl_router, tags=["hitl"])
    router.include_router(artifacts_router, tags=["artifacts"])
    return router
