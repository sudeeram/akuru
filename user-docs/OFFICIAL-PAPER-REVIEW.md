# Reviewing official exam papers

The official-paper workspace is available to Admin users under **Exam Documents → Past papers → Review questions**. It is an internal draft workspace. Saving or approving a question does not make it available to Students.

1. Upload the original question paper as a **Past paper**, with the correct course, subject, examination year, session, component and variant. Upload its exact **Marking scheme**, selecting that paper as the related source. An **Examiner report** is optional and can be attached later. Wait for extraction to finish.
2. Open **Review questions** on the past-paper row. Select the matching scheme and optional report, enter the complete number of top-level questions, and start the workspace. Each workspace is bound to the uploaded source versions; if a source PDF changes, ask a developer to handle the version change before continuing.
3. Open a question or add one. Check the source page alongside the extracted blocks. Correct the full question wording, shared stem, subpart wording and marks. When you save a subpart as ready or approved, AKURU links an exact reviewed question-paper block automatically if its label and wording have one unambiguous match on the linked page. Check the returned link after saving. If there is no unique match, use **Link this block** to record exact evidence for the selected subpart. A linked block changes to **Linked to part … · Remove link**, and its page and text appear in the linked-evidence summary. You can remove a mistaken link. **Unsaved changes** means the link is still in the browser draft; click **Save question review** to persist it. Page-only links can be saved as drafts, but approval still requires exact evidence.
4. For each subpart, review the marking points and accepted alternatives. Click **Add marking point** and enter its short code, kind and wording in separate fields. You can save incomplete rows as an unreviewed draft and return later. Every row needs a code and wording before approval. Add examiner guidance only when supported by the attached report.
5. AKURU prepares unassigned candidate diagrams and tables from the PDF. Use **Prepare or refresh candidate visuals** if needed for an existing workspace. For each candidate, choose exactly where it belongs: one or more subparts, or the shared question stem if it genuinely applies throughout. A visual can be reused in several subparts. Remove irrelevant candidates. Inspect the crop, choose **Keep this crop and attach reviewed visual** or **Adjust crop**, and add an accessible description. Save the question after changing placements. The preview groups visuals under their assigned subparts. A question cannot be approved while candidates remain unassigned or unreviewed, or while a subpart referring to a required diagram or table lacks its relevant visual.
6. Select a coverage decision: **supported**, **partial or uncertain**, or **outside current coverage**. For supported parts, link one or more published topics in the same subject and explain the match. A wording similarity or draft suggestion is not a confirmed mapping. A whole question with any unsupported required part is not eligible for a term mock.
7. Save after each correction. Set subparts to **approved** only after their wording, marks, scheme evidence and coverage decision are checked; then approve the question. Reopening an approved question resets its subpart approvals. The progress summary shows remaining blockers. An excluded question needs a reason and still counts in the source inventory.
8. When every question in the complete inventory is approved, **Prepare official paper and scheme drafts**. Review those drafts in Exam Documents. Publish the paper and then its exact marking scheme using the existing confirmation controls. A partially reviewed paper remains unavailable to Students.

For the June 2025 Chemistry pilot, an Admin may import the unreleased draft-bank JSON after uploading the exact matching PDFs. The import checks the PDF hashes and page inventory and seeds **unapproved proposals**. It never publishes material. The private draft-bank, triage JSON, licensed PDFs and rendered pages must stay outside Git.

The 1C and 2C pilot candidates were reassessed against the PDF pages. Their proposed placements remain draft suggestions. In particular, verify that 1C Question 1's atom crop includes all three answer lines, and check every part's wording and crop before approval. Some OCR-derived subpart wording still needs manual correction.

## Navigating the review workspace

The compact header shows the complete inventory, saved questions, approvals and questions needing attention. Expand **View what remains** to see the paper's existing review blockers. **Paper details & source attachments** holds source names and attachment controls; **Candidate visual tools** holds candidate generation.

Use **Find question** and **Review status** to narrow the question list. The selected question is highlighted. **Previous** and **Next** follow the complete saved inventory even when the list is filtered. Switching questions asks before discarding unsaved edits. The first saved question opens automatically when the workspace loads.

On desktop, the question editor and source viewer sit alongside each other. Select **Paper**, **Marking scheme** or **Report**, or use **Compare sources** to show the question paper and exact scheme together. Textbook topic mapping stays in the subpart's **Curriculum coverage** section; open the published textbook separately to read its full content. Source page arrows change only the source view. Clicking linked evidence opens the correct source tab, page and extracted block. At narrower widths the sources and editor stack; the question list scrolls horizontally.

The persistent toolbar shows the save state and **Save question review**. Saving still uses the existing question revision and approval checks. Draft edits, including edits made before entering a question number, are protected on portal navigation and page reload. Advanced crop controls are under **Create or adjust a visual crop**. Once internal review is complete, **Prepare official paper and scheme drafts** remains a separate action; it does not publish content to Students.

## Content approval and automatic marking

Each subpart has two separate decisions. **Subpart review status** approves its content, evidence and curriculum coverage. **Automatic-marking readiness** confirms that the marking instructions are represented in rules AKURU can apply. You can approve content while leaving marking rules unchecked or marking the part for manual marking.

Under **Automatic marking rules**, the maximum marks come from the subpart itself. Keep all acceptable marking points even when only some earn credit. Put synonyms in **Equivalent accepted answers** on the same point. Use **Add combined response** when the scheme explicitly allows one answer to satisfy multiple points, and list those point codes. Use **Add group limit** for additional caps within a subpart; a group can also specify points required for full credit.

For Q2(a), retain four points and its two-mark maximum. Add “moves on the surface” as a combined response for the movement and floating point codes. Fizzing, bubbles and effervescence belong to the same point. Check the source scheme before confirming **All scoring rules represented and checked**. Unsupported conditional rules must remain **Manual marking required**, with a reason.

The overall Question status is still a separate content decision. Approving all subparts does not automatically approve the question. Official assessment drafts can be prepared only after the complete paper's content is approved and every subpart's automatic-marking rules are confirmed. Successful content approval alone does not release student access.

## Coverage evidence and saving your place

Keep coverage reasons focused on concepts, without page numbers. Select the matching reviewed page under **Textbook evidence · Visual reference pages** and use **Open page** to verify it. References retain the exact source version and printed-page label. A replaced source is flagged for revalidation; confirm a replacement before removing the historical reference. Page evidence is optional when saving a draft.

Saving shows a toast notification and preserves the selected subpart and source pages. **Previous subpart** and **Next subpart** move within the question without discarding unsaved edits. The question navigation buttons continue to warn about unsaved work.

Coverage reasons are optional for **Outside current coverage**. They remain required before approval for **Supported** and **Partial or uncertain** decisions. A subpart edited since its last save shows **unsaved** in amber; green represents a successfully saved approval. A failed save keeps the unsaved marker until corrected and saved.


## AI-generated graph worked answers

For a question whose official marking scheme describes a graph but contains no worked plot, open **AI-generated worked answers** below Subpart review. This first version supports plotted points, anomaly circles and straight best-fit lines.

1. Save ordinary question edits first. Check the original paper and exact scheme evidence.
2. Open **Generate a graph solution**. Enter verified horizontal/vertical axis labels with units, ranges and tick intervals; enter one x,y pair per line; select the subparts and explain which sources you checked.
3. Select **Generate draft**. If generation is not configured, the controls remain disabled until an operator enables the feature and configures an OpenAI account. Reopening a preview does not call OpenAI again.
4. Inspect each worked step, source versions, checks and scientific content. **Edit explanation and plotting instructions** allows corrections; saving edits removes approval. Incorrect source values require a new generation with corrected verified input.
5. Enter a review note and choose **Approve worked answer** or **Reject**. Generated answers retain **AI-generated worked answer — not an official Pearson answer** after approval.
6. Use **Attach approved answer to question**. An approved question must be reopened first. Check the attached answers, save any further question changes and use the normal question/paper release process. Attaching does not publish the paper or bypass curriculum coverage.

Prefer the official scheme diagram when one exists. June 2025 1C Q7(c)(i–iii) is the planned graph pilot; Q5(c)(ii) already has official diagrams, and Q9(a)(i)/(iii) should use diagrams from scheme page 13. A generated graph is an illustrative solution: valid Student fits and follow-through readings may vary. This feature does not enable automatic marking of drawings.

Production OpenAI configuration and live Q7 generation were deferred by the owner on 2026-10-31. Existing source reviews and approvals are unaffected.
