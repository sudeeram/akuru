from app.services.paragraph_reconstruction import RECONSTRUCTION_VERSION, evaluate_reconstruction, reconstruct_blocks


def line(text: str, sequence: int, *, paragraph: int = 1, column: str = "left",
         kind: str = "paragraph", x: float = .1, y: float | None = None) -> dict:
    top = y if y is not None else .1 + sequence * .03
    return {"kind": kind, "text": text, "latex": None,
        "bbox": {"x0": x, "y0": top, "x1": .45, "y1": top + .02},
        "bboxSpace": "normalized", "method": "ocr", "confidence": .96,
        "needsReview": False, "metadata": {"ocrBlock": 1, "ocrParagraph": paragraph,
            "ocrLine": sequence, "layoutColumn": column}}


def test_reconstructs_same_paragraph_and_preserves_raw_lines():
    result = reconstruct_blocks([line("Particles in a solid are held", 1),
                                 line("together by strong forces.", 2)])
    assert len(result) == 1
    assert result[0]["text"] == "Particles in a solid are held together by strong forces."
    evidence = result[0]["metadata"]["reconstruction"]
    assert evidence["version"] == RECONSTRUCTION_VERSION
    assert [row["text"] for row in evidence["rawLines"]] == [
        "Particles in a solid are held", "together by strong forces."]


def test_protects_columns_lists_captions_and_equations():
    blocks = [line("Left paragraph", 1), line("Right paragraph", 2, column="right"),
              line("• First item", 3, column="right"),
              line("Figure 1.2 Particle arrangement", 4, column="right"),
              line("H2O → H+ + OH-", 5, column="right", kind="equation")]
    result = reconstruct_blocks(blocks)
    assert len(result) == len(blocks)
    assert result[1]["metadata"]["reconstructionBoundary"]["reason"] == "column_boundary"


def test_dehyphenation_is_review_required_and_compounds_are_preserved():
    repaired = reconstruct_blocks([line("evap-", 1), line("oration occurs", 2)])
    assert repaired[0]["text"] == "evaporation occurs"
    assert repaired[0]["needsReview"] is True
    preserved = reconstruct_blocks([line("low-", 1), line("temperature process", 2)])
    assert preserved[0]["text"] == "low-temperature process"


def test_native_multiline_text_is_normalized_without_losing_original():
    block = line("The particles are\nclose together.", 1)
    block["method"] = "native_pdf"
    result = reconstruct_blocks([block])
    assert result[0]["text"] == "The particles are close together."
    assert result[0]["metadata"]["reconstruction"]["rawText"] == "The particles are\nclose together."


def test_chemistry_fixture_reports_accuracy_and_review_reduction():
    blocks = [line("Matter exists as solids, liquids", 1),
              line("and gases under ordinary conditions.", 2),
              line("• Solids have fixed shapes", 3, paragraph=2),
              line("• Liquids flow", 4, paragraph=2)]
    expected = ["Matter exists as solids, liquids and gases under ordinary conditions.",
                "• Solids have fixed shapes", "• Liquids flow"]
    metrics = evaluate_reconstruction([{"blocks": blocks, "expectedParagraphs": expected}])
    assert metrics["paragraphPrecision"] == 1
    assert metrics["paragraphRecall"] == 1
    assert metrics["beforeBlockCount"] == 4 and metrics["afterBlockCount"] == 3
    assert metrics["reviewBlockReduction"] == .25
