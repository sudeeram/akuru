#!/usr/bin/env python3
"""Read-only reconciliation for June 2025 Pearson 4CH1 standard components.

Produces a local manifest beside ignored source PDFs. It is deliberately not an
importer: individual subparts, diagrams and marking points require human review.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
from pathlib import Path

import pymupdf


QUESTION_TOTAL = re.compile(r"\(?Total for Question\s*(\d+)\s*=\s*(\d+)\s*marks\)?", re.I)
SCHEME_TOTAL = re.compile(r"\bTotal\s*=*\s*(\d+)\b", re.I)
PAPER_TOTAL = re.compile(r"TOTAL FOR PAPER\s*=\s*(\d+)", re.I)
MARK_ALLOCATION = re.compile(r"^\((\d+)\)$", re.M)
COMPONENT_CODE = re.compile(r"(?:4CH1\s*[/ ]\s*|\bPaper\s*)([12]C(?:R)?)\b", re.I)


def sha256_file(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def totals(path: Path, pattern: re.Pattern) -> tuple[list[dict], int, int]:
    with pymupdf.open(path) as document:
        rows = []
        for index, page in enumerate(document):
            for match in pattern.finditer(page.get_text()):
                rows.append({"pdfPage": index + 1, "question": int(match.group(1)),
                             "marks": int(match.group(2))} if pattern is QUESTION_TOTAL else
                            {"pdfPage": index + 1, "marks": int(match.group(1))})
        return rows, len(document), sum(bool(page.get_text().strip()) for page in document)


def review_segments(path: Path, pattern: re.Pattern, first_page: int) -> list[str]:
    """Preserve source text between consecutive question totals for human review."""
    with pymupdf.open(path) as document:
        text = "\n".join(page.get_text() for page in document[first_page - 1:])
    segments = []
    previous_end = 0
    for match in pattern.finditer(text):
        segments.append(text[previous_end:match.start()].strip())
        previous_end = match.end()
    return segments


def scheme_page_ranges(path: Path, question_count: int) -> list[list[int]]:
    """Resolve every exact scheme section, including entries crossing page breaks."""
    with pymupdf.open(path) as document:
        first_page = 4
        pages = [page.get_text() for page in document[first_page - 1:]]
    starts = []
    offset = 0
    for page in pages:
        starts.append(offset)
        offset += len(page) + 1
    text = "\n".join(pages)
    totals = list(SCHEME_TOTAL.finditer(text))
    if len(totals) != question_count:
        raise ValueError("Mark-scheme section totals do not match question count")
    ranges = []
    previous_end = 0
    for question, total in enumerate(totals, 1):
        section = text[previous_end:total.start()]
        start_pattern = re.compile(rf"(?m)^\s*(?:Question\s+)?{question}\s*(?:\(a\)|$)")
        starts_for_question = list(start_pattern.finditer(section))
        if not starts_for_question:
            raise ValueError(f"Mark-scheme Question {question} start is missing")
        start_offset = previous_end + starts_for_question[0].start()
        start_page = first_page + bisect.bisect_right(starts, start_offset) - 1
        end_page = first_page + bisect.bisect_right(starts, total.start()) - 1
        ranges.append(list(range(start_page, end_page + 1)))
        previous_end = total.end()
    return ranges


def check_component(path: Path, expected: str) -> str:
    with pymupdf.open(path) as document:
        front = " ".join(page.get_text() for page in document[:4])
    found = {value.upper() for value in COMPONENT_CODE.findall(front)}
    if found and found != {expected}:
        raise ValueError(f"{path.name}: internal component {sorted(found)} disagrees with {expected}")
    return "matched" if found else "manual_review"


def report_heading_pages(page_texts: list[str], question: int) -> list[int]:
    """Candidate commentary headings, excluding incidental introduction mentions."""
    heading = re.compile(rf"(?mi)^\s*Question\s+0*{question}(?:\s*\([a-z]+\)|\s*$)")
    return [page + 1 for page, content in enumerate(page_texts) if heading.search(content)]


def inspect_set(root: Path, component: str) -> dict:
    names = {"question": ("Question-paper", "Questionpaper"),
             "markScheme": ("Mark-scheme", "Markscheme"),
             "examinerReport": ("Examiner-report", "Examinerreport")}
    files = {kind: root / folder / f"{stem}-Paper{component}-June2025.pdf"
             for kind, (folder, stem) in names.items()}
    if not all(path.is_file() for path in files.values()):
        raise ValueError(f"The {component} set is missing a companion PDF")
    identity_checks = {kind: check_component(path, component) for kind, path in files.items()}
    questions, qp_pages, qp_text_pages = totals(files["question"], QUESTION_TOTAL)
    scheme, ms_pages, ms_text_pages = totals(files["markScheme"], SCHEME_TOTAL)
    if not questions or [row["question"] for row in questions] != list(range(1, len(questions) + 1)):
        raise ValueError(f"{component}: question-total inventory is incomplete or out of order")
    if len(scheme) != len(questions) or [row["marks"] for row in scheme] != [row["marks"] for row in questions]:
        raise ValueError(f"{component}: question totals disagree with its exact mark scheme")
    question_texts = review_segments(files["question"], QUESTION_TOTAL, 3)
    scheme_texts = review_segments(files["markScheme"], SCHEME_TOTAL, 4)
    scheme_pages = scheme_page_ranges(files["markScheme"], len(questions))
    if len(question_texts) != len(questions) or len(scheme_texts) != len(questions):
        raise ValueError(f"{component}: source sections do not match the question inventory")
    with pymupdf.open(files["question"]) as document:
        final_text = "\n".join(page.get_text() for page in document[-4:])
        declared = [int(value) for value in PAPER_TOTAL.findall(final_text)]
        if declared != [sum(row["marks"] for row in questions)]:
            raise ValueError(f"{component}: declared paper total disagrees with question inventory")
        for index, row in enumerate(questions):
            possible_start = 3 if index == 0 else questions[index - 1]["pdfPage"]
            row["lastPdfPage"] = row["pdfPage"]
            number = row["question"]
            start_pattern = re.compile(rf"(?m)^\s*{number}[ \t]+(?=[A-Za-z(])")
            starts = [page_number for page_number in range(possible_start, row["lastPdfPage"] + 1)
                      if start_pattern.search(document[page_number - 1].get_text())]
            if len(starts) != 1:
                raise ValueError(f"{component} question {number}: expected one clear question start, found {starts}")
            row["firstPdfPage"] = starts[0]
            row["schemePdfPages"] = scheme_pages[index]
            allocations = [int(value) for value in MARK_ALLOCATION.findall(question_texts[index])]
            if sum(allocations) != row["marks"]:
                raise ValueError(f"{component} question {row['question']}: subpart allocations do not total {row['marks']}")
            row["subpartMarkAllocations"] = allocations
            row["status"] = "subparts_diagrams_topics_and_marking_points_need_review"
        embedded_images = sum(len(page.get_images()) for page in document)
    with pymupdf.open(files["examinerReport"]) as report:
        report_pages = len(report)
        report_text_pages = sum(bool(page.get_text().strip()) for page in report)
        report_texts = [page.get_text() for page in report]
    drafts = []
    for index, row in enumerate(questions):
        number = row["question"]
        start_match = re.search(rf"(?m)^\s*{number}[ \t]+(?=[A-Za-z(])", question_texts[index])
        if not start_match:
            raise ValueError(f"{component} question {number}: question text start is missing")
        report_pages_for_question = report_heading_pages(report_texts, number)
        drafts.append({"question": number, "marks": row["marks"],
                       "questionPdfPages": list(range(row["firstPdfPage"], row["lastPdfPage"] + 1)),
                       "schemePdfPages": row["schemePdfPages"],
                       "reportCandidatePdfPages": report_pages_for_question,
                       "subpartMarkAllocations": row["subpartMarkAllocations"],
                       "rawQuestionText": question_texts[index][start_match.start():].strip(),
                       "rawSchemeText": scheme_texts[index],
                       "reviewStatus": "draft_requires_human_verification",
                       "reviewChecks": {"promptAndSubparts": False, "visualsAndTables": False,
                                        "markingPointsAndAlternatives": False,
                                        "examinerComments": False, "topicMappings": False}})
    return {"paperKey": f"4CH1-2017-2025-JUNE-{component}",
            "component": component, "variant": "regional" if component.endswith("R") else "standard",
            "files": {kind: str(path.relative_to(root)) for kind, path in files.items()},
            "sourceSha256": {kind: sha256_file(path) for kind, path in files.items()},
            "internalIdentityChecks": identity_checks,
            "questionCount": len(questions), "totalMarks": sum(row["marks"] for row in questions),
            "questionPdfPages": qp_pages, "questionTextPages": qp_text_pages,
            "questionEmbeddedImages": embedded_images,
            "schemePdfPages": ms_pages, "schemeTextPages": ms_text_pages,
            "reportPdfPages": report_pages, "reportTextPages": report_text_pages,
            "questions": questions, "reviewDrafts": drafts}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("session_directory", type=Path)
    parser.add_argument("--include-regional", action="store_true",
                        help="Also inventory 1CR and 2CR; outside the standard-paper pilot")
    args = parser.parse_args()
    root = args.session_directory.resolve()
    components = ("1C", "2C", "1CR", "2CR") if args.include_regional else ("1C", "2C")
    manifest = {"releaseStatus": "preflight_only", "pilotComponents": list(components),
                "sets": [inspect_set(root, c) for c in components]}
    output = root / "june-2025-pilot-manifest.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {output}")
    for paper in manifest["sets"]:
        print(f"{paper['component']}: {paper['questionCount']} questions, {paper['totalMarks']} marks; exact scheme totals match")


if __name__ == "__main__":
    main()
