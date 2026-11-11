# Link exact past-paper evidence

Sign in as Admin and open **Exam Documents → Past papers → Review questions** (or the paper's Accuracy page). Open **Exact question & marking-scheme evidence**.

1. Save or discard any unsaved question edits first.
2. **Find existing exact blocks** performs free text matching. It does not call a model.
3. **AI analyse Q…** queues one question using AKURU's configured backend AI account. This can incur usage. Progress is saved; you can leave and return. From the Accuracy page, **AI analyse paper** explicitly queues all questions durably. The worker processes them one at a time. Wait for pending paper jobs before starting another run.
4. Expand a question's proposal results. Each region shows its subpart, question-paper/scheme role, physical PDF page, estimated match confidence and reason. Open the original excerpt/image and check the whole question/rubric, marks, alternatives and continuation guidance.
5. Select all correct regions for the question, tick the source-review confirmation and choose **Verify and link selected regions**. Use **Reject selected proposals** for wrong regions. **Link exact reviewed matches** is only available for unambiguous exact text matches; a high model percentage does not enable it.
6. If a region is incomplete, use **Adjust or select original PDF region**, enter the physical PDF page and normalized bounds (0–1), then preview the adjusted region. You can also use the existing Source evidence page/block controls to select or unlink evidence.
7. Linking changes the evidence snapshot, so previous accuracy assessments become outdated. Arrange a fresh source comparison/accuracy assessment before applying AI approval. AKURU deliberately does not carry the old score forward automatically.

Question content approval, visual approval, scoring readiness and Student release are separate. A successfully linked region does not publish a paper. Human-approved questions/subparts must be reopened before changing their evidence. Keep genuine ambiguities and publisher conflicts flagged rather than forcing approval.

If a source or question changes while you work, AKURU asks you to analyse again. Applied links and rejected proposals remain recorded. A repeated completed apply request does not create duplicate links. An interrupted AI job fails rather than silently retrying and charging again; check its status before explicitly starting another.

A completed run may show **superseded source snapshot** after links were applied or AI status changed, because the question revision advanced. Its **linked** rows remain an audit receipt; this label alone does not mean the saved links were removed. Check the current question's source evidence and current accuracy assessment. Only undecided proposals against a current snapshot may be applied.

## Final reassessment after image review

Open the paper's **Accuracy confidence** page (or one question's review page) and find **Final content reassessment**.

1. Complete **Images needing review**: crops, diagram labels, image associations and any proposed answer visuals.
2. Save your changes. The old assessment may now say **Reassessment required**; your reviews have not been lost.
3. Select **Reassess reviewed content**, read the model-usage confirmation and select **Queue reassessment**. The accuracy page queues outdated, image-ready questions; a question's review page focuses on that question. This uses the configured backend AI account and may incur charges.
4. You can leave and return. **Reassessment jobs** shows pending, completed and failed work. Do not blindly retry after an interruption: check job/assessment history first.
5. Inspect **Content needing manual review** and any remaining gates. Eligible high-confidence content uses AI approval without requiring you to manually approve every part. Exactly 75% does not qualify. Earlier checked publisher/source concerns remain for Admin adjudication, even if a new model suggests a higher score.
6. Complete the separate scoring/readiness and Student-release steps. Reassessment never releases a paper.

AI compares the current saved wording, marking points, original source pages and reviewed images. It records new accuracy/provenance history, without rewriting your question or undoing your image approvals. Changes made while it is processing cause a safe failure and require a new snapshot. If an assessment fails, the previous history remains; no partial new assessment is saved.

## Document workflow and automatic Tutor practice

The Exam Documents table shows four numbered progress labels for question papers: **Extracted**, **Images reviewed**, **Assessed**, **Tutor practice released**. Expand a label for counts, explanations and a link to its action. Grey means not started; blue means active work; amber means partial or needing attention; green means complete. The extraction percentage remains processing progress, not review completion or accuracy.

Mark schemes show **Extracted**, **Linked to paper**, **Evidence checked**. Reports show **Extracted**, **Linked to paper**, **Guidance checked**. These are independent milestones, scoped to each associated paper. You do not need to approve the same companion document again. A verified absence of commentary is different from an unchecked or unavailable report.

Review required image crops, labels and associations first. Then use **Reassess reviewed content** on the accuracy/review page. Read the paid-call confirmation: the final check covers wording, exact marking/report evidence, reviewed images and published textbook mappings. AI approval requires current confidence strictly above 75% and all applicable gates; exactly 75% remains for manual review. Existing human decisions are preserved. Open a subpart's accuracy details for separate curriculum confidence and referenced topic publication versions. Resolve mapping uncertainty/conflicts without forcing a topic association.

Eligible, independently answerable subparts become available for Tutor practice automatically. Amber release progress means some items remain unavailable; green requires all required items to be currently released. Unsupported scoring, missing evidence, unresolved images or curriculum uncertainty can still block release at high confidence. Nothing automatically publishes a complete exam. Student enrolment, enabled access and cumulative topic coverage still apply.

If an assessment saved but a release write failed, use **Retry eligible Tutor releases · no AI call**. This checks saved assessments and does not charge another model request. Explicitly withdrawn items remain withdrawn; only an intentional manual re-enable can restore them. Changing content/evidence or a referenced textbook publication can require reassessment. Historical attempts remain preserved.

A new low-confidence finding can require review even when an older human approval is preserved. Explicitly approving a reviewed part binds the decision to that exact assessment; it does not approve later changed content or a newer concern. Valid newly approved items use the same automatic release check without another release click. Scoring readiness is separate: an imported manual-only text rubric is not silently converted to automatic marking just because its confidence is high.

For partial Tutor practice, the Student sees the selected part's approved answer/guidance and approved answer visuals. Full marking-scheme/report pages are not exposed through this channel because they may contain unreleased neighbouring answers. The question-paper context remains accessible.
