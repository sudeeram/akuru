# Biology worked-diagram preparation

Created: 2026-11-19  
Applies alongside the existing iGCSE extraction and source-review guidelines.

When a question asks the Student to draw and its marking scheme provides textual criteria without a model diagram:

1. Preserve the original empty question grid, apparatus space or genetic-cross space. Do not place a completed answer among question visuals.
2. Prepare a separate, explicitly AI-generated answer from the exact question and official scheme. Include its relevant labels, units, scientific assumptions, accessible explanation and limitations. Official caps, alternative routes and follow-through remain in the rubric.
3. Use a supported bounded renderer. Unsupported diagram types remain explicit preparation tasks; never invent an official Pearson image, measurements, coordinate precision or experimental result.
4. Compare the rendered answer with the original sources before the separate authenticated Admin approval. Record who/what performed the review truthfully; a delegated AI review must not be described as owner/human sign-off.
5. Associate only the marking points actually illustrated. For alternative apparatus routes, do not claim one figure depicts both. Keep the maximum mark allocation unchanged.
6. After attachment, refresh the affected final source finding, resolve the actual missing-answer issue with an audit note and run the normal above-75% guarded approval and Tutor-release checks. Preserve sibling findings, previous releases and original extraction history. A drawing example is not a semantic scoring certificate.

Current bounded templates are a roan × roan male-roan cross, a heterozygous PTC male-taster cross, a bubble potometer, and a qualitative clotting-time curve with the source-specified 30–42°C range and 37°C optimum. They are not generic templates for arbitrary crosses, apparatus or enzyme graphs. Water uptake is a proxy for transpiration; an enzyme-rate optimum corresponds to a minimum in time taken, not a maximum. Qualitative curves must not acquire invented numerical y-values.

See the [verified Paper 2 completion record](reviews/2026-11-19-biology-paper2-worked-examples.md) and [implementation documentation](../../../source-code/backend/docs/ai-generated-worked-answers.md).


## June 2025 1BR follow-up — 2026-11-19

The bounded `ptc_cross` example supports Tt × Tt and a male-taster target. Keep dominant inheritance separate from codominant roan inheritance: three quarters taste PTC, so the independent male-and-taster probability is 3/8, not 1/4. Preserve alternative symbols and the official limits on follow-through.

When the source requests straight joins between consecutive observations, use the verified source points and individual straight segments; do not substitute a global regression line or smoothed curve. The original blank Student grid remains separate from the private worked answer.

Graph captions can sit below the plot. Check both the upper and lower crop boundaries against the complete original page: include each graph's own caption and exclude its neighbour's caption. On 1BR Q5(b)(ii), the old lower crop carried the upper graph's Graph 1 caption and omitted its own Graph 2 caption; both complete source crops were prepared as a regression example. Preserving axes alone is insufficient.

A saved response-type flag is not source authority. Check every draw/plot/genetic-diagram instruction against the original question even if an older import classified it as text, and configure separate private answer evidence where needed. The 1BR Q9(b)(ii) PTC cross was found by this check.

## Paper 1 bounded formats — 2026-11-20

Additional source-bound formats are available after the Paper 1 renderer update:

- `monohybrid_cross`: two diploid parental genotypes with one matching uppercase/lowercase allele pair. The renderer derives gametes, offspring, phenotype ratios and any explicitly requested sex probability. Do not reveal a later probability answer in a sibling part's phenotype-only example. Alternative symbols remain valid under the official scheme.
- `paired_line_graph`: two named series using verified source observations, numbered axes and units. Join adjacent points with straight segments only when that is the source instruction. Preserve the supplied observations; do not invent intermediate observations, regression or extrapolation.
- `starch_leaf_halves`: the specific carbon-dioxide exclusion experiment with the left region outside the jar and the right region inside a carbon-dioxide-absorbing jar. Show blue-black/starch on the left and yellow/orange/brown/no starch on the right. This is a labelled schematic, not a general template for arbitrary leaf experiments; check the original apparatus orientation first. Colours and labels must agree.

All formats still require exact source comparison, inspection of the production-rendered preview and a separately recorded approval. Renderer validation only checks supported structure and arithmetic, not whether the selected facts match the paper. Recheck shared stems when assigning visuals: a subpart retaining “the table shows…” must retain its applicable source table even when its final instruction is a practical-method question.

## Scaled pyramids of numbers — 2026-11-20

`pyramid_of_numbers` accepts two to five distinct trophic levels in producer-to-top-consumer order, with positive integer source counts. The trusted renderer derives centred bar widths on one shared linear scale and equal bar heights. Do not force a triangular shape: four oak trees, twenty mice and two foxes require a narrow base, wider middle and narrow top. Labels and accessible text retain every count and its trophic order. Counts are not biomass or physical organism size. Extreme ratios that cannot be read faithfully in this bounded format are rejected rather than silently widened. Verify the source counts, labels, scale and production preview before approving an AI-generated example; preserve the original blank Student grid.
