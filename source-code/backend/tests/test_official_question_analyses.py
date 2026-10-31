"""Analysis history must never mutate approved content or hide source/model uncertainty."""
import copy
import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from app.models import OfficialPaperReviewQuestion, OfficialQuestionAnalysis, User
from app.security import hash_password
from app.schemas.paper_analysis import AnalysisProvenance
from pydantic import ValidationError
from test_auth_integration import auth_client  # noqa
from test_official_paper_review_workspace import _setup, _question


def test_provenance_does_not_fabricate_provider_confirmation_or_an_ocr_model():
    with pytest.raises(ValidationError):
        AnalysisProvenance(role='paper', method='native_pdf', modelId='imaginary-model')
    with pytest.raises(ValidationError):
        AnalysisProvenance(role='paper', method='openai_api', modelId='test-model', modelIdentitySource='provider_response')
    assert AnalysisProvenance(role='paper', method='codex_assisted').modelId is None


def setup_analysis(auth_client):
    client, headers, db, paper, scheme, report, topic = _setup(auth_client)
    root = f'/api/v1/admin/official-paper-reviews/{paper[0].id}'
    assert client.post(root + '/start', headers=headers, json={
        'schemeDocumentId': str(scheme[0].id), 'reportDocumentId': str(report[0].id)}).status_code == 200
    saved = client.post(root + '/questions', headers=headers, json=_question(paper, scheme, topic))
    assert saved.status_code == 200, saved.text
    q = saved.json()['questions'][0]
    checks = [dict(role=role, status='checked', percent=95, pages=[1], reasons=['Compared with the exact original page.'])
              for role in ('paper', 'scheme', 'report')]
    estimate = dict(percent=95, reasons=['Wording, rubric and report association checked.'], sourceChecks=checks)
    payload = dict(expectedQuestionRevision=q['revision'], expectedAnalysisVersion=0,
        expectedContentHash=q['analysisContentHash'], stage='accuracy', methodVersion='test-comparison-v1',
        provenance=[dict(role=role, method='codex_assisted', provider='Test provider', modelId='test-model-v1',
            modelName='Test model', processedAt=datetime.now(timezone.utc).isoformat(), notes='Synthetic test analysis.')
            for role in ('paper', 'scheme', 'report')], question=estimate,
        parts=[dict(label=p['label'], **copy.deepcopy(estimate)) for p in q['data']['parts']])
    return client, headers, db, root, q, payload


@pytest.mark.integration
def test_analysis_is_append_only_and_preserves_approvals(auth_client):
    client, headers, db, root, before, payload = setup_analysis(auth_client)
    path = root + '/questions/1/analyses'
    assert client.post(path, json=payload).status_code == 403
    payload['parts'][0]['percent'] = 82
    payload['parts'][0]['provenance'] = [{**payload['provenance'][0], 'modelId': 'test-subpart-model'}]
    created = client.post(path, headers=headers, json=payload)
    assert created.status_code == 201, created.text
    row = created.json()
    assert row['question']['percent'] == 82 and row['isCurrent']
    assert row['sourceManifest'][0]['pageExtractionMethods'] == ['native']
    assert row['parts'][0]['provenance'][0]['modelId'] == 'test-subpart-model'
    after = client.get(root).json()['questions'][0]
    for field in ('revision', 'status', 'data', 'reviewedBy', 'reviewedAt', 'analysisContentHash'):
        assert before[field] == after[field]
    assert after['accuracyAnalysis']['id'] == row['id']
    assert client.post(path, headers=headers, json=payload).status_code == 409
    payload['expectedAnalysisVersion'] = 1
    payload['provenance'][0]['modelId'] = 'test-model-v2'
    assert client.post(path, headers=headers, json=payload).status_code == 201
    history = client.get(path).json()
    assert [item['version'] for item in history] == [2, 1]
    assert history[1]['provenance'][0]['modelId'] == 'test-model-v1'
    assert db.scalars(select(OfficialQuestionAnalysis)).all()


@pytest.mark.integration
def test_analysis_rejects_wrong_sources_parts_and_stale_content(auth_client):
    client, headers, db, root, q, payload = setup_analysis(auth_client)
    path = root + '/questions/1/analyses'
    bad = copy.deepcopy(payload); bad['parts'][0]['label'] = 'missing'
    assert client.post(path, headers=headers, json=bad).status_code == 422
    bad = copy.deepcopy(payload); bad['parts'][0]['sourceChecks'][0]['pages'] = [999]
    assert client.post(path, headers=headers, json=bad).status_code == 422
    bad = copy.deepcopy(payload); bad['expectedContentHash'] = 'a' * 64
    assert client.post(path, headers=headers, json=bad).status_code == 409
    created = client.post(path, headers=headers, json=payload)
    assert created.status_code == 201
    analysis = db.get(OfficialQuestionAnalysis, uuid.UUID(created.json()['id']))
    question = db.get(OfficialPaperReviewQuestion, analysis.question_id)
    # Status-only decisions do not invalidate the comparison.
    question.status = 'needs_correction'; db.commit()
    assert client.get(root).json()['questions'][0]['accuracyAnalysis']['isCurrent']
    question.review_data = {**question.review_data, 'prompt': 'Changed wording after assessment'}; db.commit()
    assert not client.get(root).json()['questions'][0]['accuracyAnalysis']['isCurrent']
    assert not client.get(path).json()[0]['isCurrent']


@pytest.mark.integration
def test_analysis_metadata_is_admin_only(auth_client):
    client, headers, db, root, q, payload = setup_analysis(auth_client)
    path = root + '/questions/1/analyses'
    username = 'analysis-parent-' + q['analysisContentHash'][:12]
    db.add(User(username=username, display_name='Test Parent', role='parent',
        password_hash=hash_password('safe parent test password'), must_change_password=False))
    db.commit()
    client.post('/api/v1/auth/logout', headers=headers)
    assert client.get(path).status_code == 401
    login = client.post('/api/v1/auth/login', json={'username': username, 'password': 'safe parent test password'}).json()
    assert client.get(path).status_code == 403
    assert client.post(path, headers={'X-CSRF-Token': login['csrfToken']}, json=payload).status_code == 403
