"""HTTP route for readiness."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/health")
def get_health(request: Request):
    request.app.state.health_service.check_ready()
    return {"status": "ready"}
