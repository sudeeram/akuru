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
