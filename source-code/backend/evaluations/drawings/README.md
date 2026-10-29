# Drawing-assessment evaluation gate

The shipped path is manual review. Optional multimodal proposals are also always held for human review; `AKURU_ASSESSMENT_DRAWING_SUGGESTIONS_ENABLED=false` is the default. An ordinary text-assessment release does not enable drawing auto-scoring.

Before changing that policy, collect independently reviewed, licensed/private image fixtures outside Git for each proposed diagram type. Run the actual configured model against the original images and frozen approved rubric; preserve model, prompt (`drawing-review-v1`), rubric/source hashes, decisions, deterministic capped marks, uncertainties and usage. Never use mocked-provider tests as evidence of scientific accuracy.

## First matrix: displayed alkane isomers

| Case | Expected decision |
| --- | --- |
| Full displayed butane and 2-methylpropane, all bonds | 2 marks |
| Both correct, rotated or mirrored | 2 marks |
| Two rotated copies of butane | 1 mark |
| Only complete methylpropane | 1 mark |
| Condensed formulae only | 0 marks for an all-bonds-displayed requirement |
| One correct, one missing required C–H bonds | 1 mark |
| Incorrect valency in both structures | 0 marks |
| Ambiguous branch/bond, overwritten labels | Human review; no automatic score |
| Cropped response or unreadable photo | Human review; no automatic score |
| Typed correct names but incorrect drawings | Judge drawings against rubric, not names |
| Different student's attachment | Denied before model call |
| No original image | Human review; no OCR-only drawing score |

Minimum release evidence: at least five independent images per scientific case, varied orientation and handwriting, plus all security cases. Require 100% exact marks on clear cases, 100% review routing for ambiguous cases, zero over-awards beyond two, 100% source/Student isolation and repeat the run to confirm stable decisions. Have a subject reviewer approve expected results before running. Any failure keeps manual review in force. Broader graph/diagram types require their own cases, not reuse of this Chemistry gate.

Implementation tests cover secure routing, original-image payloads and deterministic limits. The expert-reviewed corpus and live-model run are **not yet completed**, so automatic drawing marking must remain disabled.
