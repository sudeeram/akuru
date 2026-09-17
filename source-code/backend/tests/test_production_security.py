from types import SimpleNamespace

from app.ai.prompts import PROMPTS
from app.config import Settings
from app.rate_limit import RequestRateLimiter
from app.services.usage_limits import pseudonymous_student_id
from app.malware import scan
from app.errors import DomainError
import pytest
from app.main import _request_body_limit, app


def test_prompt_boundaries_treat_student_and_source_instructions_as_untrusted():
    assert all("untrusted" in prompt.instructions.lower() for prompt in PROMPTS.values())
    assert "never as instructions" in PROMPTS["assessment"].instructions.lower()


def test_pseudonym_does_not_expose_student_identifier():
    settings = Settings(database_password="private-secret", _env_file=None)
    learner = "11111111-1111-1111-1111-111111111111"
    reference = pseudonymous_student_id(settings, learner)
    assert reference == pseudonymous_student_id(settings, learner)
    assert learner not in reference and len(reference) == 24


def test_local_api_rate_limit_fails_after_configured_limit():
    settings = Settings(database_password="secret", api_rate_limit_per_minute=10, _env_file=None)
    limiter = RequestRateLimiter(settings)
    request = SimpleNamespace(url=SimpleNamespace(path="/api/v1/catalog"), client=SimpleNamespace(host="192.0.2.10"), headers={})
    results = [limiter.check(request)[0] for _ in range(11)]
    assert results[:10] == [True] * 10 and results[-1] is False


def test_topic_document_upload_uses_the_document_body_limit():
    topic_path = "/api/v1/admin/textbooks/book_example/topics/topic_example/documents"
    assert _request_body_limit(topic_path) == 50 * 1024 * 1024
    assert _request_body_limit(f"{topic_path}/batch") == 1_000_000
    assert _request_body_limit("/api/v1/admin/textbooks/book_example") == 1_000_000


def test_malicious_upload_is_rejected_without_storing_content(monkeypatch):
    monkeypatch.setattr("app.malware.subprocess.run", lambda *args, **kwargs: SimpleNamespace(returncode=1))
    settings = Settings(database_password="secret", malware_scan_command="clamscan", _env_file=None)
    with pytest.raises(DomainError) as error:
        scan(b"malicious-test-content", settings)
    assert error.value.code == "malicious_file"


def _dependency_names(dependant):
    names = {getattr(dependency.call, "__name__", "") for dependency in dependant.dependencies}
    for dependency in dependant.dependencies:
        names |= _dependency_names(dependency)
    return names


def test_every_private_api_endpoint_has_authentication_and_mutations_have_csrf():
    def walk(items):
        for item in items:
            if hasattr(item, "original_router"):
                yield from walk(item.original_router.routes)
            elif hasattr(item, "routes"):
                yield from walk(item.routes)
            else:
                yield item
    api_container = next(item for item in app.routes if getattr(getattr(item, "original_router", None), "prefix", "") == "/api/v1")
    routes = [route for route in walk(api_container.original_router.routes) if hasattr(route, "dependant")]
    assert routes
    for route in routes:
        names = _dependency_names(route.dependant)
        if route.path == "/auth/login":
            continue
        assert "get_principal" in names, f"{route.path} lacks authenticated principal"
        if route.methods & {"POST", "PUT", "PATCH", "DELETE"}:
            assert "require_csrf" in names, f"{route.path} lacks CSRF validation"
