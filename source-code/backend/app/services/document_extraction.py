from __future__ import annotations

import csv
import io
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import pymupdf as fitz
from PIL import Image

from app.services.document_processing_types import ProcessingFailure


QUESTION_RE = re.compile(r"^\s*(?:question\s+)?\d+[.)]\s+", re.IGNORECASE)
SUBPART_RE = re.compile(r"^\s*(?:\([a-zivx]+\)|[a-z][.)])\s+", re.IGNORECASE)
MATH_RE = re.compile(r"(?:[=±×÷√∑∫≤≥]|\b(?:sin|cos|tan|log)\b|\w\s*[²³]|\w\s*\^\s*\d)", re.IGNORECASE)
ANSWER_RE = re.compile(r"(?:_{3,}|\.{5,}|\[\s*\d+\s*marks?\s*\])", re.IGNORECASE)


def bbox_dict(box) -> dict[str, float]:
    x0, y0, x1, y1 = (float(value) for value in box)
    return {"x0": x0, "y0": y0, "x1": x1, "y1": y1}


def classify_text(text: str, font_size: float, median_font_size: float) -> str:
    stripped = text.strip()
    if QUESTION_RE.match(stripped):
        return "question"
    if SUBPART_RE.match(stripped):
        return "subpart"
    if ANSWER_RE.search(stripped):
        return "answer_space"
    if MATH_RE.search(stripped):
        return "equation"
    if stripped and (font_size >= median_font_size * 1.25 or (len(stripped) < 90 and stripped.isupper())):
        return "heading"
    return "paragraph"


def text_to_latex(text: str) -> str:
    latex = text.strip()
    replacements = {
        "×": r"\\times ", "÷": r"\\div ", "±": r"\\pm ", "≤": r"\\le ",
        "≥": r"\\ge ", "√": r"\\sqrt{}", "²": "^{2}", "³": "^{3}",
    }
    for source, target in replacements.items():
        latex = latex.replace(source, target)
    return latex


def _render_page(page: fitz.Page, dpi: int, clip: fitz.Rect | None = None) -> bytes:
    pixmap = page.get_pixmap(dpi=dpi, alpha=False, clip=clip)
    return pixmap.tobytes("png")


def _available_languages(command: str) -> set[str]:
    try:
        result = subprocess.run(
            [command, "--list-langs"], capture_output=True, text=True, timeout=10, check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProcessingFailure("ocr_unavailable", "Tesseract OCR is not available to the document worker.") from exc
    return {line.strip() for line in result.stdout.splitlines()[1:] if line.strip()}


def _ocr_blocks(png: bytes, command: str, subject_id: str) -> tuple[list[dict], dict]:
    available = _available_languages(command)
    wanted = ["fra", "eng"] if subject_id.lower() == "french" else ["eng"]
    selected = [language for language in wanted if language in available]
    if not selected:
        raise ProcessingFailure("ocr_language_unavailable", "No configured OCR language is installed.")
    with tempfile.TemporaryDirectory(prefix="akuru-ocr-") as directory:
        image_path = Path(directory) / "page.png"
        image_path.write_bytes(png)
        try:
            result = subprocess.run(
                [command, str(image_path), "stdout", "-l", "+".join(selected), "--psm", "6", "tsv"],
                capture_output=True, text=True, timeout=60, check=True,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ProcessingFailure("ocr_failed", "Tesseract could not process this page.") from exc
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in csv.DictReader(io.StringIO(result.stdout), delimiter="\t"):
        text = (row.get("text") or "").strip()
        try:
            confidence = float(row.get("conf") or -1)
        except ValueError:
            confidence = -1
        if not text or confidence < 0:
            continue
        grouped[(row["block_num"], row["par_num"], row["line_num"])].append({**row, "confidence": confidence})
    width, height = Image.open(io.BytesIO(png)).size
    blocks = []
    for words in grouped.values():
        left = min(int(word["left"]) for word in words)
        top = min(int(word["top"]) for word in words)
        right = max(int(word["left"]) + int(word["width"]) for word in words)
        bottom = max(int(word["top"]) + int(word["height"]) for word in words)
        text = " ".join(word["text"] for word in words)
        confidence = sum(word["confidence"] for word in words) / len(words) / 100
        kind = classify_text(text, 10, 10)
        block = {
            "kind": kind,
            "text": text,
            "latex": text_to_latex(text) if MATH_RE.search(text) else None,
            "bbox": {"x0": left / width, "y0": top / height, "x1": right / width, "y1": bottom / height},
            "bboxSpace": "normalized",
            "method": "ocr",
            "confidence": round(max(0, min(confidence, 1)), 4),
            "needsReview": confidence < 0.85 or bool(MATH_RE.search(text)),
        }
        blocks.append(block)
        if MATH_RE.search(text) and kind != "equation":
            blocks.append({**block, "kind": "equation", "needsReview": True})
    return blocks, {"languagesRequested": wanted, "languagesUsed": selected, "languageFallback": selected != wanted}


def _native_blocks(page: fitz.Page, dpi: int) -> tuple[list[dict], list[dict]]:
    raw = page.get_text("dict", sort=True)
    sizes = [
        float(span.get("size", 0)) for block in raw.get("blocks", []) if block.get("type") == 0
        for line in block.get("lines", []) for span in line.get("spans", []) if span.get("text", "").strip()
    ]
    median = sorted(sizes)[len(sizes) // 2] if sizes else 10.0
    blocks: list[dict] = []
    assets: list[dict] = []
    for block in raw.get("blocks", []):
        if block.get("type") == 0:
            spans = [span for line in block.get("lines", []) for span in line.get("spans", [])]
            text = "\n".join(
                "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                for line in block.get("lines", [])
            ).strip()
            if not text:
                continue
            max_size = max((float(span.get("size", median)) for span in spans), default=median)
            kind = classify_text(text, max_size, median)
            source_asset_index = None
            has_math = bool(MATH_RE.search(text))
            if has_math:
                crop = _render_page(page, dpi, fitz.Rect(block["bbox"]))
                source_asset_index = len(assets)
                assets.append({"kind": "equation_crop", "mimeType": "image/png", "content": crop, "bbox": bbox_dict(block["bbox"])})
            blocks.append({
                "kind": kind, "text": text, "latex": text_to_latex(text) if kind == "equation" else None,
                "bbox": bbox_dict(block["bbox"]), "bboxSpace": "pdf_points", "method": "native_pdf",
                "confidence": 0.99, "needsReview": kind == "equation", "sourceAssetIndex": source_asset_index,
            })
            if has_math and kind != "equation":
                blocks.append({
                    "kind": "equation", "text": text, "latex": text_to_latex(text),
                    "bbox": bbox_dict(block["bbox"]), "bboxSpace": "pdf_points",
                    "method": "native_pdf", "confidence": 0.8, "needsReview": True,
                    "sourceAssetIndex": source_asset_index,
                })
        elif block.get("type") == 1:
            box = fitz.Rect(block["bbox"])
            crop = _render_page(page, dpi, box)
            raw_image = block.get("image")
            if raw_image:
                extension = str(block.get("ext") or "bin").lower()
                embedded_mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
                    extension, "application/octet-stream"
                )
                assets.append({
                    "kind": "embedded_image", "mimeType": embedded_mime,
                    "content": raw_image, "bbox": bbox_dict(box),
                })
            asset_index = len(assets)
            assets.append({
                "kind": "diagram_crop", "mimeType": "image/png", "content": crop,
                "bbox": bbox_dict(box),
            })
            blocks.append({
                "kind": "diagram", "text": "", "latex": None, "bbox": bbox_dict(box),
                "bboxSpace": "pdf_points", "method": "native_pdf_image", "confidence": 0.8,
                "needsReview": True, "sourceAssetIndex": asset_index,
            })
    try:
        tables = page.find_tables()
    except Exception:
        tables = None
    for table in tables.tables if tables else []:
        blocks.append({
            "kind": "table", "text": "\n".join(" | ".join(cell or "" for cell in row) for row in table.extract()),
            "latex": None, "bbox": bbox_dict(table.bbox), "bboxSpace": "pdf_points",
            "method": "native_pdf_table", "confidence": 0.9, "needsReview": False,
        })
    try:
        drawing_regions = page.cluster_drawings()
    except Exception:
        drawing_regions = []
    image_boxes = [
        fitz.Rect(*(block["bbox"][key] for key in ("x0", "y0", "x1", "y1")))
        for block in blocks if block["kind"] == "diagram"
    ]
    for region in drawing_regions:
        box = fitz.Rect(region)
        if box.width < 30 or box.height < 30 or any(box.intersects(image_box) for image_box in image_boxes):
            continue
        crop = _render_page(page, dpi, box)
        asset_index = len(assets)
        assets.append({
            "kind": "diagram_crop", "mimeType": "image/png", "content": crop,
            "bbox": bbox_dict(box),
        })
        blocks.append({
            "kind": "diagram", "text": "", "latex": None, "bbox": bbox_dict(box),
            "bboxSpace": "pdf_points", "method": "vector_drawing", "confidence": 0.7,
            "needsReview": True, "sourceAssetIndex": asset_index,
        })
    blocks.sort(key=lambda item: (item["bbox"]["y0"], item["bbox"]["x0"]))
    return blocks, assets


def extract_document(
    content: bytes,
    mime_type: str,
    subject_id: str,
    max_pages: int,
    render_dpi: int,
    ocr_min_characters: int,
    tesseract_command: str,
) -> dict:
    try:
        document = fitz.open(stream=content, filetype="pdf" if mime_type == "application/pdf" else None)
    except Exception as exc:
        raise ProcessingFailure("document_open_failed", "The document could not be opened safely.") from exc
    if document.page_count < 1:
        raise ProcessingFailure("empty_document", "The document contains no pages.")
    if document.page_count > max_pages:
        raise ProcessingFailure(
            "page_limit_exceeded",
            f"The document contains {document.page_count} pages; the processing limit is {max_pages}.",
        )
    pages = []
    review_count = 0
    try:
        for page_number, page in enumerate(document, 1):
            rendered = _render_page(page, render_dpi)
            blocks, assets = _native_blocks(page, render_dpi)
            native_text = "\n".join(block["text"] for block in blocks if block["text"])
            ocr_metadata = {}
            method = "native_pdf"
            if len(native_text.strip()) < ocr_min_characters:
                visual_blocks = [block for block in blocks if block["kind"] in {"image", "diagram"}]
                ocr_blocks, ocr_metadata = _ocr_blocks(rendered, tesseract_command, subject_id)
                rendered_image = Image.open(io.BytesIO(rendered))
                for block in ocr_blocks:
                    if block["kind"] != "equation":
                        continue
                    box = block["bbox"]
                    crop = rendered_image.crop((
                        int(box["x0"] * rendered_image.width), int(box["y0"] * rendered_image.height),
                        int(box["x1"] * rendered_image.width), int(box["y1"] * rendered_image.height),
                    ))
                    crop_stream = io.BytesIO()
                    crop.save(crop_stream, format="PNG")
                    block["sourceAssetIndex"] = len(assets)
                    assets.append({
                        "kind": "equation_crop", "mimeType": "image/png",
                        "content": crop_stream.getvalue(), "bbox": box, "bboxSpace": "normalized",
                    })
                blocks = ocr_blocks + visual_blocks
                blocks.sort(key=lambda item: (item["bbox"]["y0"], item["bbox"]["x0"]))
                method = "ocr+native_pdf" if visual_blocks else "ocr"
            page_review = not blocks or ocr_metadata.get("languageFallback", False) or any(
                block["needsReview"] for block in blocks
            )
            review_count += sum(1 for block in blocks if block["needsReview"])
            pages.append({
                "pageNumber": page_number,
                "widthPoints": float(page.rect.width),
                "heightPoints": float(page.rect.height),
                "render": rendered,
                "nativeText": native_text,
                "method": method,
                "confidence": min((block["confidence"] for block in blocks), default=0),
                "needsReview": page_review,
                "metadata": ocr_metadata,
                "blocks": blocks,
                "assets": assets,
            })
    finally:
        document.close()
    return {
        "pageCount": len(pages), "contentType": mime_type, "renderDpi": render_dpi,
        "blockCount": sum(len(page["blocks"]) for page in pages),
        "reviewFlagCount": review_count + sum(1 for page in pages if page["needsReview"]),
        "pages": pages,
    }
