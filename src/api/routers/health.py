"""
Health check endpoints for load balancer integration.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from ...core.database import get_db
from ...core.config import get_settings
from ...schemas.schemas import HealthCheck, DetailedHealthCheck

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Simple health check endpoint.
    
    Returns:
        Basic health status and version
    """
    return HealthCheck(
        status="healthy",
        version=settings.APP_VERSION
    )


@router.get("/health/detailed", response_model=DetailedHealthCheck)
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with dependency status.
    
    Checks:
    - Database connectivity
    - Redis connectivity
    
    Returns:
        Health status of all components
    """
    # Check database
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            socket_timeout=1.0,
            socket_connect_timeout=1.0
        )
        redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unavailable (using in-memory fallback)"
    
    overall_status = "healthy" if db_status == "healthy" else "degraded"
    
    return DetailedHealthCheck(
        status=overall_status,
        version=settings.APP_VERSION,
        database=db_status,
        redis=redis_status
    )
