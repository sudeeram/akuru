import { randomUUID } from 'node:crypto';
import {
  grades,
  terms,
  subjects,
  passwordRecord,
  progressionPairs,
} from './curriculum.mjs';

export function adminRoutes({ path, body, user, db, fail, save, json }) {
  if (!path.startsWith('/api/admin/')) return false;
  if (user.role !== 'admin') fail(403, 'Admin access required.');
  const text = (v, max = 10000) =>
    typeof v === 'string' ? v.trim().slice(0, max) : '';
  const list = (v) => (Array.isArray(v) ? [...new Set(v)] : []);
  const subject = () => {
    if (body.course !== 'iGCSE' || !subjects.some((s) => s.id === body.subject))
      fail(400, 'Choose an iGCSE subject. Phase 1 supports iGCSE only.');
  };
  const parent = () => {
    if (!db.users.some((u) => u.id === body.parentId && u.role === 'parent'))
      fail(400, 'Choose an existing parent account.');
  };
  const enrolment = () => {
    if (
      body.level !== 'iGCSE' ||
      !grades.includes(body.grade) ||
      !terms.includes(body.term)
    )
      fail(
        400,
        'Choose iGCSE, Grade 10 or Grade 11, and Term1, Term2 or Term3.',
      );
    const ids = list(body.subjects);
    if (!ids.length || ids.some((id) => !subjects.some((s) => s.id === id)))
      fail(400, 'Choose valid iGCSE subjects.');
    const progression = list(body.progression).map((key) => {
      const [grade, term] = String(key).split('|');
      return { grade, term };
    });
    const selectedProgression = progression.length
      ? progression
      : [{ grade: body.grade, term: body.term }];
    if (
      selectedProgression.some(
        (p) => !grades.includes(p.grade) || !terms.includes(p.term),
      )
    )
      fail(400, 'Choose valid Grade and Term combinations.');
    selectedProgression.sort(
      (a, b) =>
        grades.indexOf(a.grade) - grades.indexOf(b.grade) ||
        terms.indexOf(a.term) - terms.indexOf(b.term),
    );
    for (const grade of grades) {
      const indexes = selectedProgression
        .filter((p) => p.grade === grade)
        .map((p) => terms.indexOf(p.term));
      if (indexes.length && indexes.some((index, i) => index !== i))
        fail(
          400,
          'Grade + Term progression must include earlier terms before later terms.',
        );
    }
    return {
      level: 'iGCSE',
      grade: selectedProgression.at(-1).grade,
      term: selectedProgression.at(-1).term,
      progression: selectedProgression,
      subjects: ids,
      needsConfiguration: false,
      courses: Object.fromEntries(
        ids.map((id) => [
          id,
          {
            level: 'iGCSE',
            syllabus:
              text(body.courses?.[id]?.syllabus, 120) || 'Not configured',
          },
        ]),
      ),
    };
  };
  const units = (ids, subjectId, textbookId) => {
    const selected = list(ids);
    if (
      !selected.length ||
      selected.some(
        (id) =>
          !db.units.some(
            (u) =>
              u.id === id &&
              u.course === 'iGCSE' &&
              u.subject === subjectId &&
              (!textbookId || u.textbookId === textbookId) &&
              db.documents.some(
                (d) => d.id === u.textbookId && d.status === 'approved',
              ),
          ),
      )
    )
      fail(
        400,
        'Choose at least one unit from an approved textbook in the same subject.',
      );
    return selected;
  };
  let result;
  if (path === '/api/admin/accounts') {
    const id = text(body.username, 40).toLowerCase();
    if (
      !/^[a-z0-9][a-z0-9_-]{2,39}$/.test(id) ||
      db.users.some((u) => u.id === id)
    )
      fail(
        400,
        'Choose a unique username (3–40 letters, numbers, underscores or hyphens).',
      );
    if (
      !['parent', 'student'].includes(body.role) ||
      !text(body.name, 60) ||
      typeof body.password !== 'string' ||
      body.password.length < 8 ||
      body.password.length > 100 ||
      body.password.trim() !== body.password
    )
      fail(
        400,
        'Enter a name, parent/student role and password of 8–100 characters without outer spaces.',
      );
    let profile;
    if (body.role === 'student') {
      parent();
      profile = {
        id,
        name: text(body.name, 60),
        initial: text(body.name)[0],
        parentId: body.parentId,
        ...enrolment(),
      };
    }
    const account = {
      id,
      name: text(body.name, 60),
      role: body.role,
      ...passwordRecord(body.password),
    };
    db.users.push(account);
    if (profile) db.students.push(profile);
    result = { id, name: account.name, role: account.role };
  } else if (path === '/api/admin/students') {
    const s = db.students.find((s) => s.id === body.id);
    if (!s) fail(404, 'Student not found.');
    parent();
    if (!text(body.name, 60)) fail(400, 'Name is required.');
    if (db.exams.some((e) => e.studentId === s.id && e.status === 'active'))
      fail(
        409,
        "Submit the student's active exam before changing enrolment or family.",
      );
    Object.assign(s, enrolment(), {
      name: text(body.name, 60),
      parentId: body.parentId,
    });
    db.users.find((u) => u.id === s.id).name = s.name;
    result = s;
  } else if (path === '/api/admin/units') {
    const book = db.documents.find(
      (d) =>
        d.id === body.textbookId &&
        d.kind === 'Textbook' &&
        d.status === 'approved',
    );
    if (!book) fail(400, 'Upload and approve a textbook first.');
    const title = text(body.title, 180),
      code = text(body.code, 40);
    if (
      !title ||
      !code ||
      db.units.some((u) => u.textbookId === book.id && u.code === code)
    )
      fail(400, 'Enter a unit title and a unique code within this textbook.');
    result = {
      id: randomUUID(),
      textbookId: book.id,
      course: book.course,
      subject: book.subject,
      title,
      code,
    };
    db.units.push(result);
  } else if (path === '/api/admin/coverage') {
    subject();
    if (!grades.includes(body.grade) || !terms.includes(body.term))
      fail(400, 'Choose a valid grade and term.');
    const ids = list(body.unitIds);
    if (ids.length) units(ids, body.subject);
    result = {
      course: 'iGCSE',
      subject: body.subject,
      grade: body.grade,
      term: body.term,
      unitIds: ids,
    };
    const i = db.coverage.findIndex(
      (c) =>
        c.course === result.course &&
        c.subject === result.subject &&
        c.grade === result.grade &&
        c.term === result.term,
    );
    if (i < 0) db.coverage.push(result);
    else db.coverage[i] = result;
  } else if (path === '/api/admin/questions') {
    const paper = db.documents.find(
      (d) => d.id === body.paperId && d.kind === 'Past paper' && !d.legacy,
    );
    if (!paper) fail(400, 'Upload a past paper linked to a textbook first.');
    const ids = units(body.unitIds, paper.subject, paper.textbookId);
    const number = text(body.number, 40),
      prompt = text(body.prompt),
      points = text(body.points).split('\n').filter(Boolean);
    if (
      !number ||
      !prompt ||
      !text(body.title, 180) ||
      !text(body.explanation) ||
      !points.length ||
      !Number.isInteger(body.marks) ||
      body.marks < 1 ||
      body.marks > 100 ||
      !['numeric', 'written'].includes(body.type) ||
      (body.type === 'numeric' &&
        (body.answer === '' || !Number.isFinite(Number(body.answer))))
    )
      fail(
        400,
        'Complete the question, marking points, worked explanation and valid marks/answer.',
      );
    if (
      db.questions.some(
        (q) =>
          q.paperId === paper.id && q.number === number && q.id !== body.id,
      )
    )
      fail(400, 'This question number already exists in the paper.');
    const existing =
      body.id &&
      db.questions.find((q) => q.id === body.id && q.paperId === paper.id);
    if (body.id && !existing) fail(404, 'Question not found.');
    if (
      existing &&
      db.exams.some(
        (e) => e.status === 'active' && e.questionIds.includes(existing.id),
      )
    )
      fail(409, 'An active exam uses this question. Finish it before editing.');
    result = {
      id: existing?.id || randomUUID(),
      paperId: paper.id,
      number,
      course: paper.course,
      subject: paper.subject,
      unitIds: ids,
      status: body.status === 'approved' ? 'approved' : 'pending',
      title: text(body.title, 180),
      prompt,
      topic: db.units.find((u) => u.id === ids[0]).title,
      marks: body.marks,
      type: body.type,
      answer: body.type === 'numeric' ? Number(body.answer) : null,
      explanation: text(body.explanation),
      points,
      hints: text(body.hints).split('\n').filter(Boolean),
      diagram: '',
      source: `${paper.name} · Q${number}`,
    };
    if (existing) Object.assign(existing, result);
    else db.questions.push(result);
    // Any question edit invalidates paper sign-off; admin must attest completeness again.
    paper.status = 'pending';
    paper.mappingComplete = false;
  } else fail(404, 'Admin endpoint not found.');
  db.audit.push({
    id: randomUUID(),
    actorId: user.id,
    action: path,
    targetId: result.id || `${result.subject}/${result.grade}/${result.term}`,
    createdAt: new Date().toISOString(),
  });
  save();
  json(200, result);
  return true;
}
