import type { PaperReview } from '@/api';

type Question = PaperReview['questions'][number];

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
) {
  const term = search.trim().toLowerCase();
  return questions.filter(
    (question) =>
      (filter === 'all' ||
        (filter === 'attention'
          ? !['approved', 'excluded'].includes(question.status)
          : question.status === filter)) &&
      (!term || `question ${question.number}`.toLowerCase().includes(term)),
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
export function reviewSavedPartIndex(parts: { label: string }[], selectedLabel?: string) {
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
    linkedBlockCount: new Set(onPage.flatMap((source) => source.blockId ? [source.blockId] : [])).size,
  };
}

/** Green approval represents the persisted part, never an unsaved local selection. */
export function reviewPartSaveState(part: { label: string; status: string }, savedParts: { label: string; status: string }[]) {
  const saved = savedParts.find((item) => item.label === part.label);
  const unsaved = JSON.stringify(part) !== JSON.stringify(saved);
  return { unsaved, displayStatus: unsaved ? 'unsaved' : part.status };
}
