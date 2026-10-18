import type { Assignment, Attempt } from '@/api';

/** Uses existing authorized response data only; scores are not mastery estimates. */
export function learnerSummary(
  attempts: Attempt[],
  assignments: Assignment[],
  studentId: string,
  now = new Date(),
) {
  const ownAttempts = attempts.filter((item) => item.studentId === studentId);
  const ownAssignments = assignments.filter(
    (item) => item.studentId === studentId,
  );
  const weekStart = new Date(now);
  weekStart.setHours(0, 0, 0, 0);
  weekStart.setDate(weekStart.getDate() - ((weekStart.getDay() + 6) % 7));
  return {
    attempts: ownAttempts,
    weekly: ownAttempts.filter(
      (item) =>
        Date.parse(item.createdAt) >= weekStart.getTime() &&
        Date.parse(item.createdAt) <= now.getTime(),
    ),
    pending: ownAttempts.filter((item) => item.status === 'needs-review'),
    assignments: ownAssignments
      .filter((item) => !item.completed)
      .sort((a, b) => a.due.localeCompare(b.due)),
    completed: ownAssignments.filter((item) => item.completed).length,
    totalAssignments: ownAssignments.length,
    recent: [...ownAttempts]
      .sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt))
      .slice(0, 4),
  };
}
export function markedScore(
  attempts: Attempt[],
  subject: string,
): number | null {
  const marked = attempts.filter(
    (item) =>
      item.subject === subject &&
      ['checked', 'reviewed', 'approved'].includes(item.status) &&
      item.mark !== null &&
      Number.isFinite(item.mark) &&
      item.maxMarks > 0,
  );
  const possible = marked.reduce((total, item) => total + item.maxMarks, 0);
  return possible
    ? Math.max(
        0,
        Math.min(
          100,
          (marked.reduce((total, item) => total + (item.mark ?? 0), 0) /
            possible) *
            100,
        ),
      )
    : null;
}
