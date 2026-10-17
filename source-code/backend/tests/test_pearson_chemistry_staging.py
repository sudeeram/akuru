"""Guard the private pilot analysis from becoming an implicit publication path."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "analyze-staged-pearson-chemistry.py"
spec = spec_from_file_location("pearson_staging_analysis", SCRIPT)
module = module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def _bank():
    return {
        "status": "local_draft_unreleased", "studentAccess": False,
        "course": "igcse", "subject": "chemistry",
        "papers": [{"component": "1C"}, {"component": "2C"}],
        "questions": [{
            "paperKey": "pilot-1C", "number": "1", "marks": 2,
            "studentPrompt": None, "topicMappings": [],
            "sharedStemExtractionCandidate": "The particles move in a liquid.",
            "subparts": [{"label": "a", "marks": 2,
                          "extractionCandidate": "Explain particle movement."}],
        }],
    }


def test_analysis_only_suggests_evidence_and_never_creates_mappings():
    report = module.analyze(_bank(), [{"code": "T1"}], [{
        "topicRef": "topic_1", "topicCode": "T1", "topicTitle": "States of matter",
        "contentVersion": 1, "pageNumber": 4,
        "content": "Particles move in a liquid and a gas.",
    }])
    assert report["studentAccess"] is False
    assert report["automaticMappingsCreated"] == 0
    assert report["questions"][0]["coverageStatus"] == "unverified"
    part = report["questions"][0]["subparts"][0]
    assert part["mappingStatus"] == "human_review_required"
    assert part["candidateEvidence"][0]["topicCode"] == "T1"


@pytest.mark.parametrize("change", [
    {"studentAccess": True}, {"status": "released"},
    {"papers": [{"component": "1CR"}, {"component": "2CR"}]},
])
def test_analysis_rejects_nonpilot_or_released_banks(change):
    bank = _bank()
    bank.update(change)
    with pytest.raises(ValueError):
        module.analyze(bank, [], [])
