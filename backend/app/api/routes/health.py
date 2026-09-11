from fastapi import APIRouter, HTTPException, status

from app.db.health import check_database_connection


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/database")
async def database_health_check() -> dict[str, str]:
    is_connected = await check_database_connection()

    if not is_connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )

    return {
        "status": "healthy",
        "database": "connected",
    }