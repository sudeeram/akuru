from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AIInvocation, AuditEvent, DocumentJob, FamilyUsageEvent
from app.permissions import require_roles
from app.security import Principal

router = APIRouter(prefix="/operations", tags=["operations"])

@router.get("/admin/status")
def status(principal: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    since = datetime.now(timezone.utc) - timedelta(days=1)
    jobs = dict(db.execute(select(DocumentJob.status, func.count()).group_by(DocumentJob.status)).all())
    ai = db.execute(select(func.count(), func.coalesce(func.sum(AIInvocation.total_tokens), 0), func.coalesce(func.sum(AIInvocation.latency_ms), 0)).where(AIInvocation.created_at >= since)).one()
    failures = db.scalar(select(func.count()).select_from(AIInvocation).where(AIInvocation.created_at >= since, AIInvocation.status == "failed")) or 0
    family_tokens = db.scalar(select(func.coalesce(func.sum(FamilyUsageEvent.quantity), 0)).where(FamilyUsageEvent.created_at >= since, FamilyUsageEvent.kind == "ai_token")) or 0
    audits = db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(50)).all()
    return {"documentJobs": jobs, "last24Hours": {"aiCalls": ai[0], "aiTokens": ai[1], "familyTokens": family_tokens,
        "aiFailures": failures, "averageLatencyMs": round(ai[2] / ai[0]) if ai[0] else 0},
        "alerts": (["Document jobs have failed."] if jobs.get("failed", 0) else []) + (["AI provider failures occurred in the last 24 hours."] if failures else []),
        "recentAudit": [{"action": row.action, "targetType": row.target_type, "createdAt": row.created_at} for row in audits]}
