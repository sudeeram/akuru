"""Reviewed reset for replaceable Flashcard content and dependent learner data.

Dry-run is the default. Applying requires an Admin username and the exact
confirmation phrase so a deployment cannot erase Flashcard data accidentally.
The reset intentionally leaves textbook sources, retrieval chunks, visuals,
identity, enrolment and every non-Flashcard learning domain untouched.
"""
import argparse
import json

from sqlalchemy import delete, func, inspect, select

from app.database import SessionLocal
from app.models import (AuditEvent, FlashcardDeck, FlashcardLearningState,
                        FlashcardReview, FlashcardSession, FlashcardVersion, User)


CONFIRMATION = "RESET AKURU FLASHCARDS"
MODELS = (FlashcardReview, FlashcardLearningState, FlashcardSession,
          FlashcardVersion, FlashcardDeck)
DOMAIN_TABLES = {model.__tablename__ for model in MODELS}


def _counts(db) -> dict[str, int]:
    return {model.__tablename__: db.scalar(select(func.count()).select_from(model)) or 0
            for model in MODELS}


def _unexpected_dependencies(db) -> list[str]:
    schema = inspect(db.bind)
    found = []
    for table in schema.get_table_names():
        if table in DOMAIN_TABLES:
            continue
        for foreign_key in schema.get_foreign_keys(table):
            if foreign_key.get("referred_table") in DOMAIN_TABLES:
                found.append(f"{table}.{','.join(foreign_key.get('constrained_columns') or [])}")
    return sorted(found)


def reset(*, admin_username: str | None = None, apply: bool = False,
          confirmation: str | None = None) -> dict:
    with SessionLocal() as db:
        before = _counts(db)
        unexpected = _unexpected_dependencies(db)
        report = {"mode": "apply" if apply else "dry_run", "before": before,
                  "unexpectedDependencies": unexpected,
                  "preserved": ["textbooks", "retrieval_chunks", "textbook_topic_visual_assets",
                                "users", "student_profiles", "enrolments", "non_flashcard_learning"]}
        if unexpected:
            raise RuntimeError("Unknown Flashcard dependencies prevent reset: " + ", ".join(unexpected))
        if not apply:
            report["after"] = before
            return report
        if confirmation != CONFIRMATION:
            raise RuntimeError(f"Apply requires --confirm '{CONFIRMATION}'.")
        admin = db.scalar(select(User).where(User.username == admin_username, User.role == "admin"))
        if not admin:
            raise RuntimeError("A current Admin username is required for the reset audit event.")
        try:
            for model in MODELS:
                db.execute(delete(model))
            db.add(AuditEvent(actor_id=admin.id, action="flashcard_domain.reset",
                              target_type="flashcard_domain", target_id="all",
                              event_data={"deleted": before,
                                          "preservedScopes": report["preserved"]}))
            db.commit()
        except Exception:
            db.rollback()
            raise
        report["after"] = _counts(db)
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run or apply the reviewed AKURU Flashcard reset.")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--admin-username")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    print(json.dumps(reset(admin_username=args.admin_username, apply=args.apply,
                           confirmation=args.confirm), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
