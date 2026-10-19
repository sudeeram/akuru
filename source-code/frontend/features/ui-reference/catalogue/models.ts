export type SampleRecord = {
  id: number;
  title: string;
  subject: string;
  status: string;
};
export const sampleRecords: SampleRecord[] = Array.from(
  { length: 23 },
  (_, i) => ({
    id: i + 1,
    title: `${['Atomic structure', 'Algebra practice', 'Forces and motion', 'Chemical reactions'][i % 4]} · Paper ${i + 1}`,
    subject: ['Chemistry', 'Mathematics', 'Physics'][i % 3],
    status: ['Ready', 'Needs review', 'Draft'][i % 3],
  }),
);
export function workspaceRows(
  query: string,
  status: string,
  descending: boolean,
  subject = '',
) {
  return sampleRecords
    .filter(
      (r) =>
        `${r.title} ${r.subject}`
          .toLowerCase()
          .includes(query.trim().toLowerCase()) &&
        (!status || r.status === status) &&
        (!subject || r.subject === subject),
    )
    .sort((a, b) => (descending ? b.id - a.id : a.id - b.id));
}
export function pageWindow<T>(rows: T[], page: number, size: number) {
  const pages = Math.max(1, Math.ceil(rows.length / size));
  const current = Math.max(1, Math.min(page, pages));
  return {
    current,
    pages,
    rows: rows.slice((current - 1) * size, current * size),
    start: rows.length ? (current - 1) * size + 1 : 0,
    end: Math.min(current * size, rows.length),
  };
}
export type AttendanceMark = 'Present' | 'Late' | 'Absent' | null;
export function attendanceSummary(marks: AttendanceMark[]) {
  const present = marks.filter((m) => m === 'Present').length,
    late = marks.filter((m) => m === 'Late').length,
    absent = marks.filter((m) => m === 'Absent').length;
  const marked = present + late + absent;
  return {
    present,
    late,
    absent,
    marked,
    total: marks.length,
    rate: marked ? Math.round(((present + late) / marked) * 100) : null,
  };
}
