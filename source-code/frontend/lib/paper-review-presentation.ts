import type { PaperReview } from '@/api';
import type { QuestionAnalysis } from '@/api/assessments/official-paper-review.api';

type Question = PaperReview['questions'][number];

export function reviewProvenance(
  analysis: QuestionAnalysis,
  partLabel?: string,
) {
  const overrides =
    partLabel == null
      ? []
      : analysis.parts.find((part) => part.label === partLabel)?.provenance ||
        [];
  return analysis.provenance.map(
    (source) => overrides.find((item) => item.role === source.role) || source,
  );
}

export function reviewAccuracy(question: Question) {
  if (question.accuracyAnalysis)
    return question.accuracyAnalysis.isCurrent
      ? question.accuracyAnalysis.question.percent
      : undefined;
  if (question.extractionAnalysis)
    return question.extractionAnalysis.isCurrent
      ? question.extractionAnalysis.question.percent
      : undefined;
  return question.data?.extractionConfidence?.percent;
}

/** Excluded questions remain visible in the inventory without being pending work. */
export function reviewAttentionCount(questions: Question[]) {
  return questions.filter(
    (question) => !['approved', 'excluded'].includes(question.status),
  ).length;
}

export function reviewQuestionList(
  questions: Question[],
  filter: string,
  search: string,
  confidenceFirst = false,
  modelSearch = '',
) {
  const term = search.trim().toLowerCase();
  const modelTerm = modelSearch.trim().toLowerCase();
  const matches = questions.filter(
    (question) =>
      (filter === 'all' ||
        (filter === 'attention'
          ? !['approved', 'excluded'].includes(question.status)
          : question.status === filter)) &&
      (!term || `question ${question.number}`.toLowerCase().includes(term)) &&
      (!modelTerm ||
        [question.extractionAnalysis, question.accuracyAnalysis].some(
          (analysis) =>
            [
              ...(analysis?.provenance || []),
              ...(analysis?.parts || []).flatMap(
                (part) => part.provenance || [],
              ),
            ].some((source) =>
              `${source.method} ${source.provider || ''} ${source.modelId || ''} ${source.modelName || ''}`
                .toLowerCase()
                .includes(modelTerm),
            ),
        )),
  );
  if (!confidenceFirst) return matches;
  return matches.sort(
    (a, b) => (reviewAccuracy(a) ?? 101) - (reviewAccuracy(b) ?? 101),
  );
}

/** Previous/next follows the server's inventory order, independent of display filters. */
export function reviewNeighbours(questions: Question[], selected: string) {
  const index = questions.findIndex((question) => question.number === selected);
  return {
    previous: index > 0 ? questions[index - 1] : undefined,
    next: index >= 0 ? questions[index + 1] : undefined,
  };
}

/** No navigation during a save; dirty drafts require an explicit discard choice. */
export function reviewNavigationAllowed(
  busy: boolean,
  dirty: boolean,
  confirmDiscard: () => boolean,
) {
  return !busy && (!dirty || confirmDiscard());
}

export function reviewHasChanges(
  draft: unknown,
  savedSnapshot: string,
  emptyDraft: unknown,
) {
  return (
    JSON.stringify(draft) !== (savedSnapshot || JSON.stringify(emptyDraft))
  );
}

/** Preserve the logical subpart when a saved server response refreshes the form. */
export function reviewSavedPartIndex(
  parts: { label: string }[],
  selectedLabel?: string,
) {
  const index = parts.findIndex((part) => part.label === selectedLabel);
  return index < 0 ? 0 : index;
}

/** Page-level links and exact block links are independent evidence selections. */
export function reviewPageLinkState(
  sources: { page: number; blockId?: string | null }[],
  page: number,
) {
  const onPage = sources.filter((source) => source.page === page);
  return {
    pageLinked: onPage.some((source) => !source.blockId),
    linkedBlockCount: new Set(
      onPage.flatMap((source) => (source.blockId ? [source.blockId] : [])),
    ).size,
  };
}

/** Green approval represents the persisted part, never an unsaved local selection. */
export function reviewPartSaveState(
  part: { label: string; status: string },
  savedParts: { label: string; status: string }[],
) {
  const saved = savedParts.find((item) => item.label === part.label);
  const unsaved = JSON.stringify(part) !== JSON.stringify(saved);
  return { unsaved, displayStatus: unsaved ? 'unsaved' : part.status };
}
