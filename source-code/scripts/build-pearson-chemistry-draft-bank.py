#!/usr/bin/env python3
"""Build an unreleased, local review pack from the June 2025 1C/2C preflight.

The output stays beside the ignored source PDFs. It is deliberately not an AKURU
database importer: extracted wording, marking points and report links must be
reviewed before any official-material version can be saved or published.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

import pymupdf


SCRIPT = Path(__file__).with_name("pilot-pearson-chemistry.py")
SPEC = importlib.util.spec_from_file_location("pilot_pearson_chemistry", SCRIPT)
assert SPEC and SPEC.loader
pilot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pilot)

MARK_LINE = re.compile(r"^\s*\((\d+)\)\s*$")
LEADING_LABELS = re.compile(r"^\s*((?:\([a-zivx]+\)\s*)+)")
ROMAN = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii"}


def separate_subparts(raw_text: str, allocations: list[int]) -> tuple[str, list[dict]]:
    """Keep extracted candidates and fail closed if labels/marks are ambiguous."""
    text = re.sub(r"^\s*\d+\s+", "", raw_text, count=1)
    pending: list[str] = []
    parts: list[dict] = []
    major = minor = ""
    shared_stem_lines: list[str] | None = None
    for line in text.splitlines():
        if MARK_LINE.fullmatch(line):
            if not major:
                raise ValueError("A mark allocation has no labelled subpart")
            marks = int(MARK_LINE.fullmatch(line).group(1))
            label = f"{major}({minor})" if minor else major
            parts.append({"label": label, "marks": marks,
                          "extractionCandidate": "\n".join(pending).strip(),
                          "reviewStatus": "wording_and_layout_pending"})
            pending = []
            continue
        prefix = LEADING_LABELS.match(line)
        if prefix:
            if shared_stem_lines is None:
                shared_stem_lines = pending.copy()
            for token in re.findall(r"\(([a-zivx]+)\)", prefix.group(1)):
                if token in ROMAN:
                    minor = token
                else:
                    major, minor = token, ""
        pending.append(line)
    if not parts or [part["marks"] for part in parts] != allocations:
        raise ValueError("Extracted subpart marks disagree with reconciled paper allocations")
    if len({part["label"] for part in parts}) != len(parts):
        raise ValueError("Extracted subpart labels are missing or duplicated")
    # Text before the first label is a shared-stem candidate, not an approved stem.
    stem = "\n".join(shared_stem_lines or []).strip()
    return stem, parts


def build(root: Path, manifest: dict, image_scale: float = 1.5) -> dict:
    if manifest.get("releaseStatus") != "preflight_only" or manifest.get("pilotComponents") != ["1C", "2C"]:
        raise ValueError("This review pack requires the unreleased standard 1C/2C pilot manifest")
    image_dir = root / ".pilot-review" / "question-pages"
    scheme_dir = root / ".pilot-review" / "scheme-pages"
    bank = {"schemaVersion": 1, "status": "local_draft_unreleased",
            "studentAccess": False, "course": "igcse", "subject": "chemistry",
            "papers": [], "questions": []}
    for source in manifest["sets"]:
        component = source["component"]
        files = source["files"]
        for kind, relative in files.items():
            if pilot.sha256_file(root / relative) != source["sourceSha256"][kind]:
                raise ValueError(f"{component} {kind}: PDF changed after preflight; rebuild the manifest")
        bank["papers"].append({"paperKey": source["paperKey"], "component": component,
                               "variant": "standard", "files": files,
                               "sourceSha256": source["sourceSha256"],
                               "questionCount": source["questionCount"],
                               "totalMarks": source["totalMarks"]})
        with (pymupdf.open(root / files["question"]) as pdf,
              pymupdf.open(root / files["markScheme"]) as scheme_pdf):
            for draft in source["reviewDrafts"]:
                shared_stem, subparts = separate_subparts(
                    draft["rawQuestionText"], draft["subpartMarkAllocations"]
                )
                page_images = []
                for page in draft["questionPdfPages"]:
                    relative_image = Path(".pilot-review/question-pages") / f"{component}-page-{page:02d}.png"
                    target = root / relative_image
                    image_dir.mkdir(parents=True, exist_ok=True)
                    pdf[page - 1].get_pixmap(matrix=pymupdf.Matrix(image_scale, image_scale),
                                             alpha=False).save(target)
                    page_images.append({"pdfPage": page, "localPng": relative_image.as_posix()})
                scheme_images = []
                for page in draft["schemePdfPages"]:
                    relative_image = Path(".pilot-review/scheme-pages") / f"{component}-page-{page:02d}.png"
                    target = root / relative_image
                    scheme_dir.mkdir(parents=True, exist_ok=True)
                    scheme_pdf[page - 1].get_pixmap(matrix=pymupdf.Matrix(image_scale, image_scale),
                                                    alpha=False).save(target)
                    scheme_images.append({"pdfPage": page, "localPng": relative_image.as_posix()})
                bank["questions"].append({
                    "paperKey": source["paperKey"], "component": component,
                    "number": str(draft["question"]), "marks": draft["marks"],
                    "sharedStemExtractionCandidate": shared_stem,
                    "rawQuestionExtraction": draft["rawQuestionText"],
                    "studentPrompt": None, "subparts": subparts,
                    "source": {"questionPdfPages": draft["questionPdfPages"],
                               "schemePdfPages": draft["schemePdfPages"],
                               "reportHeadingCandidatePdfPages": draft["reportCandidatePdfPages"],
                               "questionPageImages": page_images},
                    "markScheme": {"rawExtraction": draft["rawSchemeText"],
                                   "exactSchemePageImages": scheme_images,
                                   "markingPoints": [], "alternatives": [],
                                   "reviewStatus": "exact_rubric_pending"},
                    "examinerReport": {"approvedComments": [],
                                       "reviewStatus": "heading_candidates_only"},
                    "topicMappings": [],
                    "reviewStatus": "not_approved_for_import_or_students",
                })
    if len(bank["questions"]) != 16 or sum(q["marks"] for q in bank["questions"]) != 180:
        raise ValueError("The 1C/2C pilot inventory does not reconcile")
    if sum(len(q["subparts"]) for q in bank["questions"]) != 87:
        raise ValueError("The 1C/2C subpart inventory does not reconcile")
    return bank


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("session_directory", type=Path)
    args = parser.parse_args()
    root = args.session_directory.resolve()
    manifest = json.loads((root / "june-2025-pilot-manifest.json").read_text())
    bank = build(root, manifest)
    output = root / ".pilot-review" / "june-2025-standard-draft-bank.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {output}")
    print("2 papers, 16 unreleased questions, 87 labelled subparts; exact rubrics and topic mappings pending")


if __name__ == "__main__":
    main()
