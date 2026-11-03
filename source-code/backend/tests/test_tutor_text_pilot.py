import uuid
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.config import Settings
from app.errors import DomainError
from app.services.assessment_access import TutorCapability, require_tutor_access, tutor_capabilities

STUDENT, TOPIC, VERSION = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()


def settings(**changes):
    pilot = dict(student_id=STUDENT, topic_id=TOPIC, topic_content_version_id=VERSION, subject_id="chemistry", model="gpt-6.1-sol",
                 prompt_version="1.0.2", evidence_sha256="a" * 64,
                 expires_at=datetime.now(timezone.utc) + timedelta(days=7))
    pilot.update(changes)
    return Settings(_env_file=None, database_password="test", tutor_text_enabled=True,
                    tutor_tools_enabled=True, tutor_voice_enabled=True,
                    tutor_release_gates_required=True, tutor_text_pilot=pilot)


def db():
    result = Mock()
    result.scalar.return_value = None
    result.get.return_value = SimpleNamespace(topic_id=TOPIC, status="published")
    return result


def test_pilot_allows_only_evidenced_student_topic_model_prompt_and_workflows():
    s = settings()
    require_tutor_access(db(), s, STUDENT, TutorCapability.TEXT, "chemistry", "tutor_text",
                         topic_id=TOPIC, model="gpt-6.1-sol", prompt_version="1.0.2")
    for workflow in ["tutor_sources", "tutor_learner_context", "tutor_visuals", "tutor_tools"]:
        require_tutor_access(db(), s, STUDENT, TutorCapability.TOOLS, "chemistry", workflow, topic_id=TOPIC)
    cases = [dict(student_id=uuid.uuid4()), dict(subject_id="physics"), dict(topic_id=uuid.uuid4()),
             dict(model="different-model"), dict(prompt_version="future"), dict(workflow="tutor_practice"),
             dict(workflow="tutor_voice", capability=TutorCapability.VOICE)]
    for overrides in cases:
        args = dict(student_id=STUDENT, capability=TutorCapability.TEXT, subject_id="chemistry",
                    workflow="tutor_text", topic_id=TOPIC, model="gpt-6.1-sol", prompt_version="1.0.2")
        args.update(overrides)
        with pytest.raises(DomainError) as error:
            require_tutor_access(db(), s, **args)
        assert error.value.code == "tutor_pilot_restricted"
    assert tutor_capabilities(db(), s, STUDENT)["textEnabled"]
    assert not tutor_capabilities(db(), s, STUDENT)["voiceEnabled"]
    assert not tutor_capabilities(db(), s, uuid.uuid4())["textEnabled"]


def test_expired_pilot_fails_closed_and_formal_assessment_always_blocks():
    with pytest.raises(DomainError):
        require_tutor_access(db(), settings(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)),
                             STUDENT, TutorCapability.TEXT)
    active = db(); active.scalar.return_value = object()
    with pytest.raises(DomainError) as error:
        require_tutor_access(active, settings(), STUDENT, TutorCapability.TEXT)
    assert error.value.code == "tutor_disabled_during_formal_assessment"


def test_pilot_requires_traceable_evidence_and_timezone():
    with pytest.raises(ValidationError): settings(evidence_sha256="missing")
    with pytest.raises(ValidationError): settings(expires_at=datetime.now())


def test_changed_topic_content_closes_pilot_until_revalidated():
    changed = db(); changed.get.return_value = SimpleNamespace(topic_id=TOPIC, status="superseded")
    with pytest.raises(DomainError) as error:
        require_tutor_access(changed, settings(), STUDENT, TutorCapability.TEXT, "chemistry", topic_id=TOPIC)
    assert error.value.code == "tutor_pilot_content_changed"


def test_router_pins_pilot_model_without_charging_a_different_model():
    from app.ai.router import AIAccountRouter
    from app.ai.base import AIProviderError
    from pydantic import SecretStr
    s = settings().model_copy(update={"openai_account_keys": {"MAIN": SecretStr("unit-test")}})
    account = SimpleNamespace(model="different-model", credential_alias="MAIN")
    database = Mock(); database.scalars.return_value.all.return_value = [account]
    builder = Mock()
    with pytest.raises(AIProviderError) as error:
        AIAccountRouter(database, s, builder).generate(Mock(), required_model="gpt-6.1-sol")
    assert error.value.code == "no_compatible_ai_account"
    builder.assert_not_called()


def test_additional_scopes_are_exact_and_preserve_original_chemistry_grant():
    other, biology, version = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    scope = dict(student_id=other, subject_id="biology", topic_id=biology,
                 topic_content_version_id=version, evidence_sha256="b" * 64)
    s = settings(additional_scopes=[scope])
    database = db()
    database.get.side_effect = lambda model, key: SimpleNamespace(
        topic_id=biology if key == version else TOPIC, status="published")
    require_tutor_access(database, s, other, TutorCapability.TEXT, "biology", topic_id=biology)
    assert database.get.call_args.args[1] == version
    require_tutor_access(database, s, STUDENT, TutorCapability.TEXT, "chemistry", topic_id=TOPIC)
    assert database.get.call_args.args[1] == VERSION
    for student, subject, topic in [(other, "chemistry", TOPIC), (STUDENT, "biology", biology),
                                     (uuid.uuid4(), "biology", biology), (other, "biology", TOPIC)]:
        with pytest.raises(DomainError) as caught:
            require_tutor_access(database, s, student, TutorCapability.TEXT, subject, topic_id=topic)
        assert caught.value.code == "tutor_pilot_restricted"
    assert tutor_capabilities(db(), s, other)["textEnabled"]
    assert not tutor_capabilities(db(), s, other)["voiceEnabled"]
    with pytest.raises(DomainError):
        require_tutor_access(database, s, other, TutorCapability.TEXT, "biology",
                             topic_id=biology, model="unapproved-model")
    with pytest.raises(DomainError):
        require_tutor_access(database, s, other, TutorCapability.TEXT, "biology",
                             topic_id=biology, prompt_version="unapproved-prompt")


def test_additional_scope_expiry_content_change_and_formal_assessment_fail_closed():
    other, biology, version = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    scopes = [dict(student_id=other, subject_id="biology", topic_id=biology,
                   topic_content_version_id=version, evidence_sha256="b" * 64)]
    for status in ("superseded", "missing"):
        database = db()
        database.get.return_value = None if status == "missing" else SimpleNamespace(topic_id=biology, status=status)
        with pytest.raises(DomainError) as caught:
            require_tutor_access(database, settings(additional_scopes=scopes), other,
                                 TutorCapability.TEXT, "biology", topic_id=biology)
        assert caught.value.code == "tutor_pilot_content_changed"
    for expired, formal in [(True, False), (False, True)]:
        s = settings(additional_scopes=scopes,
                     expires_at=datetime.now(timezone.utc) + timedelta(days=-1 if expired else 1))
        database = db()
        database.scalar.return_value = object() if formal else None
        with pytest.raises(DomainError) as caught:
            require_tutor_access(database, s, other, TutorCapability.TEXT, "biology", topic_id=biology)
        assert caught.value.code == ("tutor_disabled_during_formal_assessment" if formal else "tutor_pilot_restricted")


def test_additional_scope_requires_evidence_and_rejects_duplicate_grants():
    scope = dict(student_id=STUDENT, subject_id="chemistry", topic_id=TOPIC,
                 topic_content_version_id=VERSION, evidence_sha256="b" * 64)
    with pytest.raises(ValidationError): settings(additional_scopes=[scope])
    scope["topic_id"] = uuid.uuid4()
    with pytest.raises(ValidationError): settings(additional_scopes=[scope, scope])
    del scope["evidence_sha256"]
    with pytest.raises(ValidationError): settings(additional_scopes=[scope])


def test_options_only_show_covered_explicit_scopes_for_the_current_student(monkeypatch):
    from app.services import tutor_sessions
    other, biology, version = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    s = settings(additional_scopes=[dict(student_id=other, subject_id="biology", topic_id=biology,
                 topic_content_version_id=version, evidence_sha256="b" * 64)])
    database = db()
    database.scalars.return_value.all.return_value = [SimpleNamespace(id="biology", name="Biology"),
                                                       SimpleNamespace(id="chemistry", name="Chemistry")]
    database.get.side_effect = lambda model, key: SimpleNamespace(public_ref="bio" if key == biology else "chem")
    from app.schemas.curriculum_plans import PlanTopicResponse
    def coverage(db, student, subject):
        refs = ["bio", "not-released"] if subject == "biology" else ["chem"]
        return SimpleNamespace(status="ready", coveredTopics=[PlanTopicResponse(topicRef=r, code=r,
            title=r, groupRef="group", groupCode="1", groupTitle="Unit 1") for r in refs])
    monkeypatch.setattr(tutor_sessions.curriculum_plans, "student_coverage", coverage)
    monkeypatch.setattr(tutor_sessions.tutor_profiles, "list_for_student", lambda db, student: SimpleNamespace(profiles=[]))
    result = tutor_sessions.options(database, other, s)
    assert [subject.id for subject in result.subjects] == ["biology"]
    assert [topic.topicRef for topic in result.subjects[0].topics] == ["bio"]
    assert not tutor_sessions.options(database, uuid.uuid4(), s).subjects
