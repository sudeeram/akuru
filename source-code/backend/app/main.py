from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.api.v1.router import api_router
from app.errors import ErrorResponse, error_content, install_error_handlers
from app.security import Principal, get_principal

settings = get_settings()
app = FastAPI(
    title="AKURU API",
    version="0.2.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.environment == "development" else None,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication required"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        422: {"model": ErrorResponse, "description": "Validation failed"},
    },
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
install_error_handlers(app)
app.include_router(api_router)


@app.middleware("http")
async def request_security(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and origin not in settings.cors_origins:
            return JSONResponse(
                status_code=403,
                content=error_content("origin_not_allowed", "Origin not allowed."),
            )
        content_length = request.headers.get("content-length")
        body_limit = settings.max_document_bytes if request.url.path == "/api/v1/documents" else 1_000_000
        if content_length and content_length.isdigit() and int(content_length) > body_limit:
            return JSONResponse(
                status_code=413,
                content=error_content("request_too_large", "Request body too large."),
            )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "akuru-api"}


@app.get("/ready", tags=["system"])
def ready(
    _principal: Annotated[Principal, Depends(get_principal)],
    db: Session = Depends(get_db),
) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}
