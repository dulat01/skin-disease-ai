"""
API Gateway Main Application
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import redis.asyncio as redis

from app.config import settings
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.cors import setup_cors
from app.routers import auth_router, predictions_router, admin_router, public_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Redis client for rate limiting
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    global redis_client

    # Startup
    logger.info(f"Starting {settings.SERVICE_NAME} v{settings.VERSION}")

    try:
        redis_client = redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}. Rate limiting disabled.")
        redis_client = None

    yield

    # Shutdown
    if redis_client:
        await redis_client.close()
    logger.info(f"Shutting down {settings.SERVICE_NAME}")


# Create FastAPI application
app = FastAPI(
    title="Skin Disease AI - API Gateway",
    description="Central API gateway for the skin disease classification system",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup CORS
setup_cors(app)

# Add authentication middleware (before rate limiting to get user_id)
app.add_middleware(AuthMiddleware)


# Add rate limiting middleware after app is created
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    # Skip for certain paths
    if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    if redis_client:
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        client_key = f"rate_limit:{user_id or client_ip}"

        try:
            pipe = redis_client.pipeline()
            pipe.incr(client_key)
            pipe.expire(client_key, settings.RATE_LIMIT_WINDOW, nx=True)
            results = await pipe.execute()
            current_count = results[0]

            if current_count > settings.RATE_LIMIT_REQUESTS:
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Try again in {settings.RATE_LIMIT_WINDOW} seconds."
                    },
                    headers={
                        "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(settings.RATE_LIMIT_WINDOW)
                    }
                )

            response = await call_next(request)
            remaining = max(0, settings.RATE_LIMIT_REQUESTS - current_count)
            response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            return response

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return await call_next(request)

    return await call_next(request)


# Include routers
app.include_router(public_router)
app.include_router(auth_router)
app.include_router(predictions_router)
app.include_router(admin_router)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    import httpx

    async def check_service(name: str, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                return "healthy" if response.status_code == 200 else "unhealthy"
        except Exception:
            return "unavailable"

    # Check dependencies
    dependencies = {}

    # Check Redis
    if redis_client:
        try:
            await redis_client.ping()
            dependencies["redis"] = "healthy"
        except Exception:
            dependencies["redis"] = "unhealthy"
    else:
        dependencies["redis"] = "unavailable"

    # Check downstream services
    dependencies["auth_service"] = await check_service("auth", settings.AUTH_SERVICE_URL)
    dependencies["prediction_service"] = await check_service("prediction", settings.PREDICTION_SERVICE_URL)
    dependencies["admin_service"] = await check_service("admin", settings.ADMIN_SERVICE_URL)

    # Determine overall status
    status = "healthy"
    if any(v == "unhealthy" for v in dependencies.values()):
        status = "degraded"
    if all(v in ["unhealthy", "unavailable"] for k, v in dependencies.items() if k != "redis"):
        status = "unhealthy"

    return {
        "status": status,
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "dependencies": dependencies
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
