"""Review and move the June 2025 1C/2C candidate crops to their relevant subparts.

Run as the PostgreSQL OS user with --apply only after deploying the subpart-aware API.
Without --apply this is a read-only verification. No question is approved here.
"""
import argparse
import json

import psycopg


# These assignments were checked against the original June 2025 Pearson PDFs.
# The candidate crops remain unapproved for Admin crop/alt-text review.
PLACEMENTS = {
    "b524e07b-a3ff-4071-bfe8-8913dccdb4ed": {
        "1": {
            "b34c630b-5821-4a89-82c5-4337b5a5e2ce": ["a", "b", "c"],  # atom
            "c10e6d10-483b-4a09-bff8-c8f2ad20d9c7": ["b", "c"],  # results table
        },
        "3": {"51348b68-befe-403c-9632-97d5e9bd93f9": ["a", "b", "c", "d"]},
        "7": {
            "29676d68-0cdc-4fe3-a602-02a6b56bf88e": ["c(i)", "c(ii)", "c(iii)", "d"],
            "111e3bb9-462c-4d91-a42d-a95de2dd456e": ["c(i)", "c(ii)", "c(iii)", "d", "e"],
        },
        "8": {
            "f9b9d05a-fb85-4bf2-a5a8-32e400c933fa": ["a"],  # diamond
            "09a4dacf-0858-4340-9ea3-95510099de4f": ["b"],  # graphite
        },
        "10": {
            "dc0de47c-8d5c-4159-a518-56d1258d0c81": ["a"],  # apparatus
            "91f20a7c-3923-45ec-b964-9681b67148c4": ["b(i)", "b(ii)"],
        },
    },
    "b4fd7a17-e3dd-4403-9799-875e1abb464c": {
        "2": {
            "928c47ca-83ed-4876-aa45-221a6639d6f2": ["c"],  # gas collection apparatus
            "7731e38f-8da3-4563-8881-ed7597c3ccdb": ["c"],  # graph axes
        },
        "3": {
            "b067138f-a8f5-4705-b313-51b29d735d09": ["a(ii)"],  # isotope data
            "74efb4f0-4e06-4c0c-af68-bdd59644a329": ["c"],  # Mg atom
            "9b754f94-642f-4548-aceb-69879f189af5": ["c"],  # O atom
            "0c464880-fbfd-4be2-bfa4-3442b54c4a25": ["d"],  # conductivity
        },
        "5": {
            "27ae8d5b-a7da-4d8c-bc28-925e7550e6c9": ["b"],  # burette reading
            "0cdb1452-1064-4aa5-9322-87d34b1a8f68": ["b"],  # rough titration table
            "96c35b57-76c4-46e8-8332-bdbfc43386d9": ["c(i)", "c(ii)"],  # repeated titrations
        },
    },
}
EXPECTED_QUESTION_COUNTS = {list(PLACEMENTS)[0]: 10, list(PLACEMENTS)[1]: 6}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", default="dbname=akuru user=postgres")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    changes = []
    with psycopg.connect(args.dsn) as connection:
        with connection.transaction():
            for paper_id, expected_count in EXPECTED_QUESTION_COUNTS.items():
                rows = connection.execute("""
                    SELECT q.id, q.number, q.revision, q.status, q.review_data, w.created_by
                    FROM official_paper_review_questions q
                    JOIN official_paper_review_workspaces w ON w.id=q.workspace_id
                    WHERE w.paper_document_id=%s ORDER BY q.number FOR UPDATE OF q
                """, (paper_id,)).fetchall()
                if len(rows) != expected_count:
                    raise RuntimeError(f"{paper_id}: expected {expected_count} questions, found {len(rows)}")
                for row_id, number, revision, status, data, actor_id in rows:
                    if status != "unreviewed":
                        raise RuntimeError(f"{paper_id} Q{number}: status changed to {status}; stop for manual review")
                    assignments = PLACEMENTS[paper_id].get(number, {})
                    if not assignments:
                        if data.get("visualAssetIds") or data.get("candidateVisualAssetIds"):
                            raise RuntimeError(f"{paper_id} Q{number}: unexpected visual(s)")
                        continue
                    parts = data["parts"]
                    labels = {part["label"] for part in parts}
                    if any(not set(targets).issubset(labels) for targets in assignments.values()):
                        raise RuntimeError(f"{paper_id} Q{number}: source subpart labels changed")
                    already = all(set(part.get("visualAssetIds", [])) == {
                        asset_id for asset_id, targets in assignments.items() if part["label"] in targets
                    } for part in parts) and not data.get("visualAssetIds") and not data.get("candidateVisualAssetIds")
                    if already:
                        continue
                    if set(data.get("visualAssetIds", [])) | set(data.get("candidateVisualAssetIds", [])) != set(assignments):
                        raise RuntimeError(f"{paper_id} Q{number}: crop IDs differ from reviewed inventory")
                    if any(part.get("visualAssetIds") for part in parts):
                        raise RuntimeError(f"{paper_id} Q{number}: existing part placement; stop for manual review")
                    for part in parts:
                        part["visualAssetIds"] = [asset_id for asset_id, targets in assignments.items()
                                                   if part["label"] in targets]
                    data["visualAssetIds"] = []
                    data["candidateVisualAssetIds"] = []
                    changes.append((paper_id, number, str(row_id), revision + 1))
                    if args.apply:
                        connection.execute("""
                            UPDATE official_paper_review_questions SET review_data=%s::json, revision=revision+1,
                                reviewed_by=NULL, reviewed_at=NULL, updated_at=now()
                            WHERE id=%s AND revision=%s
                        """, (json.dumps(data), row_id, revision))
                        connection.execute("""
                            INSERT INTO audit_events(id,actor_id,action,target_type,target_id,event_data,created_at)
                            VALUES(gen_random_uuid(),%s,'official_review.visual_subparts_reassessed',
                                   'official_question',%s,%s,now())
                        """, (actor_id, str(row_id), json.dumps({
                            "paperDocumentId": paper_id, "questionNumber": number,
                            "placements": assignments, "approved": False})))
    print(json.dumps({"mode": "apply" if args.apply else "dry-run", "changedQuestions": changes}, indent=2))


if __name__ == "__main__":
    main()
