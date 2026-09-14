import io
import json
import shutil
import subprocess
from pathlib import Path

import pymupdf as fitz
import pytest
from PIL import Image, ImageDraw

from app.services.document_extraction import extract_document, text_to_latex


FIXTURES = Path(__file__).parent / "fixtures" / "extraction" / "subjects.json"


def make_pdf(heading: str, body: str, *, diagram: bool = False) -> bytes:
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((60, 70), heading, fontsize=20)
    page.insert_text((60, 120), body, fontsize=12)
    page.insert_text((60, 180), "(a) Show your working.", fontsize=12)
    page.insert_text((60, 240), "..............................", fontsize=12)
    if diagram:
        image = Image.new("RGB", (120, 80), "white")
        draw = ImageDraw.Draw(image)
        draw.ellipse((20, 10, 100, 70), outline="black", width=4)
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        page.insert_image(fitz.Rect(330, 90, 480, 190), stream=stream.getvalue())
    content = document.tobytes()
    document.close()
    return content


@pytest.mark.parametrize("fixture", json.loads(FIXTURES.read_text()))
def test_subject_fixtures_preserve_blocks_and_coordinates(fixture) -> None:
    result = extract_document(
        make_pdf(fixture["heading"], fixture["body"], diagram=fixture["subject"] == "Biology"),
        "application/pdf", fixture["subject"], 10, 144, 10, "tesseract",
    )
    page = result["pages"][0]
    kinds = {block["kind"] for block in page["blocks"]}
    assert result["pageCount"] == 1
    assert "heading" in kinds
    assert fixture["expected"] in kinds
    assert "subpart" in kinds
    assert "answer_space" in kinds
    assert all(block["bbox"] and block["method"] and 0 <= block["confidence"] <= 1 for block in page["blocks"])
    if fixture["subject"] == "Maths":
        equation = next(block for block in page["blocks"] if block["kind"] == "equation")
        assert "^{2}" in equation["latex"]
        assert equation["sourceAssetIndex"] is not None
    if fixture["subject"] == "Biology":
        assert "diagram" in kinds
        assert any(asset["kind"] == "embedded_image" for asset in page["assets"])


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_scanned_page_uses_ocr_and_keeps_diagram() -> None:
    image = Image.new("RGB", (1000, 600), "white")
    draw = ImageDraw.Draw(image)
    draw.text((80, 80), "QUESTION 1", fill="black", font_size=42)
    draw.text((80, 160), "Calculate 12 + 8 =", fill="black", font_size=34)
    draw.rectangle((650, 100, 900, 350), outline="black", width=8)
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    document = fitz.open()
    page = document.new_page(width=500, height=300)
    page.insert_image(page.rect, stream=stream.getvalue())
    pdf = document.tobytes()
    document.close()

    result = extract_document(pdf, "application/pdf", "Maths", 5, 144, 40, "tesseract")
    extracted = result["pages"][0]
    assert extracted["method"] == "ocr+native_pdf"
    assert any(block["method"] == "ocr" and "12" in block["text"] for block in extracted["blocks"])
    assert any(block["kind"] == "diagram" for block in extracted["blocks"])


def test_equation_normalization_is_deterministic() -> None:
    assert text_to_latex("x² ≥ 4 × y") == r"x^{2} \\ge  4 \\times  y"


def test_pdf_page_labels_preserve_front_matter_and_printed_page_numbers() -> None:
    document = fitz.open()
    for text in ("Contents", "Cell structure", "Transport"):
        page = document.new_page(width=595, height=842)
        page.insert_text((60, 80), text, fontsize=14)
    document.set_page_labels([
        {"startpage": 0, "prefix": "", "style": "r", "firstpagenum": 1},
        {"startpage": 1, "prefix": "", "style": "D", "firstpagenum": 101},
    ])
    content = document.tobytes()
    document.close()

    result = extract_document(content, "application/pdf", "Biology", 5, 144, 10, "tesseract")
    assert [page["printedPageLabel"] for page in result["pages"]] == ["i", "101", "102"]
    assert [page["pageNumber"] for page in result["pages"]] == [1, 2, 3]


def test_vector_only_diagram_is_retained_as_review_crop() -> None:
    document = fitz.open()
    page = document.new_page(width=500, height=400)
    page.insert_text((40, 50), "1. Label the circuit shown below.", fontsize=12)
    shape = page.new_shape()
    shape.draw_rect(fitz.Rect(100, 120, 380, 300))
    shape.draw_circle(fitz.Point(240, 210), 55)
    shape.finish(width=3)
    shape.commit()
    content = document.tobytes()
    document.close()
    result = extract_document(content, "application/pdf", "Physics", 2, 144, 10, "tesseract")
    extracted = result["pages"][0]
    assert any(block["kind"] == "diagram" and block["method"] == "vector_drawing" for block in extracted["blocks"])
    assert any(asset["kind"] == "diagram_crop" for asset in extracted["assets"])


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_uploaded_image_is_treated_as_one_ocr_page() -> None:
    image = Image.new("RGB", (800, 300), "white")
    ImageDraw.Draw(image).text((50, 80), "SCIENCE QUESTION 2", fill="black", font_size=40)
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    result = extract_document(stream.getvalue(), "image/png", "Physics", 1, 144, 10, "tesseract")
    assert result["pageCount"] == 1
    assert result["pages"][0]["method"].startswith("ocr")
    assert result["pages"][0]["blocks"]


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract is not installed")
def test_french_scan_uses_french_and_english_language_data_when_available() -> None:
    completed = subprocess.run(
        ["tesseract", "--list-langs"], capture_output=True, text=True, check=True,
    )
    if "fra" not in completed.stdout.splitlines():
        pytest.skip("French Tesseract data is not installed")
    image = Image.new("RGB", (900, 280), "white")
    ImageDraw.Draw(image).text((60, 90), "BONJOUR MON ECOLE", fill="black", font_size=44)
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    result = extract_document(stream.getvalue(), "image/png", "French", 1, 144, 10, "tesseract")
    metadata = result["pages"][0]["metadata"]
    assert metadata["languagesUsed"] == ["fra", "eng"]
    assert metadata["languageFallback"] is False
