import argparse
import getpass

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first AKURU administrator")
    parser.add_argument("--username", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    username = args.username.strip().lower()
    password = getpass.getpass("New admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if len(password) < 12 or len(password) > 200 or password != confirm:
        raise SystemExit("Passwords must match and contain 12 to 200 characters.")
    with SessionLocal.begin() as db:
        if db.execute(select(User).where(User.username == username)).scalar_one_or_none():
            raise SystemExit("That username already exists.")
        db.add(User(
            username=username,
            display_name=args.name.strip(),
            role="admin",
            password_hash=hash_password(password),
            must_change_password=True,
        ))
    print(f"Created administrator: {username}")


if __name__ == "__main__":
    main()
