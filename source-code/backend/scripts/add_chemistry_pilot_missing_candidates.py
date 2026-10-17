"""Attach two visually verified, still-unapproved pilot question crops.

Dry run by default. Run with --apply as the AKURU service user after deploying the
subpart-aware review schema. This never changes a review or publication status.
"""
import argparse
import hashlib
import uuid

import pymupdf
from sqlalchemy import select

from app.database import SessionLocal
from app.models import AuditEvent, DocumentAsset, DocumentVersion, OfficialPaperReviewQuestion, OfficialPaperReviewWorkspace
from app.storage import get_storage


MISSING = [
    ("b524e07b-a3ff-4071-bfe8-8913dccdb4ed", "9", 20, (255, 140, 342, 210),
     ("a(i)", "a(iii)"), "chloroethene_displayed_formula"),
    ("b4fd7a17-e3dd-4403-9799-875e1abb464c", "2", 7, (75, 430, 315, 665),
     ("e",), "reaction_profile_axes"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    storage = get_storage()
    with SessionLocal() as db:
        for paper_id, number, page_number, coords, target_parts, reference in MISSING:
            workspace = db.scalar(select(OfficialPaperReviewWorkspace).where(
                OfficialPaperReviewWorkspace.paper_document_id == uuid.UUID(paper_id)))
            if not workspace:
                raise RuntimeError(f"Missing workspace for {paper_id}")
            question = db.scalar(select(OfficialPaperReviewQuestion).where(
                OfficialPaperReviewQuestion.workspace_id == workspace.id,
                OfficialPaperReviewQuestion.number == number).with_for_update())
            if not question or question.status != "unreviewed":
                raise RuntimeError(f"Q{number}: draft missing or already reviewed")
            existing = db.scalar(select(DocumentAsset).where(
                DocumentAsset.document_version_id == workspace.paper_version_id,
                DocumentAsset.asset_metadata["pilotVisualRef"].as_string() == reference))
            if existing:
                print(f"{reference}: already exists ({existing.id})")
                continue
            labels = {part["label"] for part in question.review_data["parts"]}
            if not set(target_parts).issubset(labels):
                raise RuntimeError(f"Q{number}: expected part labels are missing")
            version = db.get(DocumentVersion, workspace.paper_version_id)
            original = storage.get(version.object_key, version.mime_type).content
            if hashlib.sha256(original).hexdigest() != version.sha256:
                raise RuntimeError(f"Q{number}: source PDF hash changed")
            with pymupdf.open(stream=original, filetype="pdf") as pdf:
                page = pdf[page_number - 1]
                box = pymupdf.Rect(coords)
                if not page.rect.contains(box):
                    raise RuntimeError(f"Q{number}: invalid crop box")
                content = page.get_pixmap(dpi=180, alpha=False, clip=box).tobytes("png")
                bounds = {key: value for key, value in zip(("x0", "y0", "x1", "y1"), coords)}
                normalized = {"x0": box.x0/page.rect.width, "y0": box.y0/page.rect.height,
                              "x1": box.x1/page.rect.width, "y1": box.y1/page.rect.height}
            print(f"{reference}: Q{number} page {page_number}, parts {target_parts}, {len(content)} PNG bytes")
            if not args.apply:
                continue
            asset_id = uuid.uuid4()
            key = f"derived/{version.id}/review-candidates/{asset_id}.png"
            storage.put(key, content, "image/png")
            db.add(DocumentAsset(id=asset_id, document_version_id=version.id,
                asset_kind="candidate_diagram_crop", object_key=key, mime_type="image/png",
                sha256=hashlib.sha256(content).hexdigest(), size_bytes=len(content),
                page_number=page_number, bounding_box=bounds,
                asset_metadata={"reviewCrop": True, "reviewApproved": False, "kind": "diagram",
                    "altText": "", "normalizedBounds": normalized, "pilotVisualRef": reference}))
            data = dict(question.review_data)
            data["parts"] = [{**part, "visualAssetIds": [*part.get("visualAssetIds", []), str(asset_id)]}
                if part["label"] in target_parts else part for part in data["parts"]]
            question.review_data = data
            question.revision += 1
            db.add(AuditEvent(actor_id=workspace.created_by,
                action="official_review.missing_pilot_visual_candidate_added",
                target_type="official_question", target_id=str(question.id),
                event_data={"paperDocumentId": paper_id, "questionNumber": number,
                            "assetId": str(asset_id), "partLabels": target_parts, "approved": False}))
            db.commit()


if __name__ == "__main__":
    main()
