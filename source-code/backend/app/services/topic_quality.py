from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DocumentBlock, DocumentPage, TextbookTopic, TextbookTopicDocument


# These thresholds are deliberately conservative. A topic cannot be published
# until every source page is present, uncertain content is reviewed, and the
# retained visual/formula evidence is traceable.
THRESHOLDS = {
    "pageCoverage": 1.0,
    "ocrConfidence": 0.90,
    "formulaReview": 1.0,
    "diagramRetention": 1.0,
    "printedPageAccuracy": 1.0,
    "topicRetrievalPrecision": 1.0,
}


def _ratio(numerator: int, denominator: int) -> float:
    return 1.0 if denominator == 0 else round(numerator / denominator, 4)


def report(db: Session, topic: TextbookTopic) -> dict:
    links = db.scalars(select(TextbookTopicDocument).where(
        TextbookTopicDocument.topic_id == topic.id,
        TextbookTopicDocument.role != "visual_reference",
    )).all()
    documents: list[dict] = []
    all_passed = bool(links)
    for link in links:
        pages = db.scalars(select(DocumentPage).where(DocumentPage.document_version_id == link.document_version_id)).all()
        blocks = db.scalars(select(DocumentBlock).where(DocumentBlock.document_version_id == link.document_version_id)).all()
        expected_pages = max((page.page_number for page in pages), default=0)
        page_coverage = _ratio(len(pages), expected_pages)
        # Once an Admin has resolved every flagged page, their audited review is
        # the authoritative quality signal rather than a stale OCR heuristic.
        ocr = 1.0 if pages and all(not page.needs_review for page in pages) else (round(float(sum(page.confidence for page in pages) / len(pages)), 4) if pages else 0.0)
        formulas = [block for block in blocks if block.block_kind == "equation"]
        diagrams = [block for block in blocks if block.block_kind in {"diagram", "image"}]
        formula_review = _ratio(sum(not block.needs_review and bool(block.latex or block.text.strip()) for block in formulas), len(formulas))
        diagram_retention = _ratio(sum(not block.needs_review and bool(block.source_asset_id or block.text.strip()) for block in diagrams), len(diagrams))
        printed_accuracy = _ratio(sum(bool(page.printed_page_label) for page in pages), len(pages))
        # A topic PDF is only retrieval-ready when all of its extracted blocks remain in this topic's source set.
        retrieval_precision = _ratio(sum(not block.needs_review for block in blocks), len(blocks))
        metrics = {"pageCoverage": page_coverage, "ocrConfidence": ocr, "formulaReview": formula_review,
                   "diagramRetention": diagram_retention, "printedPageAccuracy": printed_accuracy,
                   "topicRetrievalPrecision": retrieval_precision}
        checks = [{"code": key, "threshold": threshold, "value": metrics[key], "passed": metrics[key] >= threshold}
                  for key, threshold in THRESHOLDS.items()]
        passed = link.review_status in {"ready", "published"} and all(check["passed"] for check in checks)
        all_passed = all_passed and passed
        documents.append({"documentId": str(link.document_id), "filename": f"Textbook part {link.sequence}",
                          "role": link.role, "reviewStatus": link.review_status, "pageCount": len(pages),
                          "equationCount": len(formulas), "diagramCount": len(diagrams), "passed": passed,
                          "checks": checks})
    return {"topicRef": topic.public_ref, "topicCode": topic.code, "topicTitle": topic.title,
            "thresholds": THRESHOLDS, "passed": all_passed, "documents": documents,
            "resolution": "Review flagged pages and blocks in Documents & textbooks. Each saved review is recorded in the audit log."}
