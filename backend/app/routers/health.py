from fastapi import APIRouter, status

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Check whether the Environmental Intelligence Backend API is operational.",
)
def get_health():
    """Health check endpoint returning service health status."""
    return {
        "status": "healthy",
        "service": "environmental-intelligence-api",
    }
