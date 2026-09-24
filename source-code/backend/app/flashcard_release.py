import argparse
import json

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.services.flashcard_artifacts import import_artifact, load_artifact, validate_artifact


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate or import an AKURU curated flashcard release.")
    parser.add_argument("action", choices=("validate", "import"))
    parser.add_argument("artifact")
    parser.add_argument("--admin-username")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    artifact = load_artifact(args.artifact)
    with SessionLocal() as db:
        if args.action == "validate":
            report = validate_artifact(db, artifact)
            report.pop("resolved", None)
        else:
            if not args.admin_username:
                parser.error("--admin-username is required for import")
            admin = db.scalar(select(User).where(User.username == args.admin_username, User.role == "admin", User.is_active.is_(True)))
            if not admin:
                parser.error("active Admin account not found")
            report = import_artifact(db, artifact, admin, release=args.release, dry_run=args.dry_run)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
