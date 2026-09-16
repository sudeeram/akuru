import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.permissions import require_csrf_roles, require_roles
from app.schemas.question_mappings import (
    MappingSuggestionResponse, PaperMappingResponse, QuestionMappingResponse,
    SaveUnitMappingsRequest,
    SaveTopicMappingsRequest, TopicMappingSuggestionResponse, TopicPaperMappingResponse, TopicQuestionMappingResponse,
)
from app.security import Principal
from app.services import question_mappings
from app.services import topic_question_mappings


router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("/papers/{paper_id}/topic-mappings", response_model=TopicPaperMappingResponse)
def paper_topic_mappings(paper_id: uuid.UUID, _principal: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return topic_question_mappings.paper_mappings(db, paper_id)


@router.post("/{question_id}/topic-mapping/suggest", response_model=TopicMappingSuggestionResponse)
def suggest_topic_mapping(question_id: uuid.UUID, _principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return topic_question_mappings.suggest(db, question_id)


@router.post("/{question_id}/topic-mapping", response_model=TopicQuestionMappingResponse)
def save_topic_mapping(question_id: uuid.UUID, payload: SaveTopicMappingsRequest, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return topic_question_mappings.save(db, principal, question_id, payload)


@router.post("/{question_id}/topic-mapping/publish", response_model=TopicQuestionMappingResponse)
def publish_topic_mapping(question_id: uuid.UUID, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return topic_question_mappings.publish(db, principal, question_id)


@router.get("/papers/{paper_id}/unit-mappings", response_model=PaperMappingResponse)
def paper_unit_mappings(paper_id: uuid.UUID, _principal: Annotated[Principal, Depends(require_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return question_mappings.paper_mappings(db, paper_id)


@router.post("/{question_id}/unit-mapping/suggest", response_model=MappingSuggestionResponse)
def suggest_unit_mapping(question_id: uuid.UUID, _principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)], settings: Annotated[Settings, Depends(get_settings)]):
    return question_mappings.suggest(db, settings, question_id)


@router.post("/{question_id}/unit-mapping", response_model=QuestionMappingResponse)
def save_unit_mapping(question_id: uuid.UUID, payload: SaveUnitMappingsRequest, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return question_mappings.save(db, principal, question_id, payload)


@router.post("/{question_id}/unit-mapping/publish", response_model=QuestionMappingResponse)
def publish_unit_mapping(question_id: uuid.UUID, principal: Annotated[Principal, Depends(require_csrf_roles("admin"))], db: Annotated[Session, Depends(get_db)]):
    return question_mappings.publish(db, principal, question_id)
