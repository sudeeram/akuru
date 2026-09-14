import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import TutorSession, TutorSignal, TutorTurn, TutorTurnSource


def replay(db: Session, session_id: uuid.UUID, request_key: str) -> TutorTurn | None:
    return db.scalar(select(TutorTurn).where(
        TutorTurn.session_id == session_id, TutorTurn.role == "assistant",
        TutorTurn.request_key == request_key,
    ))


def recent(db: Session, session_id: uuid.UUID, limit: int = 12) -> list[TutorTurn]:
    rows = db.scalars(select(TutorTurn).where(TutorTurn.session_id == session_id)
                      .order_by(TutorTurn.sequence.desc()).limit(limit)).all()
    return list(reversed(rows))


def save_exchange(db: Session, session: TutorSession, message: str, request_key: str,
                  response: dict, source_ids: list[uuid.UUID], operation_id: uuid.UUID,
                  provider: str, model: str, prompt_name: str, prompt_version: str) -> TutorTurn:
    sequence = (db.scalar(select(func.max(TutorTurn.sequence)).where(TutorTurn.session_id == session.id)) or 0) + 1
    student = TutorTurn(public_ref=f"tutor_turn_{uuid.uuid4().hex}", session_id=session.id,
        profile_version_id=session.current_profile_version_id, sequence=sequence, role="student",
        modality="text", content=message, request_key=request_key[:92] + ":student", operation_id=operation_id)
    assistant = TutorTurn(public_ref=f"tutor_turn_{uuid.uuid4().hex}", session_id=session.id,
        profile_version_id=session.current_profile_version_id, sequence=sequence + 1, role="assistant",
        modality="text", content=response["content"], response_data=response,
        request_key=request_key, operation_id=operation_id, provider=provider, model=model,
        prompt_name=prompt_name, prompt_version=prompt_version)
    db.add_all([student, assistant]); db.flush()
    assistant.response_data = {**response, "turnRef": assistant.public_ref}
    for ordinal, chunk_id in enumerate(source_ids):
        db.add(TutorTurnSource(turn_id=assistant.id, retrieval_chunk_id=chunk_id, ordinal=ordinal))
    db.commit(); db.refresh(assistant)
    return assistant


def append_signals(db: Session, session: TutorSession, turn: TutorTurn, signals: list,
                   provider: str, model: str, prompt_name: str, prompt_version: str) -> None:
    for signal in signals:
        db.add(TutorSignal(public_ref=f"tutor_signal_{uuid.uuid4().hex}", student_id=session.student_id,
            session_id=session.id, turn_id=turn.id, unit_id=session.active_unit_id,
            category=signal.category, observation=signal.observation,
            evidence_references=signal.evidenceRefs, confidence=signal.confidence,
            prompt_name=prompt_name, prompt_version=prompt_version, provider=provider, model=model))
    db.commit()
