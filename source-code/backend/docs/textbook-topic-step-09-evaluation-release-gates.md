# Step 9 — Textbook-topic evaluation and release gates

## Automated gates

The existing evaluation service now treats `topic_citation` as a required assessment corpus category. A reviewed corpus must validate exact topic isolation and all required citation fields before it can be approved. Mapping evaluation now accepts topic references as the authoritative vocabulary.

The automated suite covers schema constraints, authorization, family isolation, immutable snapshots, cumulative coverage, cross-subject rejections, topic eligibility, mastery aggregation and citation isolation. Extraction fixtures cover English, French, Science, ICT and Maths including equations, diagrams and tables.

## Topic-PDF quality gate

`GET /api/v1/admin/textbooks/{textbookRef}/topics/{topicRef}/quality` is Admin-only. It returns one report row for each attached topic PDF and checks:

- complete extracted-page coverage;
- mean OCR confidence of at least 90%;
- reviewed and retained equation blocks;
- reviewed and retained image/diagram blocks;
- printed-page labels for every page; and
- reviewed, topic-scoped retrieval evidence.

Publication evaluates the same report and fails closed when any topic PDF misses a mandatory threshold. Admins resolve exceptions by reviewing and saving the relevant page or block in the existing extraction-review workflow; those actions are already audit logged. The report never returns storage keys, provider credentials or internal database identifiers.

## Pilot procedure

Start with Chemistry Topics 1 and 2. Upload their scanned parts, complete each quality report, publish only when every check passes, then run the approved topic-citation evaluation corpus. Verify that retrieval returns only the active reviewed Chemistry topic and cites its exact group, document and page before the remaining collection is processed.
