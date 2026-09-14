import uuid
from unittest.mock import Mock

import pytest

from app.config import Settings
from app.errors import DomainError
from app.services.assessment_access import (
    TutorCapability,
    is_formal_assessment,
    require_practice_assistance,
    require_tutor_access,
    tutor_capabilities,
)


def _settings(**overrides) -> Settings:
    return Settings(database_password="test", _env_file=None, **overrides)


def _db(active_assessment=None) -> Mock:
    db = Mock()
    db.scalar.return_value = active_assessment
    return db


def test_assessment_modes_fail_closed_and_only_practice_allows_help() -> None:
    assert is_formal_assessment("mock") is True
    assert is_formal_assessment("official_paper") is True
    assert is_formal_assessment("practice") is False
    require_practice_assistance("practice")
    with pytest.raises(DomainError) as existing_hint:
        require_practice_assistance("mock")
    assert existing_hint.value.code == "hints_disabled"
    for mode in ("mock", "official_paper"):
        with pytest.raises(DomainError) as caught:
            require_practice_assistance(mode, assistance="Tutor hints and voice")
        assert caught.value.code == "assistance_disabled_during_formal_assessment"
        assert caught.value.status_code == 403
    with pytest.raises(DomainError) as unknown:
        require_practice_assistance("future_mode")
    assert unknown.value.code == "unknown_assessment_mode"


def test_tutor_features_default_to_disabled_and_do_not_expose_credentials() -> None:
    settings = _settings()
    assert settings.tutor_text_enabled is False
    assert settings.tutor_voice_enabled is False
    assert settings.tutor_tools_enabled is False
    result = tutor_capabilities(_db(), settings, uuid.uuid4())
    assert result == {
        "textEnabled": False,
        "voiceEnabled": False,
        "toolsEnabled": False,
        "blockedReason": None,
    }


def test_live_formal_assessment_blocks_every_enabled_tutor_capability() -> None:
    settings = _settings(
        tutor_text_enabled=True,
        tutor_voice_enabled=True,
        tutor_tools_enabled=True,
    )
    db = _db(active_assessment=object())
    student_id = uuid.uuid4()
    capabilities = tutor_capabilities(db, settings, student_id)
    assert capabilities == {
        "textEnabled": False,
        "voiceEnabled": False,
        "toolsEnabled": False,
        "blockedReason": "formal_assessment_active",
    }
    for capability in TutorCapability:
        with pytest.raises(DomainError) as caught:
            require_tutor_access(db, settings, student_id, capability)
        assert caught.value.code == "tutor_disabled_during_formal_assessment"
        assert caught.value.status_code == 403


def test_enabled_tutor_capabilities_are_available_without_a_formal_attempt() -> None:
    settings = _settings(
        tutor_text_enabled=True,
        tutor_voice_enabled=True,
        tutor_tools_enabled=True,
    )
    db = _db()
    student_id = uuid.uuid4()
    for capability in TutorCapability:
        require_tutor_access(db, settings, student_id, capability)
    assert tutor_capabilities(db, settings, student_id)["blockedReason"] is None


def test_disabled_tutor_feature_fails_before_provider_or_session_work() -> None:
    with pytest.raises(DomainError) as caught:
        require_tutor_access(_db(), _settings(), uuid.uuid4(), TutorCapability.VOICE)
    assert caught.value.code == "tutor_feature_disabled"
    assert caught.value.status_code == 403
