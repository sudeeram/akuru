#!/usr/bin/env python3
"""Record prepared analysis metadata through the Admin API; never edit question content.

Dry-run by default. Keep payloads and credential files outside Git. A baseline is
mandatory so a newly prepared assessment cannot silently describe changed content.
"""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import quote, urlparse

import httpx
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.schemas.paper_analysis import RecordQuestionAnalysis  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    origin = args.base_url.rstrip("/")
    parsed = urlparse(origin)
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise SystemExit("Use a plain server origin without credentials, query or path.")
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}):
        raise SystemExit("Use HTTPS for remote AKURU servers.")
    credentials = dotenv_values(args.env_file)
    baseline = json.loads(args.baseline.read_text())
    prepared = json.loads(args.input.read_text())
    paper_id = prepared["paperId"]
    if baseline["paperDocumentId"] != paper_id:
        raise SystemExit("The baseline belongs to a different paper.")
    with httpx.Client(base_url=origin + "/api/v1/", headers={"Origin": origin}, timeout=90) as client:
        def request(method, path, body=None):
            response = client.request(method, path, json=body)
            if response.status_code >= 400:
                # Error envelopes have no credentials; never print request headers/body.
                error = response.json().get("error", {})
                raise RuntimeError(f"{method} {path}: HTTP {response.status_code} {error.get('code', '')} {error.get('message', '')}")
            return None if response.status_code == 204 else response.json()
        login = request("POST", "auth/login", {"username": credentials["AKURU_ADMIN_USERNAME"],
                                               "password": credentials["AKURU_ADMIN_PASSWORD"]})
        client.headers["X-CSRF-Token"] = login["csrfToken"]
        try:
            root = f"admin/official-paper-reviews/{quote(paper_id, safe='')}"
            before = request("GET", root)
            prior = {q["number"]: q for q in baseline["questions"]}
            current = {q["number"]: q for q in before["questions"]}
            writes = []
            skipped = 0
            numbers = set()
            for assessment in prepared["assessments"]:
                assessment = dict(assessment)
                number = assessment.pop("number")
                if number in numbers:
                    raise RuntimeError("The batch repeats a question number.")
                numbers.add(number)
                original, latest = prior[number], current[number]
                for field in ("revision", "status", "data", "reviewedBy", "reviewedAt"):
                    if original[field] != latest[field]:
                        raise RuntimeError(f"Q{number} changed since its source comparison; reassess before writing.")
                payload = RecordQuestionAnalysis.model_validate({**assessment,
                    "expectedQuestionRevision": latest["revision"],
                    "expectedAnalysisVersion": latest["analysisVersion"],
                    "expectedContentHash": latest["analysisContentHash"]}).model_dump(mode="json")
                previous_analysis = latest.get('accuracyAnalysis' if payload['stage'] == 'accuracy' else 'extractionAnalysis')
                if previous_analysis and previous_analysis['isCurrent'] and all(
                    previous_analysis[field] == payload[field]
                    for field in ('stage', 'methodVersion', 'provenance', 'question', 'parts')
                ):
                    skipped += 1
                    continue
                writes.append((number, payload))
            print(f"Validated {len(writes)} new assessments; {skipped} identical current assessments skipped. Execute: {args.execute}")
            results = []
            if args.execute:
                for number, payload in writes:
                    result = request("POST", root + f"/questions/{quote(number, safe='')}/analyses", payload)
                    results.append(result)
                    print(f"Q{number}: accuracy confidence {result['question']['percent']}%, analysis v{result['version']}")
                after = request("GET", root)
                for previous in before["questions"]:
                    following = next(q for q in after["questions"] if q["number"] == previous["number"])
                    for field in ("revision", "status", "data", "reviewedBy", "reviewedAt"):
                        if previous[field] != following[field]:
                            raise RuntimeError(f"Q{previous['number']} content or approval changed during the batch. Inspect before continuing.")
                if args.evidence:
                    args.evidence.parent.mkdir(parents=True, exist_ok=True)
                    args.evidence.write_text(json.dumps({"before": before, "analyses": results, "after": after}, indent=2))
                print("Verified every question's content, revision, approval and reviewer metadata stayed unchanged.")
        finally:
            request("POST", "auth/logout")


if __name__ == "__main__":
    main()
