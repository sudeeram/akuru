"""Dry-run-first repair for historical extraction-review status mismatches."""

from __future__ import annotations

import argparse
import json

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Document, DocumentVersion, User
from app.services.documents import _refresh_topic_document_readiness


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply the reported changes.")
    parser.add_argument("--actor-username", help="Admin username recorded on completion events.")
    args = parser.parse_args()
    if args.apply and not args.actor_username:
        parser.error("--actor-username is required with --apply")
    with SessionLocal() as db:
        actor = db.scalar(select(User).where(User.username == args.actor_username, User.role == "admin")) \
            if args.actor_username else None
        if args.apply and not actor:
            parser.error("The supplied Admin username does not exist.")
        changes = []
        for version in db.scalars(select(DocumentVersion).order_by(DocumentVersion.created_at)).all():
            document = db.get(Document, version.document_id)
            before = {"versionStatus": version.status,
                      "libraryReviewState": document.review_state if document else None}
            _refresh_topic_document_readiness(db, version.id, actor.id if actor else None)
            after = {"versionStatus": version.status,
                     "libraryReviewState": document.review_state if document else None}
            if before != after:
                changes.append({"documentId": str(version.document_id),
                                "documentVersionId": str(version.id), "before": before, "after": after})
        print(json.dumps({"mode": "apply" if args.apply else "dry_run", "changeCount": len(changes),
                          "changes": changes}, indent=2))
        if args.apply:
            db.commit()
        else:
            db.rollback()


if __name__ == "__main__":
    main()
