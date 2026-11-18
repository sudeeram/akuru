# Prepared source correction and carry-forward

Guideline ID: `pearson-igcse-source-review`

Version: `prepared-review-v1`

Effective: 2026-11-18

Use this procedure when reviewing stored question, scheme and examiner-report extraction through AKURU's prepared developer APIs. It supplements the extraction guidelines; it does not replace source inspection.

1. Export the exact current paper/question, original source versions and part bindings. Inspect the original page/region, not just an earlier paraphrase. Record source roles, PDF pages and the specific defect.
2. Preserve every official alternative, equivalent-answer allowance, exception, rejection, any-N cap and combined-response condition. Parenthetical explanatory text must not become a new compulsory credit condition. Accept converse comparisons only where permitted by the official source.
3. Keep extraction fidelity, report guidance, curriculum support and executable scoring separate. Source confidence may be high while a free-text explanation remains manual-only. A scheme/report conflict follows the marking scheme under AKURU's agreed policy; a contradiction inside the scheme needs explicit adjudication.
4. Correct only the affected part and genuine shared dependencies. Supply an attributed new finding for every changed dependency. Do not pretend unchanged sibling findings were freshly re-read: carry them forward with their original analysis identity only when their saved scope still matches.
5. Record the actual model/reasoning identity only when reliably known. Otherwise use `not_recorded` and explain the limitation. Never invent provider response IDs, API usage or a human reviewer. Preserve initial extraction provenance separately from later source review.
6. An extraction-issue resolution must name the relevant correction and source recheck. A note cannot repair missing marking points. Preserve the issue history even when the defect is corrected. Excluded report guidance stays excluded in Student releases.
7. Stage and inspect an immutable preview before applying. If content, sources, mappings or an Admin edit conflicts, prepare a fresh review rather than refreshing expected hashes to force the previous package through.
8. Apply through authenticated Admin APIs with CSRF protection. Keep licensed exports and credentials outside Git. Do not use production SQL to bypass the review workflow.
9. Preserve human-reviewed siblings, compatible server scoring certificates and explicitly enabled Tutor releases. Do not silently restore a withdrawal. Revalidate affected proofs on the deployed server; a local expected answer or confidence figure is not a certificate.
10. Inspect post-apply readiness and record remaining blockers. Tutor practice, official drafts and formal publication are distinct. A complete source review is not a statement that an entire exam is automatically markable or published.

API and CLI reference: [prepared review workflow](../../../source-code/backend/docs/developer-review-apis.md).
