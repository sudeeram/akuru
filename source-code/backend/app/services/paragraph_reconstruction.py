from __future__ import annotations

import re
from copy import deepcopy


RECONSTRUCTION_VERSION = "paragraph-reconstruction-1.0.0"
PROTECTED_KINDS = {"heading", "table", "equation", "image", "diagram", "question", "subpart", "answer_space"}
LIST_RE = re.compile(r"^\s*(?:[•●▪◦]|[-–—]\s|\(?\d+[.)]\s|\(?[a-zA-Z][.)]\s)")
CAPTION_RE = re.compile(r"^\s*(?:figure|fig\.?|table|diagram)\s+\d", re.I)
TERMINAL_RE = re.compile(r"[.!?:;][\"'’”)]?$")
PRESERVE_HYPHEN_PREFIXES = {"low", "high", "well", "non", "self", "two", "three", "four"}


def _bbox_union(left: dict, right: dict) -> dict:
    return {"x0": min(float(left.get("x0", 0)), float(right.get("x0", 0))),
            "y0": min(float(left.get("y0", 0)), float(right.get("y0", 0))),
            "x1": max(float(left.get("x1", 0)), float(right.get("x1", 0))),
            "y1": max(float(left.get("y1", 0)), float(right.get("y1", 0)))}


def _join_text(left: str, right: str) -> tuple[str, dict]:
    left, right = left.rstrip(), right.lstrip()
    if left.endswith("-") and right and right[0].islower():
        prior = re.search(r"([A-Za-z]+)-$", left)
        prefix = prior.group(1).lower() if prior else ""
        if prefix in PRESERVE_HYPHEN_PREFIXES:
            return left + right, {"kind": "preserve_hyphen", "confidence": 0.9,
                "reason": "recognized_compound_prefix", "requiresReview": False}
        if prefix not in PRESERVE_HYPHEN_PREFIXES:
            return left[:-1] + right, {"kind": "dehyphenate", "confidence": 0.78,
                "reason": "lowercase_word_continues_after_line_end_hyphen", "requiresReview": True}
    return f"{left} {right}".strip(), {"kind": "space", "confidence": 0.96,
        "reason": "paragraph_lines_joined_with_space", "requiresReview": False}


def _raw_line(block: dict, index: int) -> dict:
    metadata = block.get("metadata", {})
    return {"sourceIndex": index, "text": block.get("text", ""),
        "bbox": deepcopy(block.get("bbox", {})), "confidence": block.get("confidence", 0),
        "ocrBlock": metadata.get("ocrBlock"), "ocrParagraph": metadata.get("ocrParagraph"),
        "ocrLine": metadata.get("ocrLine"), "layoutColumn": metadata.get("layoutColumn")}


def _decision(left: dict, right: dict) -> dict:
    lm, rm = left.get("metadata", {}), right.get("metadata", {})
    if left.get("kind") in PROTECTED_KINDS or right.get("kind") in PROTECTED_KINDS:
        return {"join": False, "confidence": 1.0, "reason": "protected_content_type"}
    if LIST_RE.match(left.get("text", "")) or LIST_RE.match(right.get("text", "")):
        return {"join": False, "confidence": 0.98, "reason": "list_boundary"}
    if CAPTION_RE.match(left.get("text", "")) or CAPTION_RE.match(right.get("text", "")):
        return {"join": False, "confidence": 0.98, "reason": "caption_boundary"}
    if lm.get("layoutColumn") != rm.get("layoutColumn"):
        return {"join": False, "confidence": 1.0, "reason": "column_boundary"}
    lb, rb = left.get("bbox", {}), right.get("bbox", {})
    height = max(float(lb.get("y1", 0)) - float(lb.get("y0", 0)),
                 float(rb.get("y1", 0)) - float(rb.get("y0", 0)), 0.001)
    gap = float(rb.get("y0", 0)) - float(lb.get("y1", 0))
    indent = abs(float(lb.get("x0", 0)) - float(rb.get("x0", 0)))
    same_paragraph = lm.get("ocrBlock") is not None and lm.get("ocrBlock") == rm.get("ocrBlock") and lm.get("ocrParagraph") == rm.get("ocrParagraph")
    if same_paragraph and gap <= height * 1.8 and indent <= 0.06:
        return {"join": True, "confidence": 0.97, "reason": "same_ocr_paragraph_and_normal_spacing"}
    if gap <= height * 0.9 and indent <= 0.025 and not TERMINAL_RE.search(left.get("text", "")):
        return {"join": True, "confidence": 0.84, "reason": "aligned_continuation_without_terminal_punctuation"}
    return {"join": False, "confidence": 0.91, "reason": "paragraph_boundary_preserved"}


def _normalize_native(block: dict, source_index: int) -> dict:
    lines = [line.strip() for line in block.get("text", "").splitlines() if line.strip()]
    if len(lines) <= 1 or block.get("kind") in PROTECTED_KINDS:
        return block
    text, joins = lines[0], []
    for line in lines[1:]:
        text, join = _join_text(text, line); joins.append(join)
    result = deepcopy(block); result["text"] = text
    result["needsReview"] = bool(result.get("needsReview") or any(row["requiresReview"] for row in joins))
    result.setdefault("metadata", {})["reconstruction"] = {
        "version": RECONSTRUCTION_VERSION, "rawText": block.get("text", ""),
        "rawLines": [{"sourceIndex": source_index, "lineIndex": index + 1, "text": line,
            "bbox": deepcopy(block.get("bbox", {})), "confidence": block.get("confidence", 0)}
            for index, line in enumerate(lines)],
        "decisions": joins, "confidence": min((row["confidence"] for row in joins), default=1.0)}
    return result


def reconstruct_blocks(blocks: list[dict]) -> list[dict]:
    """Build deterministic paragraphs while retaining every source line."""
    normalized = [_normalize_native(deepcopy(block), index) for index, block in enumerate(blocks)]
    result: list[dict] = []
    for source_index, block in enumerate(normalized):
        block.setdefault("metadata", {}).setdefault("sourceLine", _raw_line(block, source_index))
        if not result:
            result.append(block); continue
        previous = result[-1]; boundary = _decision(previous, block)
        if not boundary["join"]:
            block["metadata"].setdefault("reconstructionBoundary", {"version": RECONSTRUCTION_VERSION, **boundary})
            result.append(block); continue
        prior_meta = previous.setdefault("metadata", {}); existing = prior_meta.get("reconstruction", {})
        raw_lines = existing.get("rawLines") or [prior_meta.get("sourceLine", _raw_line(previous, source_index - 1))]
        joined, join_style = _join_text(previous.get("text", ""), block.get("text", ""))
        previous["text"] = joined; previous["bbox"] = _bbox_union(previous.get("bbox", {}), block.get("bbox", {}))
        previous["confidence"] = round(min(float(previous.get("confidence", 0)), float(block.get("confidence", 0)), boundary["confidence"], join_style["confidence"]), 4)
        previous["needsReview"] = bool(previous.get("needsReview") or block.get("needsReview") or join_style["requiresReview"])
        prior_meta["reconstruction"] = {"version": RECONSTRUCTION_VERSION,
            "rawText": "\n".join(row.get("text", "") for row in [*raw_lines, _raw_line(block, source_index)]),
            "rawLines": [*raw_lines, _raw_line(block, source_index)],
            "decisions": [*existing.get("decisions", []), {**boundary, **join_style}],
            "confidence": previous["confidence"]}
    for sequence, block in enumerate(result, 1):
        block.setdefault("metadata", {})["layoutReadingOrder"] = sequence
    return result


def evaluate_reconstruction(cases: list[dict]) -> dict:
    """Measure exact paragraph and boundary quality for reviewed fixtures."""
    expected_total = 0; predicted_total = 0; exact_total = 0; correct_boundaries = 0; boundary_total = 0
    before_blocks = 0; after_blocks = 0
    for case in cases:
        expected = case["expectedParagraphs"]
        predicted = [block["text"] for block in reconstruct_blocks(case["blocks"])]
        before_blocks += len(case["blocks"]); after_blocks += len(predicted)
        expected_total += len(expected); predicted_total += len(predicted)
        exact_total += sum(value in expected for value in predicted)
        expected_boundaries = set(expected[:-1]); predicted_boundaries = set(predicted[:-1])
        boundary_total += max(len(expected) - 1, 0)
        correct_boundaries += len(expected_boundaries & predicted_boundaries)
    precision = exact_total / predicted_total if predicted_total else 1.0
    recall = exact_total / expected_total if expected_total else 1.0
    return {"paragraphPrecision": round(precision, 4), "paragraphRecall": round(recall, 4),
            "boundaryAccuracy": round(correct_boundaries / boundary_total, 4) if boundary_total else 1.0,
            "beforeBlockCount": before_blocks, "afterBlockCount": after_blocks,
            "reviewBlockReduction": round(1 - after_blocks / before_blocks, 4) if before_blocks else 0.0}
