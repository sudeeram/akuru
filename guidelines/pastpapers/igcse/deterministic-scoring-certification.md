# Source-based deterministic scoring certification

Created: 2026-11-18

Apply this after the question, full marking-scheme row (including continued pages) and available examiner guidance have been compared. The marking scheme governs credit; examiner examples do not introduce new allowances. Keep unresolved internal scheme contradictions explicit.

1. Record official maximum, each independent criterion, alternatives, any-N caps, dependencies, combined responses and mutually exclusive full/partial outcomes. Weighted alternatives must not add together.
2. Determine response grammar before selecting an engine: exact numeric final; explicit labels; reviewed finite choice/name; atomic member set; or unsupported semantic/drawing response. Unknown valid paraphrases must refer for review, not score zero.
3. Encode only source-authorised precision, units, omission of units, aliases, exclusions, calculation stages and operands. Keep numerical equality separate from significant-figure compliance. Do not borrow the precision rule from another question.
4. Require exact paper and scheme evidence and approved visuals where relevant. Preserve source wording and record every interpretation separately. A source confidence above 75% does not establish scoring readiness.
5. Prepare synthetic actual answers with independently reviewed expected marks/credited criterion IDs. Cover every full/partial/zero outcome, every explicit source allowance, wrong magnitude/sign/denominator, units, precision, conflicting answers, labels in wrong slots, duplicate fields and unsupported grammar. Include held-out examples and abstentions. Do not use Student transcripts as reusable fixtures.
6. Run the deployed matcher and allocator through the authenticated validation API. A client-supplied pass, mocked marking decision or local allocation-only test is insufficient. Compare the engine hash. Store the immutable validation receipt and distinguish deterministic rule execution from statistical confidence.
7. Let the server derive automatic readiness from a current passing certificate. Revalidate after relevant rules, source content or engine policy changes. Preserve historical results and approvals; do not silently recertify legacy automatic items.
8. Independently check source accuracy, curriculum, visuals, independent answerability and release gates. A scoring pass does not itself publish a formal exam or override an explicit Tutor withdrawal.

Unsupported open explanations, drawing recognition, unrestricted working and ambiguous publisher instructions retain precise manual/semantic blockers. Do not inflate extraction confidence or attach a keyword recognizer to make them appear complete.

Developer operations and capability boundaries: [backend guide](../../../source-code/backend/docs/deterministic-scoring-and-readiness.md).
