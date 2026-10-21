import uuid
import pymupdf

import pytest
from sqlalchemy import select

from app.database import get_db
from app.main import app
from app.models import (
    Document, DocumentAsset, DocumentBlock, DocumentPage, DocumentVersion,
    OfficialPaperReviewQuestion, Textbook, TextbookGroup, TextbookTopic, User,
)
from app.security import hash_password
from app.storage.factory import get_storage
from app.storage.local import LocalObjectStorage
from test_auth_integration import auth_client  # noqa: F401 - shared transactional fixture


def _source(session, admin, token, kind, paper=None):
    document = Document(kind=kind, course_id="igcse", subject_id="chemistry",
        title=f"{kind}-{token}", original_filename=f"{kind}.pdf",
        object_key=f"tests/review-{token}-{kind}.pdf", mime_type="application/pdf",
        sha256=(token * 2)[:64], size_bytes=10, review_state="pending",
        publication_year=2025, exam_session="June", component="1C", variant="standard",
        source_document_id=paper.id if paper else None, uploaded_by=admin.id)
    session.add(document); session.flush()
    version = DocumentVersion(document_id=document.id, version_number=1,
        original_filename=document.original_filename,
        object_key=f"tests/review-{token}-{kind}-v1.pdf", mime_type="application/pdf",
        sha256=(token[::-1] * 2)[:64], size_bytes=10, status="completed", uploaded_by=admin.id)
    session.add(version); session.flush()
    asset = DocumentAsset(document_version_id=version.id, asset_kind="page_render",
        object_key=f"tests/review-{token}-{kind}.png", mime_type="image/png",
        sha256=(f"a{token}" * 2)[:64], size_bytes=10, page_number=1, bounding_box={})
    session.add(asset); session.flush()
    visual = DocumentAsset(document_version_id=version.id, asset_kind="review_diagram_crop",
        object_key=f"tests/review-{token}-{kind}-visual.png", mime_type="image/png",
        sha256=(f"b{token}" * 2)[:64], size_bytes=10, page_number=1,
        bounding_box={"x0":10,"y0":10,"x1":60,"y1":60},
        asset_metadata={"reviewCrop":True,"reviewApproved":True,"kind":"diagram","altText":"Two separated chromatography spots."})
    session.add(visual); session.flush()
    page = DocumentPage(document_version_id=version.id, page_number=1,
        width_points=100, height_points=100, render_asset_id=asset.id,
        extraction_method="native", confidence=1.0, needs_review=False, page_metadata={})
    session.add(page); session.flush()
    block = DocumentBlock(document_version_id=version.id, page_id=page.id,
        sequence_number=1, block_kind="question", text="Question 1", bounding_box={},
        extraction_method="native", confidence=1.0, needs_review=False, block_metadata={})
    session.add(block); session.flush()
    return document, version, page, block, asset, visual


def _setup(auth_client):
    client, username, password = auth_client
    assert client.get("/api/v1/admin/official-paper-reviews/" + str(uuid.uuid4())).status_code == 401
    login = client.post("/api/v1/auth/login", json={"username": username, "password": password}).json()
    headers = {"X-CSRF-Token": login["csrfToken"]}
    session = next(app.dependency_overrides[get_db]())
    admin = session.scalar(select(User).where(User.username == username))
    token = uuid.uuid4().hex
    paper = _source(session, admin, token + "p", "past_paper")
    scheme = _source(session, admin, token + "s", "mark_scheme", paper[0])
    report = _source(session, admin, token + "r", "examiner_report", paper[0])
    book = Textbook(course_id="igcse", subject_id="chemistry", title=f"Book {token}",
        edition="2025", publisher="AKURU", group_label="unit", status="published", created_by=admin.id)
    session.add(book); session.flush()
    group = TextbookGroup(textbook_id=book.id, code="1", title="Unit 1", sequence=1, status="published")
    session.add(group); session.flush()
    topic = TextbookTopic(textbook_id=book.id, group_id=group.id, course_id="igcse",
        subject_id="chemistry", code="1", title="States", sequence=1, status="published")
    session.add(topic); session.commit()
    return client, headers, session, paper, scheme, report, topic


def _question(paper, scheme, topic):
    paper_source = {"page": 1, "blockId": str(paper[3].id), "assetId": str(paper[4].id)}
    scheme_source = {"page": 1, "blockId": str(scheme[3].id), "assetId": str(scheme[4].id)}
    return {"number": "1", "expectedRevision": 0, "status": "approved", "data": {
        "marks": 2, "prompt": "Explain the chromatogram", "sharedStem": "Use the diagram",
        "paperSources": [paper_source], "visualAssetIds": [str(paper[5].id)], "parts": [{
            "label": "a", "marks": 2, "prompt": "Explain the chromatogram",
            "markingPoints": [{"code": "M1", "text": "One spot", "kind": "method"},
                              {"code": "M2", "text": "Separated dyes", "kind": "accuracy"}],
            "paperSources": [paper_source], "schemeSources": [scheme_source],
            "assessmentReadiness": "automatic",
            "coverage": "supported", "coverageReason": "The published chapter teaches chromatography.",
            "topicRefs": [topic.public_ref], "status": "approved",
        }],
    }}


@pytest.mark.integration
def test_admin_can_review_one_question_without_student_release(auth_client):
    client, headers, session, paper, scheme, report, topic = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    assert client.post(root + "/start", json={"schemeDocumentId": str(scheme[0].id)}).status_code == 403
    started = client.post(root + "/start", headers=headers, json={
        "schemeDocumentId": str(scheme[0].id), "reportDocumentId": str(report[0].id),
        "expectedQuestionCount": 2})
    assert started.status_code == 200, started.text
    assert started.json()["wholePaperReady"] is False
    body = _question(paper, scheme, topic)
    saved = client.post(root + "/questions", headers=headers, json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json()["approvedCount"] == 1
    assert saved.json()["wholePaperReady"] is False
    assert session.scalar(select(OfficialPaperReviewQuestion).where(
        OfficialPaperReviewQuestion.workspace_id.is_not(None))).status == "approved"
    assert client.post(root + "/questions", headers=headers, json=body).status_code == 409
    assert client.get(root).json()["questions"][0]["data"]["parts"][0]["topicRefs"] == [topic.public_ref]
    reopened = _question(paper, scheme, topic)
    reopened["expectedRevision"] = 1
    reopened["status"] = "needs_correction"
    reopened["data"]["prompt"] = "Revised explanation"
    result = client.post(root + "/questions", headers=headers, json=reopened)
    assert result.status_code == 200, result.text
    assert result.json()["questions"][0]["status"] == "needs_correction"
    assert result.json()["questions"][0]["data"]["parts"][0]["status"] == "needs_correction"


@pytest.mark.integration
def test_approval_links_one_matching_paper_subpart_without_repeating_manual_work(auth_client):
    client, headers, session, paper, scheme, _, topic = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    block = DocumentBlock(document_version_id=paper[1].id, page_id=paper[2].id,
        sequence_number=2, block_kind="subpart", text="(a) Explain the chromatography diagram.",
        bounding_box={}, extraction_method="native", confidence=1.0,
        needs_review=False, block_metadata={})
    session.add(block); session.commit()
    assert client.post(root + "/start", headers=headers, json={
        "schemeDocumentId": str(scheme[0].id), "expectedQuestionCount": 1}).status_code == 200
    body = _question(paper, scheme, topic)
    body["data"]["parts"][0]["prompt"] = "(a) Explain the chromatography diagram."
    page_only = {"page": 1, "assetId": str(paper[4].id)}
    body["data"]["paperSources"] = [page_only]
    body["data"]["parts"][0]["paperSources"] = [page_only]
    saved = client.post(root + "/questions", headers=headers, json=body)
    assert saved.status_code == 200, saved.text
    question = saved.json()["questions"][0]
    assert question["status"] == "approved"
    assert any(source.get("blockId") == str(block.id) for source in question["data"]["paperSources"])
    assert any(source.get("blockId") == str(block.id) for source in question["data"]["parts"][0]["paperSources"])


@pytest.mark.integration
def test_approval_does_not_guess_when_paper_blocks_are_ambiguous(auth_client):
    client, headers, session, paper, scheme, _, topic = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    for sequence in (2, 3):
        session.add(DocumentBlock(document_version_id=paper[1].id, page_id=paper[2].id,
            sequence_number=sequence, block_kind="subpart", text="(a) Explain the chromatography diagram.",
            bounding_box={}, extraction_method="native", confidence=1.0,
            needs_review=False, block_metadata={}))
    session.commit()
    assert client.post(root + "/start", headers=headers, json={
        "schemeDocumentId": str(scheme[0].id), "expectedQuestionCount": 1}).status_code == 200
    body = _question(paper, scheme, topic)
    body["data"]["parts"][0]["prompt"] = "(a) Explain the chromatography diagram."
    page_only = {"page": 1, "assetId": str(paper[4].id)}
    body["data"]["paperSources"] = [page_only]
    body["data"]["parts"][0]["paperSources"] = [page_only]
    response = client.post(root + "/questions", headers=headers, json=body)
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "exact_block_required"


@pytest.mark.integration
def test_draft_marking_points_and_precise_visual_crops(auth_client, tmp_path):
    client, headers, session, paper, scheme, _, topic = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    assert client.post(root + "/start", headers=headers, json={
        "schemeDocumentId": str(scheme[0].id), "expectedQuestionCount": 1}).status_code == 200
    draft = _question(paper, scheme, topic)
    draft["status"] = "unreviewed"
    draft["data"]["marks"] = 3  # incomplete reconciliation is allowed in a saved draft
    draft["data"]["visualAssetIds"] = []
    draft["data"]["parts"][0]["status"] = "unreviewed"
    draft["data"]["parts"][0]["assessmentReadiness"] = "unreviewed"
    draft["data"]["parts"][0]["markingPoints"] = [{"code": "", "text": ""}]
    saved = client.post(root + "/questions", headers=headers, json=draft)
    assert saved.status_code == 200, saved.text
    assert client.get(root).json()["questions"][0]["data"]["parts"][0]["markingPoints"][0]["text"] == ""
    approved = _question(paper, scheme, topic)
    approved["data"]["visualAssetIds"] = []
    approved["expectedRevision"] = 1
    assert client.post(root + "/questions", headers=headers, json=approved).json()["error"]["code"] == "required_part_visual_missing"

    pdf = pymupdf.open()
    page = pdf.new_page(width=100, height=100)
    page.insert_text((20, 30), "Atom diagram")
    shape = page.new_shape()
    shape.draw_circle(pymupdf.Point(48, 57), 23)
    shape.draw_circle(pymupdf.Point(48, 57), 10)
    shape.finish(color=(0, 0, 0), width=1)
    shape.commit()
    content = pdf.tobytes()
    pdf.close()
    storage = LocalObjectStorage(tmp_path)
    storage.put(paper[1].object_key, content, "application/pdf")
    old_storage = app.dependency_overrides.get(get_storage)
    app.dependency_overrides[get_storage] = lambda: storage
    try:
        generated = client.post(root + "/visual-candidates/generate", headers=headers)
        assert generated.status_code == 200, generated.text
        assert generated.json()["created"] >= 1
        candidates = client.get(root + "/visual-crops").json()
        assert any(not row["approved"] for row in candidates)
        assert any(row["assetId"] in client.get(root).json()["questions"][0]["data"]["candidateVisualAssetIds"] for row in candidates)
        crop = {"page":1,"kind":"diagram","x0":0.1,"y0":0.1,"x1":0.7,"y1":0.6,
                "altText":"An atom diagram with labelled particles."}
        assert client.post(root + "/visual-crops", json=crop).status_code == 403
        assert client.post(root + "/visual-crops", headers=headers, json={**crop,"x1":1,"y1":1}).status_code == 422
        created = client.post(root + "/visual-crops", headers=headers, json=crop)
        assert created.status_code == 200, created.text
        asset_id = created.json()["assetId"]
        assert any(row["assetId"] == asset_id for row in client.get(root + "/visual-crops").json())
        asset = session.get(DocumentAsset, uuid.UUID(asset_id))
        assert asset.document_version_id == paper[1].id and asset.asset_metadata["altText"] == crop["altText"]
        assert storage.get(asset.object_key, "image/png").content.startswith(b"\x89PNG")
        approved["data"]["parts"][0]["visualAssetIds"] = [asset_id]
        approved["expectedRevision"] = 2
        saved = client.post(root + "/questions", headers=headers, json=approved)
        assert saved.status_code == 200, saved.text
    finally:
        if old_storage is None:
            app.dependency_overrides.pop(get_storage, None)
        else:
            app.dependency_overrides[get_storage] = old_storage


@pytest.mark.integration
def test_subpart_visuals_are_required_at_the_relevant_part_and_preserved(auth_client):
    client, headers, session, paper, scheme, _, topic = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    assert client.post(root + "/start", headers=headers, json={
        "schemeDocumentId": str(scheme[0].id), "expectedQuestionCount": 1}).status_code == 200
    table = DocumentAsset(document_version_id=paper[1].id, asset_kind="review_table_crop",
        object_key=f"tests/review-{uuid.uuid4().hex}-table.png", mime_type="image/png",
        sha256=uuid.uuid4().hex * 2, size_bytes=10, page_number=1, bounding_box={},
        asset_metadata={"reviewCrop": True, "reviewApproved": True, "kind": "table",
                        "altText": "Four rows of results for the atom."})
    session.add(table); session.commit()
    body = _question(paper, scheme, topic)
    body["data"]["marks"] = 4
    body["data"]["visualAssetIds"] = []
    first = body["data"]["parts"][0]
    first["prompt"] = "Label the diagram."
    first["visualAssetIds"] = [str(paper[5].id)]
    second = {**first, "label": "b", "prompt": "Use the diagram to complete the table.",
              "visualAssetIds": [str(table.id)]}
    body["data"]["parts"].append(second)
    missing = client.post(root + "/questions", headers=headers, json=body)
    assert missing.status_code == 409 and missing.json()["error"]["code"] == "required_part_visual_missing"
    second["visualAssetIds"] = [str(paper[5].id), str(table.id)]
    saved = client.post(root + "/questions", headers=headers, json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json()["questions"][0]["data"]["parts"][1]["visualAssetIds"] == second["visualAssetIds"]
    prepared = client.post(root + "/prepare-official-drafts", headers=headers)
    assert prepared.status_code == 200, prepared.text
    published_draft = client.get(f"/api/v1/documents/{paper[0].id}/official-review").json()
    assert published_draft["questions"][0]["visualPlacements"] == {
        "shared": [], "a": [str(paper[5].id)], "b": second["visualAssetIds"]}


@pytest.mark.integration
def test_source_topic_and_companion_guards(auth_client):
    client, headers, session, paper, scheme, report, topic = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    bad = client.post(root + "/start", headers=headers, json={"schemeDocumentId": str(report[0].id)})
    assert bad.status_code == 409
    assert client.post(root + "/start", headers=headers, json={"schemeDocumentId": str(scheme[0].id)}).status_code == 200
    body = _question(paper, scheme, topic)
    body["data"]["parts"][0]["schemeSources"][0]["blockId"] = str(paper[3].id)
    assert client.post(root + "/questions", headers=headers, json=body).status_code == 422
    body = _question(paper, scheme, topic)
    body["data"]["parts"][0]["topicRefs"] = ["topic_missing"]
    assert client.post(root + "/questions", headers=headers, json=body).status_code == 422
    body = _question(paper, scheme, topic)
    body["data"]["parts"][0]["markingPoints"] = []
    assert client.post(root + "/questions", headers=headers, json=body).status_code == 409


@pytest.mark.integration
def test_import_requires_exact_uploaded_pdf_hashes(auth_client):
    client, headers, session, paper, scheme, _, _ = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    assert client.post(root + "/start", headers=headers, json={
        "schemeDocumentId": str(scheme[0].id), "expectedQuestionCount": 1}).status_code == 200
    bank = {"status": "local_draft_unreleased", "studentAccess": False,
        "course": "igcse", "subject": "chemistry", "papers": [{
            "component": "1C", "paperKey": "pilot-1C", "questionCount": 1,
            "totalMarks": 2, "sourceSha256": {"question": "wrong", "markScheme": scheme[1].sha256},
        }], "questions": [{"paperKey": "pilot-1C", "component": "1C", "number": "1",
            "marks": 2, "studentPrompt": None, "topicMappings": [],
            "rawQuestionExtraction": "Draft wording", "subparts": [{"label": "a", "marks": 2,
                "extractionCandidate": "Draft wording"}],
            "source": {"questionPdfPages": [1], "schemePdfPages": [1]}}]}
    assert client.post(root + "/seed", headers=headers, json={"draftBank": bank}).status_code == 409
    bank["papers"][0]["sourceSha256"]["question"] = paper[1].sha256
    response = client.post(root + "/seed", headers=headers, json={"draftBank": bank})
    assert response.status_code == 200, response.text
    assert response.json()["questions"][0]["status"] == "unreviewed"
    assert response.json()["wholePaperReady"] is False


@pytest.mark.integration
def test_whole_paper_review_prepares_drafts_and_gates_publication(auth_client):
    client, headers, _, paper, scheme, _, topic = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    paper_publish = f"/api/v1/documents/{paper[0].id}/official-review/publish"
    scheme_publish = f"/api/v1/documents/{scheme[0].id}/official-review/publish"
    confirmation = {"confirmCourse": True, "confirmSubject": True,
                    "confirmComplete": True, "confirmSourcePaper": True}
    assert client.post(root + "/start", headers=headers, json={
        "schemeDocumentId": str(scheme[0].id), "expectedQuestionCount": 1}).status_code == 200
    assert client.post(root + "/prepare-official-drafts", headers=headers).status_code == 409
    assert client.post(root + "/questions", headers=headers,
                       json=_question(paper, scheme, topic)).status_code == 200
    assert client.post(paper_publish, headers=headers, json=confirmation).status_code == 409
    prepared = client.post(root + "/prepare-official-drafts", headers=headers)
    assert prepared.status_code == 200, prepared.text
    assert prepared.json()["published"] is False
    assert client.post(scheme_publish, headers=headers, json=confirmation).status_code == 409
    released_paper = client.post(paper_publish, headers=headers, json=confirmation)
    assert released_paper.status_code == 200, released_paper.text
    released_scheme = client.post(scheme_publish, headers=headers, json=confirmation)
    assert released_scheme.status_code == 200, released_scheme.text


@pytest.mark.integration
def test_content_approval_and_grouped_scoring_readiness_are_separate(auth_client):
    client, headers, session, paper, scheme, _, topic = _setup(auth_client)
    root = f"/api/v1/admin/official-paper-reviews/{paper[0].id}"
    assert client.post(root + "/start", headers=headers, json={"schemeDocumentId":str(scheme[0].id),"expectedQuestionCount":1}).status_code == 200
    body = _question(paper, scheme, topic)
    part = body["data"]["parts"][0]
    part["assessmentReadiness"] = "unreviewed"
    part["markingPoints"].extend([{"code":"M3","text":"Third observation"},{"code":"M4","text":"Fourth observation"}])
    response = client.post(root + "/questions", headers=headers, json=body)
    assert response.status_code == 200, response.text
    assert response.json()["wholePaperReady"] is True
    assert response.json()["automaticAssessmentReady"] is False
    assert client.post(root + "/prepare-official-drafts", headers=headers).status_code == 409
    body["expectedRevision"] = 1
    part["assessmentReadiness"] = "automatic"
    part["scoringRules"] = {"combinedResponses":[{"phrase":"moves on the surface","pointIds":["M2","M3"]}]}
    response = client.post(root + "/questions", headers=headers, json=body)
    assert response.status_code == 200, response.text
    assert response.json()["questions"][0]["status"] == "approved"
    assert response.json()["automaticAssessmentReady"] is True
    assert client.post(root + "/prepare-official-drafts", headers=headers).status_code == 200
    from app.models import MarkSchemeEntryVersion
    entry = session.scalar(select(MarkSchemeEntryVersion).where(MarkSchemeEntryVersion.question_number == "1"))
    assert entry.scoring_rules["groups"][0]["maxMarks"] == 2
    assert entry.scoring_rules["combinedResponses"][0]["pointIds"] == ["a.M2", "a.M3"]
    assert client.post(root + "/questions", headers=headers, json=body).status_code == 409
    body["expectedRevision"] = 2
    part["scoringRules"]["combinedResponses"][0]["pointIds"] = ["M2","missing"]
    assert client.post(root + "/questions", headers=headers, json=body).status_code == 409
