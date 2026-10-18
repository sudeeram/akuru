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
