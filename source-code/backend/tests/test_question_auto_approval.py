"""AI decisions require current confidence, complete review and server authority."""
import copy
import pytest
from sqlalchemy import select
from app.models import OfficialPaperReviewQuestion
from test_auth_integration import auth_client  # noqa
from test_official_question_analyses import setup_analysis


def pending(auth_client):
    client, headers, db, root, q, payload = setup_analysis(auth_client)
    row = db.scalar(select(OfficialPaperReviewQuestion))
    row.status = 'unreviewed'
    data = copy.deepcopy(row.review_data)
    for part in data['parts']: part['status'] = 'unreviewed'
    row.review_data = data
    db.commit()
    return client, headers, db, root, q, payload


@pytest.mark.integration
@pytest.mark.parametrize('percent,expected', [(75, 'unreviewed'), (76, 'ai_approved'), (95, 'ai_approved')])
def test_strict_threshold_and_idempotent_batch(auth_client, percent, expected):
    client, headers, db, root, q, payload = pending(auth_client)
    payload['question']['percent'] = percent
    for part in payload['parts']: part['percent'] = percent
    result = client.post(root + '/questions/1/analyses', headers=headers, json=payload)
    assert result.status_code == 201, result.text
    after = client.get(root).json()['questions'][0]
    assert after['status'] == expected
    assert after['data']['parts'][0]['status'] == expected
    assert client.post(root + '/auto-approval', json={}).status_code == 403
    applied = client.post(root + '/auto-approval', headers=headers, json={})
    assert applied.status_code == 200, applied.text
    assert not applied.json()['results'][0]['changed']
    assert client.get(root).json()['questions'][0]['revision'] == after['revision']


@pytest.mark.integration
def test_lower_analysis_revokes_ai_approval(auth_client):
    client, headers, db, root, q, payload = pending(auth_client)
    assert client.post(root + '/questions/1/analyses', headers=headers, json=payload).status_code == 201
    current = client.get(root).json()['questions'][0]
    payload.update(expectedQuestionRevision=current['revision'], expectedAnalysisVersion=1)
    payload['parts'][0]['percent'] = 70
    result = client.post(root + '/questions/1/analyses', headers=headers, json=payload)
    assert result.status_code == 201, result.text
    assert client.get(root).json()['questions'][0]['status'] == 'unreviewed'


@pytest.mark.integration
@pytest.mark.parametrize('decision', ['approved', 'excluded', 'needs_correction'])
def test_human_decisions_preserved(auth_client, decision):
    client, headers, db, root, q, payload = setup_analysis(auth_client)
    row = db.scalar(select(OfficialPaperReviewQuestion))
    row.status = decision
    db.commit()
    assert client.post(root + '/questions/1/analyses', headers=headers, json=payload).status_code == 201
    assert client.get(root).json()['questions'][0]['status'] == decision


@pytest.mark.integration
def test_incomplete_and_stale_evidence_block_approval(auth_client):
    client, headers, db, root, q, payload = pending(auth_client)
    row = db.scalar(select(OfficialPaperReviewQuestion))
    data = copy.deepcopy(row.review_data)
    data['parts'][0].update(coverage='unreviewed', topicRefs=[])
    row.review_data = data
    db.commit()
    result = client.post(root + '/questions/1/analyses', headers=headers, json=payload)
    assert result.status_code == 201, result.text
    assert client.get(root).json()['questions'][0]['status'] == 'unreviewed'
    applied = client.post(root + '/auto-approval', headers=headers, json={}).json()
    assert 'coverage' in applied['results'][0]['reason']
    data['prompt'] = 'Changed after comparison'
    row.review_data = copy.deepcopy(data)
    db.commit()
    assert not client.get(root).json()['questions'][0]['accuracyAnalysis']['isCurrent']
    assert client.post(root + '/auto-approval', headers=headers, json={}).json()['results'][0]['status'] == 'unreviewed'


@pytest.mark.integration
def test_client_cannot_assign_ai_status(auth_client):
    client, headers, db, root, q, payload = pending(auth_client)
    body = dict(number='1', expectedRevision=q['revision'], status='ai_approved', data=q['data'])
    assert client.post(root + '/questions', headers=headers, json=body).status_code == 422


@pytest.mark.integration
def test_stale_ai_approval_is_not_counted_or_shown_as_approved(auth_client):
    client, headers, db, root, q, payload = pending(auth_client)
    assert client.post(root + '/questions/1/analyses', headers=headers, json=payload).status_code == 201
    row = db.scalar(select(OfficialPaperReviewQuestion))
    row.review_data = {**row.review_data, 'prompt': 'Changed source wording'}
    db.commit()
    review = client.get(root).json()
    assert review['approvedCount'] == 0
    assert review['questions'][0]['status'] == 'unreviewed'
    assert review['questions'][0]['data']['parts'][0]['status'] == 'unreviewed'
    assert not review['wholePaperReady']
    assert client.post(root + '/auto-approval', headers=headers, json={}).json()['results'][0]['changed']


@pytest.mark.integration
def test_unapproved_visual_does_not_get_bypassed(auth_client):
    client, headers, db, root, q, payload = pending(auth_client)
    from app.models import DocumentAsset
    row = db.scalar(select(OfficialPaperReviewQuestion))
    import uuid
    asset = db.get(DocumentAsset, uuid.UUID(row.review_data['visualAssetIds'][0]))
    asset.asset_metadata = {**asset.asset_metadata, 'reviewApproved': False}
    db.commit()
    payload['expectedContentHash'] = client.get(root).json()['questions'][0]['analysisContentHash']
    assert client.post(root + '/questions/1/analyses', headers=headers, json=payload).status_code == 201
    review = client.get(root).json()
    assert review['questions'][0]['status'] == 'unreviewed'
    assert review['approvedCount'] == 0


@pytest.mark.integration
def test_existing_accuracy_can_be_applied_without_another_model_call(auth_client):
    client, headers, db, root, q, payload = setup_analysis(auth_client)
    assert client.post(root + '/questions/1/analyses', headers=headers, json=payload).status_code == 201
    row = db.scalar(select(OfficialPaperReviewQuestion))
    row.status = 'unreviewed'
    data = copy.deepcopy(row.review_data)
    data['parts'][0]['status'] = 'unreviewed'
    row.review_data = data
    db.commit()
    result = client.post(root + '/auto-approval', headers=headers, json={})
    assert result.status_code == 200
    assert result.json()['results'][0]['status'] == 'ai_approved'
    assert client.get(root).json()['questions'][0]['accuracyAnalysis']['version'] == 1


@pytest.mark.integration
def test_batch_action_is_admin_only(auth_client):
    client, headers, db, root, q, payload = pending(auth_client)
    from app.models import User
    from app.security import hash_password
    import uuid
    username = 'approval-parent-' + uuid.uuid4().hex
    db.add(User(username=username, display_name='Parent', role='parent',
        password_hash=hash_password('parent test password'), must_change_password=False))
    db.commit()
    client.post('/api/v1/auth/logout', headers=headers)
    assert client.post(root + '/auto-approval', json={}).status_code == 401
    login = client.post('/api/v1/auth/login', json={'username': username, 'password': 'parent test password'}).json()
    assert client.post(root + '/auto-approval', headers={'X-CSRF-Token': login['csrfToken']}, json={}).status_code == 403


def test_analysis_importer_allows_only_policy_status_changes():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location('record_analysis', Path(__file__).parents[2] / 'scripts/record-official-question-analyses.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    before = dict(revision=1, status='unreviewed', reviewedBy='admin', reviewedAt='today',
        analysisContentHash='digest', data={'prompt': 'Original', 'parts': [{'label': 'a', 'status': 'unreviewed'}]})
    after = copy.deepcopy(before)
    after.update(revision=2, status='ai_approved')
    after['data']['parts'][0]['status'] = 'ai_approved'
    assert module.verify_policy_only_change(before, after)
    after['data']['prompt'] = 'Changed'
    assert not module.verify_policy_only_change(before, after)
    after = copy.deepcopy(before)
    after['status'] = 'approved'
    assert not module.verify_policy_only_change(before, after)


@pytest.mark.integration
def test_high_confidence_part_can_qualify_while_lower_part_remains_pending(auth_client):
    client, headers, db, root, q, payload = pending(auth_client)
    row = db.scalar(select(OfficialPaperReviewQuestion))
    data = copy.deepcopy(row.review_data)
    original = data['parts'][0]
    original['marks'] = 1
    original['markingPoints'] = original['markingPoints'][:1]
    second = copy.deepcopy(original)
    second['label'] = 'b'
    data['parts'].append(second)
    row.review_data = data
    db.commit()
    current = client.get(root).json()['questions'][0]
    payload['expectedContentHash'] = current['analysisContentHash']
    second_analysis = copy.deepcopy(payload['parts'][0])
    second_analysis.update(label='b', percent=70)
    payload['parts'].append(second_analysis)
    result = client.post(root + '/questions/1/analyses', headers=headers, json=payload)
    assert result.status_code == 201, result.text
    after = client.get(root).json()['questions'][0]
    assert after['status'] == 'unreviewed'
    assert [p['status'] for p in after['data']['parts']] == ['ai_approved', 'unreviewed']


@pytest.mark.integration
@pytest.mark.parametrize('prompt,expected', [
    ('Suggest a suitable explanation.', 'ai_approved'),
    ('Describe a notable change.', 'ai_approved'),
    ('Use the table to explain the result.', 'unreviewed'),
    ('Compare the graphs.', 'unreviewed'),
])
def test_visual_requirement_matches_words_not_fragments(auth_client, prompt, expected):
    client, headers, db, root, q, payload = pending(auth_client)
    row = db.scalar(select(OfficialPaperReviewQuestion))
    data = copy.deepcopy(row.review_data)
    data['visualAssetIds'] = []
    data['candidateVisualAssetIds'] = []
    data['parts'][0]['visualAssetIds'] = []
    data['parts'][0]['prompt'] = prompt
    row.review_data = data
    db.commit()
    current = client.get(root).json()['questions'][0]
    payload['expectedContentHash'] = current['analysisContentHash']
    result = client.post(root + '/questions/1/analyses', headers=headers, json=payload)
    assert result.status_code == 201, result.text
    assert client.get(root).json()['questions'][0]['status'] == expected
