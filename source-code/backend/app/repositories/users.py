import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import AuthSession, LoginThrottle, StudentProfile, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def by_username(self, username: str) -> User | None:
        return self.db.execute(select(User).where(User.username == username)).scalar_one_or_none()

    def username_exists(self, username: str) -> bool:
        return self.db.execute(select(User.id).where(User.username == username)).scalar_one_or_none() is not None

    def user(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def profile(self, student_id: uuid.UUID) -> StudentProfile | None:
        return self.db.get(StudentProfile, student_id)

    def throttle(self, key: str) -> LoginThrottle | None:
        return self.db.get(LoginThrottle, key)

    def expired_sessions(self, user_id: uuid.UUID, now) -> None:
        self.db.execute(delete(AuthSession).where((AuthSession.user_id == user_id) & (AuthSession.expires_at <= now)))

    def revoke_other_sessions(self, user_id: uuid.UUID, current_session_id: uuid.UUID) -> None:
        self.db.execute(delete(AuthSession).where(
            (AuthSession.user_id == user_id) & (AuthSession.id != current_session_id)
        ))

    def revoke_all_sessions(self, user_id: uuid.UUID) -> int:
        return self.db.execute(delete(AuthSession).where(AuthSession.user_id == user_id)).rowcount or 0

    def portal_accounts(self) -> list[User]:
        return list(self.db.execute(
            select(User).where(User.role.in_(("parent", "student"))).order_by(User.display_name)
        ).scalars())
