"""Unlettered questions retain their source identity in Tutor practice."""
import copy
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.models import OfficialPaperReviewQuestion, OfficialPaperReviewWorkspace
from app.schemas.tutor_past_papers import ReleasePastPaperPart
from app.services import tutor_past_papers as service
from test_auth_integration import auth_client  # noqa: F401
from test_tutor_past_papers import _ready, _login_student


@pytest.mark.parametrize('label', ['', 'a', 'b(ii)'])
def test_release_contract_preserves_actual_source_labels(label):
    assert ReleasePastPaperPart(partLabel=label, revision=1, confirmSelfContained=True).partLabel == label


def test_release_contract_still_requires_label_and_limits_length():
    with pytest.raises(ValidationError):
        ReleasePastPaperPart(revision=1, confirmSelfContained=True)
    with pytest.raises(ValidationError):
        ReleasePastPaperPart(partLabel='x' * 41, revision=1, confirmSelfContained=True)


@pytest.mark.parametrize('number,label,expected', [('5', '', '5'), ('2', 'b(ii)', '2(b(ii))')])
def test_whole_question_display(number, label, expected):
    assert service.question_label(number, label) == expected


@pytest.mark.integration
def test_whole_question_release_and_student_reveal_keep_permissions(auth_client, monkeypatch):
    client, headers, db, root, child, topic, paper, scheme, settings = _ready(auth_client, monkeypatch)
    workspace = db.scalar(select(OfficialPaperReviewWorkspace).where(
        OfficialPaperReviewWorkspace.paper_document_id == paper[0].id))
    question = db.scalar(select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id == workspace.id,
        OfficialPaperReviewQuestion.number == '1'))
    data = copy.deepcopy(question.review_data)
    assert len(data['parts']) == 1
    data['parts'][0]['label'] = ''
    question.review_data = data
    db.commit()
    payload = {'partLabel': '', 'revision': question.revision, 'confirmSelfContained': True}
    path = root + '/questions/1/chat-release'
    assert client.post(path, json=payload).status_code == 403
    assert client.post(path, headers=headers, json={**payload, 'confirmSelfContained': False}).status_code == 409
    assert client.post(path, headers=headers, json={**payload, 'revision': question.revision + 1}).status_code == 409
    result = client.post(path, headers=headers, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()['partLabel'] == ''
    assert client.post(path, headers=headers, json=payload).json() == result.json()
    assert len(service.eligible(db, child.id, 'chemistry')) == 1
    sh, ref = _login_student(client, child, topic)
    monkeypatch.setattr('app.services.tutor_agent._invoke', lambda *a, **kw: pytest.fail('No model call needed'))
    turns = f'/api/v1/tutoring/sessions/{ref}/agent-turns'
    selected = client.post(turns, headers=sh, json={
        'message': 'Ask me an igcse past paper question', 'requestKey': uuid.uuid4().hex})
    assert selected.status_code == 200, selected.text
    state = selected.json()['pastPaper']
    assert state['questionLabel'] == '1'
    assert state['practice']['question']['rubric'] is None
    assert state['markingGuidance'] == []
    revealed = client.post(turns, headers=sh, json={
        'message': 'Show approved answer', 'requestKey': uuid.uuid4().hex})
    assert revealed.status_code == 200, revealed.text
    assert revealed.json()['pastPaper']['questionLabel'] == '1'
    assert revealed.json()['pastPaper']['markingGuidance']
