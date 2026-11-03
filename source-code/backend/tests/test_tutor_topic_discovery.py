from types import SimpleNamespace as Row
from unittest.mock import Mock
import uuid

import pytest

from app.errors import DomainError
from app.services import tutor_topic_discovery as discovery

QUERY = 'I have learnt about Viruses. Can you tell me which topic or topics it could belong to'


def record(text, kind='paragraph', page=29):
    return (Row(content=text, page_number=page, source_ordinal=1), Row(block_kind=kind),
            Row(page_number=page, printed_page_label=str(page), page_metadata={}))


def test_natural_location_intent_and_teaching_are_distinct():
    for message in [QUERY, 'Which topic covers osmosis?', 'Where are viruses taught?',
                    'Find the topic about viruses', 'What chapter covers enzymes?']:
        assert discovery.requested(message)
    for message in ['Explain viruses', 'What is a virus?', 'Can you ask me a past paper question?']:
        assert not discovery.requested(message)
    assert discovery.concept_terms(QUERY) == {'virus'}


def test_matching_is_grounded_and_ignores_exercises_and_answer_spaces():
    rows = [record('Viruses\nViruses reproduce only inside living host cells.'),
            record('Name two viruses.', 'question'), record('CHAPTER QUESTIONS\nDescribe viruses.'),
            record('Write virus here', 'answer_space'), record('Cells contain nuclei.')]
    matches = discovery.rank_records(QUERY, rows)
    assert len(matches) == 1 and matches[0][1].page_number == 29
    assert not discovery.rank_records('Which topic covers quantum teleportation?', rows)
    assert discovery.rank_records('Which topic covers viruses?', [record('A virus has a protein coat.')])


def setup(monkeypatch, denied=False):
    topic_id = uuid.uuid4()
    session = Row(public_ref='session_own', subject_id='biology', active_topic_id=uuid.uuid4())
    principal = Row(user=Row(id=uuid.uuid4()))
    item = Row(topicRef='topic_virus', groupCode='1', groupTitle='Organisms')
    monkeypatch.setattr(discovery.tutor_sources, '_session', Mock(return_value=session))
    monkeypatch.setattr(discovery.tutor_sessions, 'options', Mock(return_value=Row(subjects=[Row(id='biology', topics=[item]) ])))
    gate = Mock(side_effect=DomainError('tutor_pilot_restricted', 'Not permitted', 403) if denied else None)
    monkeypatch.setattr(discovery, 'require_tutor_access', gate)
    monkeypatch.setattr(discovery.tutor_sources, '_active_chunks', Mock(return_value=(None, Row(id=uuid.uuid4(), version_number=1), Row(title='Biology'))))
    monkeypatch.setattr(discovery.repository, 'save_exchange', Mock(return_value=Row(public_ref='turn_saved')))
    db = Mock()
    db.scalar.return_value = Row(id=topic_id, public_ref='topic_virus', code='2', title='Variety of Living Organisms')
    db.execute.return_value.all.return_value = [record('Viruses\nViruses use host cells.')]
    payload = Row(message=QUERY, requestKey='unique-request', teachingMode='explanation')
    return db, principal, session, payload, gate


def test_lookup_uses_current_student_and_subject_without_switching_or_paid_calls(monkeypatch):
    db, principal, session, payload, gate = setup(monkeypatch)
    original = session.active_topic_id
    response = discovery.handle(db, Row(), principal, session, payload)
    assert response.topicMatches[0].topicRef == 'topic_virus'
    assert response.topicMatches[0].pageReference == 'Page 29'
    assert response.provider == 'akuru'
    assert response.citations == []  # Cross-topic source URLs must not bypass the active-topic gate.
    assert session.active_topic_id == original
    assert discovery.tutor_sessions.options.call_args.args[1] == principal.user.id
    assert gate.call_args.args[2] == principal.user.id
    assert gate.call_args.args[4] == 'biology'
    # Both topic and content version are required in the query, as are reviewed blocks/documents.
    sql = str(db.execute.call_args.args[0])
    for required in ['topic_content_version_id', 'needs_review', 'removed_at', 'review_state']:
        assert required in sql


def test_restricted_topics_are_not_searched_or_exposed(monkeypatch):
    db, principal, session, payload, _ = setup(monkeypatch, denied=True)
    response = discovery.handle(db, Row(), principal, session, payload)
    assert not response.topicMatches
    assert 'accessible, published' in response.content
    db.execute.assert_not_called()


def test_session_access_failure_propagates(monkeypatch):
    db, principal, session, payload, _ = setup(monkeypatch)
    monkeypatch.setattr(discovery.tutor_sources, '_session', Mock(side_effect=DomainError('not_owned', 'No', 404)))
    with pytest.raises(DomainError):
        discovery.handle(db, Row(), principal, session, payload)
    db.execute.assert_not_called()


def test_unrelated_request_does_not_query_or_change_anything():
    db = Mock()
    assert discovery.handle(db, None, None, None, Row(message='Explain viruses')) is None
    assert not db.mock_calls


def test_unpublished_content_is_not_searched(monkeypatch):
    db, principal, session, payload, _ = setup(monkeypatch)
    monkeypatch.setattr(discovery.tutor_sources, '_active_chunks', Mock(return_value=(None, None, None)))
    assert not discovery.handle(db, Row(), principal, session, payload).topicMatches
    db.execute.assert_not_called()


def test_no_other_subjects_are_exposed(monkeypatch):
    db, principal, session, payload, _ = setup(monkeypatch)
    monkeypatch.setattr(discovery.tutor_sessions, 'options', Mock(return_value=Row(subjects=[Row(id='chemistry', topics=[Row(topicRef='private')])])))
    assert not discovery.handle(db, Row(), principal, session, payload).topicMatches
    db.execute.assert_not_called()


def test_long_evidence_excerpt_contains_the_matched_concept():
    assert 'Viruses' in discovery.evidence_excerpt('Introduction. ' * 100 + 'Viruses require host cells.', QUERY)


def test_agent_dispatches_discovery_before_topic_scoped_teaching(monkeypatch):
    from app.services import tutor_agent, tutor_past_papers
    from app.schemas.tutor_agent import TutorAgentTurnRequest
    db = Mock()
    session = Row(id=uuid.uuid4(), subject_id='biology', active_topic_id=uuid.uuid4())
    principal = Row(user=Row(id=uuid.uuid4()))
    monkeypatch.setattr(tutor_agent, 'require_tutor_access', Mock())
    monkeypatch.setattr(tutor_agent.tutor_sessions, '_owned_session', Mock(return_value=session))
    monkeypatch.setattr(tutor_agent.tutor_sessions, '_require_active', Mock())
    monkeypatch.setattr(tutor_agent.repository, 'replay', Mock(return_value=None))
    monkeypatch.setattr(tutor_agent, '_record_safety', Mock())
    answer = Row(content='Topic 2')
    lookup = Mock(return_value=answer)
    monkeypatch.setattr(discovery, 'handle', lookup)
    paper = Mock()
    monkeypatch.setattr(tutor_past_papers, 'handle', paper)
    generator = Mock()
    result = tutor_agent.complete_turn(db, Row(), principal, 'own_session',
        TutorAgentTurnRequest(message=QUERY, requestKey='request-key-discovery'), generator)
    assert result is answer
    assert lookup.call_args.args[2] is principal
    assert lookup.call_args.args[3] is session
    generator.assert_not_called()
    paper.assert_not_called()
