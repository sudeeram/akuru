from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Course, Subject
from app.auth import router as auth_router
from app.portal import router as portal_router
from app.security import Principal, get_principal

settings = get_settings()
app = FastAPI(
    title="AKURU API",
    version="0.2.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.environment == "development" else None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(portal_router)


@app.middleware("http")
async def request_security(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and origin not in settings.cors_origins:
            return JSONResponse(status_code=403, content={"detail": "Origin not allowed."})
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > 1_000_000:
            return JSONResponse(status_code=413, content={"detail": "Request body too large."})
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


@app.get("/api/v1/catalog", tags=["curriculum"])
def catalog(
    _principal: Annotated[Principal, Depends(get_principal)],
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, object]]]:
    courses = db.execute(select(Course).order_by(Course.name)).scalars()
    subjects = db.execute(select(Subject).order_by(Subject.name)).scalars()
    return {
        "courses": [{"id": row.id, "name": row.name, "phase1Active": row.phase1_active} for row in courses],
        "subjects": [{"id": row.id, "name": row.name} for row in subjects],
    }
