from contextlib import contextmanager

from app import bootstrap_admin


class _QueryResult:
    def scalar_one_or_none(self):
        return None


class _Session:
    def __init__(self) -> None:
        self.created_user = None

    def execute(self, _statement):
        return _QueryResult()

    def add(self, user) -> None:
        self.created_user = user


def test_bootstrapped_admin_must_replace_the_initial_password(monkeypatch) -> None:
    session = _Session()

    @contextmanager
    def begin():
        yield session

    monkeypatch.setattr(bootstrap_admin.SessionLocal, "begin", begin)
    monkeypatch.setattr(bootstrap_admin.getpass, "getpass", lambda _prompt: "temporary secure password")
    monkeypatch.setattr(bootstrap_admin, "hash_password", lambda _password: "hashed")
    monkeypatch.setattr(
        "sys.argv",
        ["bootstrap_admin", "--username", "Initial-Admin", "--name", "Initial Administrator"],
    )

    bootstrap_admin.main()

    assert session.created_user.username == "initial-admin"
    assert session.created_user.role == "admin"
    assert session.created_user.must_change_password is True
