#!/usr/bin/env python3
"""Read-only lexical preflight of a private pilot bank against AKURU textbook chunks.

Run with the normal backend environment and PYTHONPATH. Suggestions are never
topic mappings, coverage decisions or Student-visible content.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
import re
from pathlib import Path

from sqlalchemy import select, text

from app.database import SessionLocal
from app.models import RetrievalChunk, TextbookTopic, TextbookTopicContentVersion


STOP = set("a an and are as at be by can do does for from give how if in into is it its of on or the their then there these this those to two use using was were what when which with you your answer question marks mark page area write turn over line show state explain calculate describe name correct result student".split())
TOKEN = re.compile(r"[a-z][a-z0-9]{2,}", re.I)


def words(value: str) -> list[str]:
    return [token for token in TOKEN.findall(value.casefold()) if token not in STOP]


def rank_chunks(query: str, chunks: list[dict], limit: int = 3) -> list[dict]:
    """Rank within the available published content; scores are not probabilities."""
    query_terms = set(words(query))
    if not query_terms or not chunks:
        return []
    frequencies = [Counter(words(chunk["content"])) for chunk in chunks]
    lengths = [sum(counts.values()) for counts in frequencies]
    average_length = max(1, sum(lengths) / len(lengths))
    document_frequency = Counter(term for counts in frequencies for term in counts)
    ranked = []
    for chunk, counts, length in zip(chunks, frequencies, lengths):
        score = 0.0
        for term in query_terms:
            frequency = counts.get(term, 0)
            if not frequency:
                continue
            idf = math.log(1 + (len(chunks) - document_frequency[term] + 0.5)
                           / (document_frequency[term] + 0.5))
            score += idf * (frequency * 2.2) / (frequency + 1.2 * (0.25 + 0.75 * length / average_length))
        if score > 0:
            ranked.append({"topicRef": chunk["topicRef"], "topicCode": chunk["topicCode"],
                           "topicTitle": chunk["topicTitle"], "contentVersion": chunk["contentVersion"],
                           "pageNumber": chunk["pageNumber"], "lexicalScore": round(score, 3),
                           "evidenceExcerpt": " ".join(chunk["content"].split())[:240]})
    ranked.sort(key=lambda row: row["lexicalScore"], reverse=True)
    return ranked[:limit]


def published_chunks() -> tuple[list[dict], list[dict]]:
    with SessionLocal() as db:
        db.execute(text("SET TRANSACTION READ ONLY"))
        topics = db.execute(select(TextbookTopic).where(
            TextbookTopic.course_id == "igcse", TextbookTopic.subject_id == "chemistry",
            TextbookTopic.status == "published",
        ).order_by(TextbookTopic.code)).scalars().all()
        topic_ids = [topic.id for topic in topics]
        rows = db.execute(select(RetrievalChunk, TextbookTopic, TextbookTopicContentVersion).join(
            TextbookTopic, TextbookTopic.id == RetrievalChunk.topic_id
        ).join(
            TextbookTopicContentVersion,
            TextbookTopicContentVersion.id == RetrievalChunk.topic_content_version_id,
        ).where(
            RetrievalChunk.topic_id.in_(topic_ids), RetrievalChunk.status == "active",
            RetrievalChunk.source_type == "textbook_section",
            TextbookTopicContentVersion.status == "published",
        )).all()
        topic_rows = [{"publicRef": topic.public_ref, "code": topic.code, "title": topic.title,
                       "publishedAt": topic.published_at.isoformat() if topic.published_at else None}
                      for topic in topics]
        chunk_rows = [{"topicRef": topic.public_ref, "topicCode": topic.code,
                       "topicTitle": topic.title, "contentVersion": version.version_number,
                       "pageNumber": chunk.page_number, "content": chunk.content}
                      for chunk, topic, version in rows]
        db.rollback()
        return topic_rows, chunk_rows


def analyze(bank: dict, topics: list[dict], chunks: list[dict]) -> dict:
    if bank.get("status") != "local_draft_unreleased" or bank.get("studentAccess") is not False:
        raise ValueError("Only an unreleased pilot draft bank may be analyzed")
    if bank.get("course") != "igcse" or bank.get("subject") != "chemistry":
        raise ValueError("Only iGCSE Chemistry pilot material may be analyzed")
    if [paper.get("component") for paper in bank.get("papers", [])] != ["1C", "2C"]:
        raise ValueError("Only standard June 2025 1C/2C pilot papers are accepted")
    if any(question.get("studentPrompt") is not None or question.get("topicMappings") for question in bank["questions"]):
        raise ValueError("A released or mapped question cannot enter the private preflight")
    analyses = []
    for question in bank["questions"]:
        subparts = []
        for part in question["subparts"]:
            # Include the common stem; a subpart may otherwise lack its subject.
            query = " ".join((question.get("sharedStemExtractionCandidate", ""),
                              part.get("extractionCandidate", "")))
            subparts.append({"label": part["label"], "marks": part["marks"],
                             "candidateEvidence": rank_chunks(query, chunks),
                             "mappingStatus": "human_review_required"})
        analyses.append({"paperKey": question["paperKey"], "number": question["number"],
                         "questionMarks": question["marks"], "subparts": subparts,
                         "coverageStatus": "unverified"})
    return {"analysisType": "read_only_lexical_preflight", "studentAccess": False,
            "automaticMappingsCreated": 0, "topics": topics,
            "activeTextbookChunkCount": len(chunks), "questions": analyses,
            "limitations": ["Lexical overlap is not syllabus equivalence.",
                            "Only currently published Chemistry topics are searched.",
                            "All question and subpart topic mappings require human approval."]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft_bank", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--context-output", type=Path,
                        help="Private copy of published textbook chunks for human review")
    args = parser.parse_args()
    bank = json.loads(args.draft_bank.read_text())
    topics, chunks = published_chunks()
    report = analyze(bank, topics, chunks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if args.context_output:
        args.context_output.parent.mkdir(parents=True, exist_ok=True)
        args.context_output.write_text(json.dumps({"topics": topics, "chunks": chunks},
                                                  indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {args.output}: {len(report['questions'])} questions, "
          f"{len(topics)} published topics, {len(chunks)} active chunks; zero mappings created")


if __name__ == "__main__":
    main()
