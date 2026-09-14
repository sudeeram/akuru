import uuid
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.study_plans import PlanGenerateRequest, PlanHistoryResponse, StudyPlanResponse
from app.security import Principal
from app.services import study_plans

router=APIRouter(prefix="/plans",tags=["study plans"])

@router.get("/students/{student_id}",response_model=StudyPlanResponse)
def current_plan(student_id:uuid.UUID,principal:Annotated[Principal,Depends(require_roles("student","parent"))],db:Annotated[Session,Depends(get_db)]):
    return study_plans.current(db,principal,student_id)

@router.get("/students/{student_id}/history",response_model=PlanHistoryResponse)
def plan_history(student_id:uuid.UUID,principal:Annotated[Principal,Depends(require_roles("student","parent"))],db:Annotated[Session,Depends(get_db)]):
    return study_plans.history(db,principal,student_id)

@router.post("",response_model=StudyPlanResponse)
def generate_plan(payload:PlanGenerateRequest,principal:Annotated[Principal,Depends(require_csrf_roles("student","parent"))],db:Annotated[Session,Depends(get_db)]):
    student_id=payload.studentId or principal.user.id
    study_plans.authorize(db,principal,student_id)
    return study_plans.generate(db,student_id,principal.user.id,force=True)

@router.post("/items/{item_id}/complete",response_model=StudyPlanResponse)
def complete_item(item_id:uuid.UUID,principal:Annotated[Principal,Depends(require_csrf_roles("student"))],db:Annotated[Session,Depends(get_db)]):
    return study_plans.complete(db,principal,item_id)
