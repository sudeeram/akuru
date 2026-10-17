#!/usr/bin/env python3
"""Produce a conservative, unpublished coverage triage for the June 2025 1C/2C pilot.

This is a reviewer decision record, not an AKURU topic mapping or a rubric import.
It deliberately leaves every student/import gate closed.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


# The currently published textbook has only Topic 1 (States of Matter) and
# Topic 2 (Elements, Compounds and Mixtures). The remaining questions assess
# material beyond those two chapters, even where lexical suggestions overlap.
OUTSIDE_REASON = {
    ("1C", "1"): "Atomic structure, subatomic particles and electronic configuration are not taught in the published chapters.",
    ("1C", "2"): "Group 1 lithium reactions, alkalinity and flame tests need later content.",
    ("1C", "4"): "Ionic formulae, charges, formula mass, percentages and balancing need later content.",
    ("1C", "5"): "Alkanes, combustion, isomerism and chain-length effects need organic chemistry content.",
    ("1C", "6"): "Rusting, reactivity, ion tests, redox and yield need later content.",
    ("1C", "7"): "Neutralisation and its temperature/graph experiment are outside the published chapters.",
    ("1C", "8"): "Diamond and graphite structure and bonding need later content.",
    ("1C", "9"): "Covalent bonding, polymers and organic reactions need later content.",
    ("1C", "10"): "Fuel-energy calorimetry and enthalpy calculations need later content.",
    ("2C", "2"): "Rates, collision theory and reaction profiles need later content.",
    ("2C", "3"): "Isotopes, ionic bonding, conductivity and electrolysis need later content.",
    ("2C", "4"): "Ethanol, ethanoic acid and ester reactions need organic chemistry content.",
    ("2C", "5"): "Acid-base titration, stoichiometry and crystal preparation need later content.",
    ("2C", "6"): "Equilibrium, conditions and yield calculations need later content.",
}

TOPIC_2 = "topic_94eb1d136d68435b9a1c1a3aa8cb0b35"
SUPPORTED = "supported_by_published_topic"
UNCERTAIN = "partial_or_uncertain"
OUTSIDE = "outside_published_topics"

SPECIAL = {
    ("1C", "3", "a"): (SUPPORTED, [10], "Topic 2 explicitly teaches pencil start lines and why ink moves with solvent."),
    ("1C", "3", "b"): (SUPPORTED, [11], "Topic 2 links furthest-travelling spots to solubility in solvent."),
    ("1C", "3", "c"): (SUPPORTED, [12], "Topic 2 covers spot count and the possibility of unresolved dyes."),
    ("1C", "3", "d"): (SUPPORTED, [13], "Topic 2 explains Rf as a distance ratio; the source chromatogram remains essential."),
    ("2C", "1", "a(i)"): (SUPPORTED, [3], "Topic 2 defines compounds and explicitly uses water as an example."),
    ("2C", "1", "a(ii)"): (UNCERTAIN, [3, 4], "Mixtures are taught, but the reviewed text does not identify petrol specifically as a mixture."),
    ("2C", "1", "a(iii)"): (OUTSIDE, [], "The reviewed text does not teach diatomic fluorine or the diatomic-molecule classification."),
    ("2C", "1", "a(iv)"): (UNCERTAIN, [2, 3], "Elements are taught, but identifying calcium as a metal needs additional Periodic Table knowledge."),
    ("2C", "1", "b(i)"): (UNCERTAIN, [4, 8], "Topic 2 teaches fractional distillation and mentions crude oil, but does not explicitly teach crude-oil fractions."),
    ("2C", "1", "b(ii)"): (OUTSIDE, [], "The reviewed text does not cover kerosene uses."),
}


def make_review(bank: dict, context: dict) -> dict:
    if bank.get("status") != "local_draft_unreleased" or bank.get("studentAccess") is not False:
        raise ValueError("Expected the unreleased pilot bank")
    if (bank.get("course"), bank.get("subject")) != ("igcse", "chemistry"):
        raise ValueError("Expected iGCSE Chemistry")
    if [paper["component"] for paper in bank["papers"]] != ["1C", "2C"]:
        raise ValueError("Expected only standard 1C and 2C")
    topic = next((t for t in context["topics"] if t["publicRef"] == TOPIC_2), None)
    if not topic or len(context["topics"]) != 2:
        raise ValueError("Published topic set changed; review decisions must be revisited")
    available_pages = {chunk["pageNumber"] for chunk in context["chunks"] if chunk["topicRef"] == TOPIC_2}
    content_versions = {chunk["contentVersion"] for chunk in context["chunks"] if chunk["topicRef"] == TOPIC_2}
    if len(content_versions) != 1:
        raise ValueError("Expected one active published Topic 2 content version")
    if not all(set(pages).issubset(available_pages) for _, pages, _ in SPECIAL.values()):
        raise ValueError("Required published Topic 2 evidence pages are missing")

    rows = []
    question_summaries = []
    seen_special = set()
    seen_outside = set()
    for question in bank["questions"]:
        key = (question["component"], question["number"])
        question_rows = []
        for part in question["subparts"]:
            part_key = (*key, part["label"])
            if part_key in SPECIAL:
                seen_special.add(part_key)
                status, pages, reason = SPECIAL[part_key]
            else:
                if key not in OUTSIDE_REASON:
                    raise ValueError(f"Unclassified subpart: {part_key}")
                seen_outside.add(key)
                status, pages, reason = OUTSIDE, [], OUTSIDE_REASON[key]
            row = {
                "paperKey": question["paperKey"], "component": key[0], "question": key[1],
                "subpart": part["label"], "marks": part["marks"], "coverageTriage": status,
                "candidateTopicRef": TOPIC_2 if pages else None,
                "publishedTopicContentVersion": next(iter(content_versions)) if pages else None,
                "textbookExtractionPages": pages, "reason": reason,
                "questionPdfPages": question["source"]["questionPdfPages"],
                "schemePdfPages": question["source"]["schemePdfPages"],
                "rubricReview": "pending", "studentAccess": False,
            }
            rows.append(row)
            question_rows.append(row)
        question_summaries.append({
            "component": key[0], "question": key[1], "marks": question["marks"],
            "wholeQuestionWithinPublishedTopics": all(r["coverageTriage"] == SUPPORTED for r in question_rows),
            "readyForImport": False, "studentAccess": False,
        })
    if seen_special != set(SPECIAL) or seen_outside != set(OUTSIDE_REASON):
        raise ValueError("Review decisions do not cover the expected bank")
    if len(rows) != 87 or len(question_summaries) != 16 or sum(r["marks"] for r in rows) != 180:
        raise ValueError("Pilot question/mark totals changed")
    return {
        "reviewType": "human_coverage_triage_not_import", "studentAccess": False,
        "topicSnapshot": context["topics"], "questionSummaries": question_summaries,
        "subparts": rows,
        "caveat": "Evidence pages refer to extracted PDF pages, not verified printed-page labels. Wording, full rubric and examiner guidance remain pending except the source spot-check noted in the review document.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("draft_bank", type=Path)
    parser.add_argument("published_context", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review = make_review(json.loads(args.draft_bank.read_text()),
                         json.loads(args.published_context.read_text()))
    args.output.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n")
    csv_path = args.output.with_suffix(".csv")
    with csv_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=review["subparts"][0].keys())
        writer.writeheader()
        writer.writerows(review["subparts"])
    print(f"Wrote {len(review['subparts'])} conservative subpart decisions and 16 question summaries")


if __name__ == "__main__":
    main()
