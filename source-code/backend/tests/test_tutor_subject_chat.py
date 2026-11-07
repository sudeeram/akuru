"""Subject sessions and follow-up context must retain the same access boundaries."""
import json
import uuid
from types import SimpleNamespace as Row
from unittest.mock import Mock

import pytest
from sqlalchemy import select
from app.errors import DomainError
from app.models import TutorSession, TextbookTopic, TextbookTopicContentVersion, CurriculumPlan, CurriculumPlanTopic
from app.services import tutor_conversation as conversation, tutor_sources
from app.schemas.tutor_sessions import TutorSessionStartRequest
from test_auth_integration import auth_client  # noqa: F401


def turn(role, content, **data):
    return Row(role=role, content=content, response_data=data)


@pytest.mark.parametrize('message', ['Why does it happen faster when heated?', 'Can you explain that?',
    'How are they different?', 'Give me another example', 'What does that mean?', 'Why?',
    'What is its function?', 'How does this differ from osmosis?'])
def test_follow_up_retrieval_includes_the_tutors_antecedent(message):
    history = [turn('student', 'What happens during evaporation?'),
               turn('assistant', 'Fast particles escape from the liquid surface during evaporation.')]
    query, strategy = conversation.resolve(message, history)
    assert strategy == 'own_session_conversation_follow_up'
    assert 'evaporation' in query and 'Fast particles escape' in query
    assert query.endswith(message)


def test_explicit_topic_change_ignores_old_retrieval_context_and_context_is_bounded():
    history = [turn('student', 'Explain evaporation.'), turn('assistant', 'liquid ' * 5000)]
    for message in ['What is mitosis?', 'And what is freezing?', 'Explain photosynthesis', 'Explain photosynthesis and how it occurs']:
        assert conversation.resolve(message, history) == (message, 'direct')
    assert sum(len(t['content']) for t in conversation.bounded_history(history * 100)) <= 4800
    assert len(conversation.resolve('Why?', history * 100)[0]) < 6000
    for basis in ['outside_scope', 'uncertain', 'clarification']:
        assert conversation.resolve('What does that mean?', history + [turn('assistant', 'Please clarify.', answerBasis=basis)])[1] == 'direct'


def test_request_schema_preserves_legacy_default_and_rejects_unknown_scope():
    payload = dict(subjectId='biology', profileRef='profile_test', requestKey='request_test')
    assert TutorSessionStartRequest(**payload).chatScope == 'topic'
    assert TutorSessionStartRequest(**payload, chatScope='subject').topicRef is None
    with pytest.raises(ValueError): TutorSessionStartRequest(**payload, chatScope='everything')


def test_subject_citation_opening_reauthorizes_exact_topic_version(monkeypatch):
    topic_id, version_id = uuid.uuid4(), uuid.uuid4()
    session = Row(chat_scope='subject')
    monkeypatch.setattr(tutor_sources, '_session', lambda *a: session)
    monkeypatch.setattr(tutor_sources, 'authorized_topics', lambda *a: [(Row(id=topic_id), Row(id=version_id), None)])
    monkeypatch.setattr(tutor_sources, '_citation', lambda *a: 'authorized')
    chunk = Row(status='active', source_type='textbook_section', topic_id=topic_id, topic_content_version_id=version_id)
    db = Mock(); db.get.return_value = chunk
    assert tutor_sources.get_citation(db, None, None, 'own_session', 'citation_'+uuid.uuid4().hex) == 'authorized'
    for field in ['topic_id', 'topic_content_version_id']:
        original = getattr(chunk, field); setattr(chunk, field, uuid.uuid4())
        with pytest.raises(DomainError) as caught:
            tutor_sources.get_citation(db, None, None, 'own_session', 'citation_'+uuid.uuid4().hex)
        assert caught.value.status_code == 404
        setattr(chunk, field, original)


@pytest.mark.integration
def test_subject_start_scope_is_durable_owned_and_does_not_require_topic(auth_client, monkeypatch):
    from test_tutor_past_papers import _ready, _login_student
    client, _, db, _, child, topic, _, _, settings = _ready(auth_client, monkeypatch)
    headers, ref = _login_student(client, child, topic)
    original = client.get('/api/v1/tutoring/sessions').json()['sessions'][0]
    assert original['chatScope'] == 'topic'
    assert client.post(f'/api/v1/tutoring/sessions/{ref}/end',headers=headers,json={'requestKey':uuid.uuid4().hex}).status_code == 200
    payload = {'subjectId':'chemistry', 'chatScope':'subject', 'profileRef':original['currentTutor']['profileRef'], 'requestKey':uuid.uuid4().hex}
    result = client.post('/api/v1/tutoring/sessions', headers=headers, json=payload)
    assert result.status_code == 201, result.text
    data = result.json(); assert data['chatScope'] == 'subject' and data['activeTopic']['topicRef'] == topic.public_ref
    assert client.post('/api/v1/tutoring/sessions',headers=headers,json=payload).json()['sessionRef'] == data['sessionRef']
    assert db.scalar(select(TutorSession).where(TutorSession.public_ref == data['sessionRef'])).chat_scope == 'subject'
    # Entirely different subject has no enrolment/coverage; it cannot be selected.
    assert client.post(f"/api/v1/tutoring/sessions/{data['sessionRef']}/end",headers=headers,json={'requestKey':uuid.uuid4().hex}).status_code == 200
    bad = {**payload, 'subjectId':'physics', 'requestKey':uuid.uuid4().hex}
    assert client.post('/api/v1/tutoring/sessions',headers=headers,json=bad).status_code in {403,409,422}
    no_topic = {**payload, 'chatScope':'topic', 'requestKey':uuid.uuid4().hex}
    assert client.post('/api/v1/tutoring/sessions',headers=headers,json=no_topic).status_code == 422
    client.post('/api/v1/auth/logout',headers=headers)
    assert client.get('/api/v1/tutoring/sessions').status_code == 401


@pytest.mark.integration
def test_subject_search_crosses_topics_but_topic_search_and_withdrawal_fail_closed(auth_client, monkeypatch):
    from test_tutor_past_papers import _ready, _login_student
    from test_official_paper_review_workspace import _source
    from app.models import User, RetrievalChunk
    from app.services.embeddings import embed_texts
    client, _, db, _, child, first, _, _, settings = _ready(auth_client, monkeypatch)
    admin = db.scalar(select(User).where(User.role == 'admin'))
    second = TextbookTopic(textbook_id=first.textbook_id, group_id=first.group_id, course_id='igcse',
        subject_id='chemistry', code='second', title='Elements and mixtures', sequence=2,status='published')
    db.add(second); db.flush()
    v2=TextbookTopicContentVersion(topic_id=second.id,version_number=1,status='published',source_manifest=[],extraction_manifest={},published_by=admin.id)
    db.add(v2); db.flush()
    plan=db.scalar(select(CurriculumPlan).where(CurriculumPlan.subject_id=='chemistry',CurriculumPlan.status=='published'))
    db.add(CurriculumPlanTopic(plan_id=plan.id,topic_id=second.id,grade=10,term=1))
    text='Chromatography separates soluble dyes because they have different solubilities.'
    source=_source(db,admin,uuid.uuid4().hex,'textbook')
    source[0].review_state='published'; source[3].block_kind='paragraph'; source[3].needs_review=False
    source[3].text=text
    chunk=RetrievalChunk(document_id=source[0].id,document_version_id=source[1].id,
        topic_id=second.id,topic_content_version_id=v2.id,group_id=second.group_id,course_id='igcse',subject_id='chemistry',
        source_type='textbook_section',source_item_id=source[3].id,source_ordinal=1,content=text,page_number=1,
        bounding_box={},content_hash='a'*64,embedding_model='local',embedding=embed_texts(settings,[text])[0])
    db.add(chunk); db.commit()
    headers,ref=_login_student(client,child,first)
    endpoint=f'/api/v1/tutoring/sessions/{ref}'
    query={'query':'Explain chromatography and soluble dyes'}
    assert client.post(endpoint+'/sources/search',headers=headers,json=query).json()['citations']==[]
    row=db.scalar(select(TutorSession).where(TutorSession.public_ref==ref)); row.chat_scope='subject'; db.commit()
    result=client.post(endpoint+'/sources/search',headers=headers,json=query)
    assert result.status_code==200,result.text
    citations=result.json()['citations']; assert len(citations)==1
    assert citations[0]['topicRef']==second.public_ref and citations[0]['topicTitle']==second.title
    assert client.get(endpoint+'/sources/'+citations[0]['citationRef']).status_code==200
    nearby=client.get(endpoint+'/sources/'+citations[0]['citationRef']+'/context')
    assert nearby.status_code==200,nearby.text
    # Real agent pipeline, deterministic provider: no API tokens are used.
    from app.ai.base import AIResult, AIUsage
    from app.services import tutor_agent
    captured = []
    def provider(*args):
        data=json.loads(args[3].task); captured.append(data)
        assert data['scope']['chatScope']=='subject'
        assert 'practiceFocus' in data['scope'] and 'activeTopic' not in data['scope']
        refs=[c['citationRef'] for c in data['approvedCitations']]
        assert refs
        return AIResult(output={'content':'Chromatography separates soluble dyes by differences in solubility.',
            'citationRefs':refs,'followUpChoices':[],'proposedSignals':[]},provider='test',model='test-model',
            response_id=None,usage=AIUsage(1,1,2),latency_ms=1,attempt_count=1)
    monkeypatch.setattr(tutor_agent,'_invoke',provider)
    for message in ['Explain chromatography and soluble dyes', 'Why does it separate them?']:
        reply=client.post(endpoint+'/agent-turns',headers=headers,json={'message':message,'requestKey':uuid.uuid4().hex})
        assert reply.status_code==200,reply.text
        assert reply.json()['citations'][0]['topicRef']==second.public_ref
    assert captured[-1]['conversationContext']['strategy']=='own_session_conversation_follow_up'
    assert any(t['role']=='assistant' for t in captured[-1]['recentTranscript'])
    db.query(CurriculumPlanTopic).filter_by(plan_id=plan.id,topic_id=second.id).delete(); db.commit()
    assert client.get(endpoint+'/sources/'+citations[0]['citationRef']).status_code==404
    assert client.post(endpoint+'/sources/search',headers=headers,json=query).json()['citations']==[]
