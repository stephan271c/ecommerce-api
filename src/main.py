"""
E-Commerce API - Main Application

Production-ready RESTful API with:
- JWT authentication
- Rate limiting
- Health checks
- Structured logging
- CORS support
"""

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .core.config import get_settings
from .core.database import init_db
from .middleware.middleware import RequestIDMiddleware, LoggingMiddleware
from .services.rate_limit import rate_limit_dependency, add_rate_limit_headers
from .core.exceptions import APIException

# Import routers
from .api.routers import auth, users, listings, external, frontend
from .api.routers.health import router as health_router

settings = get_settings()


def create_initial_admin():
    """Create initial admin user from environment variables if configured."""
    if not all([settings.ADMIN_EMAIL, settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD]):
        return  # Not configured, skip
    
    from .core.database import SessionLocal
    from .models.models import User, UserRole
    from .services.auth import get_password_hash
    import logging
    
    logger = logging.getLogger("api")
    db = SessionLocal()
    
    try:
        # Check if any admin already exists
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN.value).first()
        if existing_admin:
            logger.info("Admin user already exists, skipping auto-creation")
            return
        
        # Check if email/username already taken
        existing = db.query(User).filter(
            (User.email == settings.ADMIN_EMAIL) | (User.username == settings.ADMIN_USERNAME)
        ).first()
        if existing:
            logger.warning(f"Cannot create admin: email or username already exists")
            return
        
        # Create admin
        admin = User(
            email=settings.ADMIN_EMAIL,
            username=settings.ADMIN_USERNAME,
            hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN.value
        )
        db.add(admin)
        db.commit()
        logger.info(f"✓ Initial admin '{settings.ADMIN_USERNAME}' created successfully")
    except Exception as e:
        logger.error(f"Error creating initial admin: {e}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    init_db()
    create_initial_admin()
    yield
    # Shutdown (cleanup if needed)


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## E-Commerce REST API

A production-ready API for an e-commerce platform.

### Features
- **User Management**: Registration, authentication, profile management
- **Listings**: Create and manage product listings
- **Rate Limiting**: Redis-based sliding window rate limiting
- **Health Checks**: Load balancer integration endpoints

### Authentication
Use the `/v1/auth/register` endpoint to create an account, then
`/v1/auth/login` to get a JWT token. Include the token in the
`Authorization` header as `Bearer <token>`.
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware (order matters - last added runs first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)


# Global exception handler
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions with standardized format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
        headers={"X-Request-ID": getattr(request.state, "request_id", "N/A")}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    import logging
    logger = logging.getLogger("api")
    logger.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {}
        },
        headers={"X-Request-ID": getattr(request.state, "request_id", "N/A")}
    )


# Mount static files
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include API routers
app.include_router(health_router)
app.include_router(auth.router, dependencies=[Depends(rate_limit_dependency)])
app.include_router(users.router, dependencies=[Depends(rate_limit_dependency)])
app.include_router(listings.router, dependencies=[Depends(rate_limit_dependency)])
app.include_router(external.router, dependencies=[Depends(rate_limit_dependency)])

# Include frontend router (must be last to avoid route conflicts)
app.include_router(frontend.router)


# Rate limited example endpoint
@app.get("/v1/rate-limited", tags=["Examples"])
async def rate_limited_endpoint(
    request: Request,
    _: None = None  # We'll add rate limiting via middleware in production
):
    """
    Example rate-limited endpoint.
    
    Rate limit headers are included in the response.
    """
    # For demonstration, manually check rate limit
    from .services.rate_limit import sliding_window_rate_limit, get_client_identifier
    
    client_id = get_client_identifier(request)
    is_allowed, remaining, limit, reset_time = sliding_window_rate_limit(client_id)
    
    response_data = {
        "message": "This endpoint is rate limited",
        "rate_limit": {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time
        }
    }
    
    if not is_allowed:
        from .core.exceptions import RateLimitError
        raise RateLimitError(retry_after=reset_time - int(__import__('time').time()))
    
    return response_data

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)