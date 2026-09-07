from fastapi import APIRouter

from backend.schemas import StatusResponse

router = APIRouter(prefix="/api/v1", tags=["status"])


@router.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse()
