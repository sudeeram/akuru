import { randomBytes, scryptSync } from 'node:crypto';

export const courseCatalog = ['iPrimary', 'iLower Secondary', 'iGCSE'];
export const grades = ['Grade 10', 'Grade 11'];
export const terms = ['Term1', 'Term2', 'Term3'];
export const progressionPairs = grades.flatMap((grade) =>
  terms.map((term) => ({ grade, term })),
);
export const subjects = [
  ['english', 'English', 'orange'],
  ['maths', 'Maths', 'blue'],
  ['ict', 'ICT', 'purple'],
  ['biology', 'Biology', 'green'],
  ['chemistry', 'Chemistry', 'green'],
  ['physics', 'Physics', 'blue'],
  ['french', 'French', 'orange'],
  ['human-biology', 'Human Biology', 'green'],
].map(([id, name, color]) => ({
  id,
  name,
  color,
  symbol: '',
  topic: 'iGCSE subject',
  topics: [],
  course: 'iGCSE',
}));
export const kinds = [
  'Textbook',
  'Past paper',
  'Marking scheme',
  'Examiner report',
  'Reference material',
];
export function passwordRecord(password) {
  const salt = randomBytes(16).toString('hex');
  return { salt, hash: scryptSync(password, salt, 64).toString('hex') };
}
export function migrate(db, credentials, seedQuestions, fresh) {
  if (db.schemaVersion === 2) {
    for (const s of db.students) {
      s.progression ??=
        s.grade && s.term ? [{ grade: s.grade, term: s.term }] : [];
    }
    return;
  }
  db.users = credentials.map(({ password, ...u }) => ({
    ...u,
    ...passwordRecord(password),
  }));
  db.users.push({
    id: 'admin',
    name: 'Admin',
    role: 'admin',
    ...passwordRecord('admin123'),
  });
  db.units = [];
  db.coverage = [];
  db.audit = [];
  db.questions = seedQuestions.map((q) => ({
    ...q,
    course: 'iGCSE',
    status: 'legacy',
    unitIds: [],
  }));
  for (const s of db.students) {
    s.parentId = 'parent';
    s.legacyProfile = {
      grade: s.grade,
      level: s.level,
      subjects: s.subjects,
      courses: s.courses,
    };
    s.subjects = s.subjects.filter((id) => subjects.some((x) => x.id === id));
    s.level = 'iGCSE';
    s.grade = fresh ? (s.id === 'sam' ? 'Grade 11' : 'Grade 10') : s.grade;
    s.term = fresh ? 'Term1' : '';
    s.progression = fresh && s.grade ? [{ grade: s.grade, term: 'Term1' }] : [];
    s.needsConfiguration = !fresh;
    s.courses = Object.fromEntries(
      s.subjects.map((id) => [
        id,
        { level: 'iGCSE', syllabus: 'Not configured' },
      ]),
    );
  }
  for (const d of db.documents) {
    d.status = 'pending';
    d.course = 'iGCSE';
    d.legacy = true;
  }
  for (const e of db.exams) if (e.status === 'active') e.status = 'legacy';
  if (fresh) db.assignments = [];
  db.schemaVersion = 2;
}
export function coveredUnits(db, student, subject) {
  if (!student || student.needsConfiguration) return [];
  const progression = student.progression?.length
    ? student.progression
    : student.grade && student.term
      ? [{ grade: student.grade, term: student.term }]
      : [];
  return [
    ...new Set(
      db.coverage
        .filter(
          (c) =>
            c.course === student.level &&
            c.subject === subject &&
            progression.some((p) => p.grade === c.grade && p.term === c.term),
        )
        .flatMap((c) => c.unitIds),
    ),
  ];
}
export function published(db, q) {
  const paper = db.documents.find((d) => d.id === q.paperId);
  return (
    q.status === 'approved' &&
    q.unitIds?.length > 0 &&
    paper?.status === 'approved' &&
    q.unitIds.every((id) => {
      const unit = db.units.find((u) => u.id === id);
      return (
        unit?.subject === q.subject &&
        unit.course === q.course &&
        unit.textbookId === paper.textbookId &&
        db.documents.some(
          (d) =>
            d.id === unit.textbookId &&
            d.kind === 'Textbook' &&
            d.status === 'approved',
        )
      );
    })
  );
}
export function eligible(db, student, q) {
  const covered = coveredUnits(db, student, q.subject);
  return (
    student?.level === q.course &&
    student.subjects.includes(q.subject) &&
    published(db, q) &&
    q.unitIds.every((id) => covered.includes(id))
  );
}
