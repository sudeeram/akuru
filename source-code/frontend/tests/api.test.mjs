import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { Readable } from 'node:stream';
process.env.PORTAL_DATA_DIR = mkdtempSync(join(tmpdir(), 'akuru-v2-test-'));
const { handler } = await import('../local-server/api.mjs');
async function call(path, body, cookie, extra = {}) {
  const req = Readable.from(body === undefined ? [] : [JSON.stringify(body)]);
  Object.assign(req, {
    url: `/api/${path}`,
    method: body === undefined ? 'GET' : 'POST',
    headers: {
      host: '127.0.0.1:5181',
      ...(cookie ? { cookie } : {}),
      ...extra,
    },
    socket: { remoteAddress: 'test' },
  });
  const headers = {};
  let output;
  const res = {
    statusCode: 200,
    setHeader(k, v) {
      headers[k.toLowerCase()] = v;
    },
    end(v) {
      output = v;
    },
  };
  await handler(req, res, () => {
    throw new Error('Unexpected fallthrough');
  });
  let data;
  try {
    data = JSON.parse(String(output));
  } catch {
    data = output;
  }
  return { status: res.statusCode, data, headers };
}
async function login(username, password) {
  const r = await call('login', { username, password });
  assert.equal(r.status, 200, JSON.stringify(r.data));
  assert.match(r.headers['set-cookie'], /HttpOnly; SameSite=Strict/);
  return r.headers['set-cookie'].split(';')[0];
}
let admin,
  parent,
  alex,
  otherParent,
  otherChild,
  book,
  paper,
  unit1,
  unit2,
  foreignUnit,
  q1,
  q2,
  attempt,
  exam;
const file = {
  name: 'Fixture.pdf',
  data:
    'data:application/pdf;base64,' +
    Buffer.from('%PDF-1.4\nSynthetic test').toString('base64'),
  course: 'iGCSE',
  subject: 'maths',
};
const enrolment = {
  level: 'iGCSE',
  grade: 'Grade 10',
  term: 'Term1',
  subjects: ['maths'],
};
async function ok(path, body, cookie = admin) {
  const r = await call(path, body, cookie);
  assert(r.status < 300, `${path}: ${JSON.stringify(r.data)}`);
  return r.data;
}
async function approve(id, complete = false) {
  return ok('documents/review', {
    id,
    status: 'approved',
    mappingComplete: complete,
  });
}
test('authentication and role-scoped catalog', async () => {
  assert.equal((await call('state')).status, 401);
  assert.equal(
    (await call('login', { username: 'admin', password: 'wrong' })).status,
    401,
  );
  admin = await login('admin', 'admin123');
  parent = await login('parent', 'parent123');
  alex = await login('alex', 'alex123');
  const s = await ok('state', undefined, admin);
  assert.equal(s.subjects.length, 8);
  assert.deepEqual(s.catalog.courses, [
    'iPrimary',
    'iLower Secondary',
    'iGCSE',
  ]);
  assert.equal(s.accounts.length, 5);
  assert(s.accounts.every((a) => !a.hash && !a.password));
  assert.equal((await ok('state', undefined, alex)).questions.length, 0);
});
test('only admin creates linked accounts; phase 1 restricts courses, grades and terms', async () => {
  const p = {
    username: 'parent-two',
    name: 'Other Parent',
    role: 'parent',
    password: 'testing123',
  };
  assert.equal((await call('admin/accounts', p, parent)).status, 403);
  await ok('admin/accounts', p);
  otherParent = await login(p.username, p.password);
  assert.equal((await call('admin/accounts', p, admin)).status, 400);
  const child = {
    ...enrolment,
    username: 'child-two',
    name: 'Other Child',
    role: 'student',
    password: 'testing456',
    parentId: 'parent-two',
  };
  for (const change of [
    { parentId: 'alex' },
    { level: 'iPrimary' },
    { grade: 'Grade 9' },
    { term: 'Term4' },
    { subjects: ['science'] },
  ])
    assert.equal(
      (await call('admin/accounts', { ...child, ...change }, admin)).status,
      400,
    );
  assert.equal(
    (
      await call(
        'admin/accounts',
        { ...child, progression: ['Grade 10|Term2'] },
        admin,
      )
    ).status,
    400,
  );
  await ok('admin/accounts', child);
  otherChild = await login(child.username, child.password);
  assert.deepEqual(
    (await ok('state', undefined, otherParent)).students.map((s) => s.id),
    ['child-two'],
  );
  const disk = JSON.parse(
    readFileSync(join(process.env.PORTAL_DATA_DIR, 'state.json'), 'utf8'),
  );
  assert(disk.users.find((u) => u.id === 'child-two').hash);
  assert(!JSON.stringify(disk).includes('testing456'));
});
test('only admin updates enrolments', async () => {
  const update = { ...enrolment, id: 'alex', parentId: 'parent', name: 'Alex' };
  assert.equal((await call('students', update, parent)).status, 403);
  assert.equal((await call('admin/students', update, parent)).status, 403);
  await ok('admin/students', update);
});
test('textbook and units precede past papers; learning documents admin-only', async () => {
  assert.equal(
    (await call('upload', { ...file, kind: 'Textbook' }, parent)).status,
    403,
  );
  assert.equal(
    (await call('upload', { ...file, kind: 'Textbook' }, alex)).status,
    403,
  );
  assert.equal(
    (await call('upload', { ...file, kind: 'Past paper' }, admin)).status,
    400,
  );
  book = await ok('upload', { ...file, kind: 'Textbook' });
  assert.equal(
    (
      await call(
        'admin/units',
        { textbookId: book.id, code: '1', title: 'Number' },
        admin,
      )
    ).status,
    400,
  );
  await approve(book.id);
  assert.equal(
    (
      await call(
        'upload',
        { ...file, kind: 'Past paper', textbookId: book.id },
        admin,
      )
    ).status,
    400,
  );
  unit1 = await ok('admin/units', {
    textbookId: book.id,
    code: '1',
    title: 'Number',
  });
  unit2 = await ok('admin/units', {
    textbookId: book.id,
    code: '2',
    title: 'Geometry',
  });
  paper = await ok('upload', {
    ...file,
    kind: 'Past paper',
    textbookId: book.id,
  });
});
test('cross-subject relationships fail for uploads, coverage and questions', async () => {
  const chemistry = await ok('upload', {
    ...file,
    subject: 'chemistry',
    kind: 'Textbook',
  });
  await approve(chemistry.id);
  foreignUnit = await ok('admin/units', {
    textbookId: chemistry.id,
    code: '1',
    title: 'Particles',
  });
  assert.equal(
    (
      await call(
        'upload',
        {
          ...file,
          subject: 'chemistry',
          kind: 'Past paper',
          textbookId: book.id,
        },
        admin,
      )
    ).status,
    400,
  );
  assert.equal(
    (
      await call(
        'upload',
        {
          ...file,
          subject: 'chemistry',
          kind: 'Marking scheme',
          paperId: paper.id,
        },
        admin,
      )
    ).status,
    400,
  );
  assert.equal(
    (
      await call(
        'admin/coverage',
        {
          course: 'iGCSE',
          subject: 'maths',
          grade: 'Grade 10',
          term: 'Term1',
          unitIds: [foreignUnit.id],
        },
        admin,
      )
    ).status,
    400,
  );
  const question = {
    paperId: paper.id,
    number: '1',
    title: 'Half',
    prompt: 'What is half of 10?',
    marks: 1,
    type: 'numeric',
    answer: 5,
    explanation: '10 divided by 2 is 5.',
    points: 'Answer 5',
    hints: 'Divide by 2',
    status: 'approved',
  };
  for (const unitIds of [[], [foreignUnit.id], ['missing']])
    assert.equal(
      (await call('admin/questions', { ...question, unitIds }, admin)).status,
      400,
    );
  q1 = await ok('admin/questions', { ...question, unitIds: [unit1.id] });
  q2 = await ok('admin/questions', {
    ...question,
    number: '2',
    title: 'Mixed question',
    unitIds: [unit1.id, unit2.id],
  });
});
test('paper completeness sign-off and restricted source access', async () => {
  assert.equal(
    (
      await call(
        'documents/review',
        { id: paper.id, status: 'approved' },
        admin,
      )
    ).status,
    400,
  );
  await approve(paper.id, true);
  const scheme = await ok('upload', {
    ...file,
    kind: 'Marking scheme',
    paperId: paper.id,
  });
  await approve(scheme.id);
  assert.equal((await call('files/' + paper.id, undefined, alex)).status, 403);
  assert.equal((await call('files/' + scheme.id, undefined, alex)).status, 403);
  assert.equal((await call('files/' + book.id, undefined, alex)).status, 200);
  assert.equal(
    (await call('documents/review', { id: book.id, status: 'pending' }, parent))
      .status,
    403,
  );
});
test('all mapped units must be covered; term and grade matching is exact', async () => {
  await ok('admin/coverage', {
    course: 'iGCSE',
    subject: 'maths',
    grade: 'Grade 10',
    term: 'Term1',
    unitIds: [unit1.id],
  });
  const s = await ok('state', undefined, alex);
  assert.deepEqual(
    s.questions.map((q) => q.id),
    [q1.id],
  );
  assert(s.questions.every((q) => !('answer' in q) && !('explanation' in q)));
  assert.equal(
    (await call('lesson?question=' + q2.id, undefined, alex)).status,
    403,
  );
  assert.equal(
    (await call('attempt', { questionId: q2.id, answer: '5' }, alex)).status,
    403,
  );
  await ok('admin/students', {
    ...enrolment,
    id: 'child-two',
    name: 'Other Child',
    parentId: 'parent-two',
    grade: 'Grade 11',
  });
  assert.equal((await ok('state', undefined, otherChild)).questions.length, 0);
  assert.equal(
    (await call('exams/start', { subject: 'maths' }, otherChild)).status,
    409,
  );
});
test('drafts, attempts, reviews, and files remain family-scoped', async () => {
  await ok('drafts', { questionId: q1.id, answer: 'draft' }, alex);
  assert.equal(
    Object.keys((await ok('state', undefined, otherChild)).drafts).length,
    0,
  );
  attempt = await ok('attempt', { questionId: q1.id, answer: '5' }, alex);
  assert.equal(attempt.mark, 1);
  assert.equal((await ok('state', undefined, otherParent)).attempts.length, 0);
  assert.equal(
    (
      await call(
        'reviews',
        { id: attempt.id, mark: 1, feedback: 'Test' },
        otherParent,
      )
    ).status,
    403,
  );
  assert.equal(
    (
      await call(
        'reviews',
        { id: attempt.id, mark: 99, feedback: 'Test' },
        parent,
      )
    ).status,
    400,
  );
  await ok(
    'reviews',
    { id: attempt.id, mark: 1, feedback: 'Good calculation' },
    parent,
  );
  assert.equal((await ok('state', undefined, alex)).reviews.length, 1);
  const work = await ok('upload', { ...file, purpose: 'working' }, alex);
  assert.equal((await call('files/' + work.id, undefined, parent)).status, 200);
  assert.equal(
    (await call('files/' + work.id, undefined, otherParent)).status,
    403,
  );
});
test('assignments validate family ownership and term eligibility', async () => {
  const a = { studentId: 'alex', questionId: q1.id, due: '2026-12-01' };
  assert.equal((await call('assignments', a, otherParent)).status, 403);
  assert.equal(
    (await call('assignments', { ...a, questionId: q2.id }, parent)).status,
    400,
  );
  await ok('assignments', a, parent);
});
test('mock exams use eligible units, block hints and preserve submission scope', async () => {
  exam = await ok('exams/start', { subject: 'maths' }, alex);
  assert.deepEqual(exam.questionIds, [q1.id]);
  assert.equal(exam.scope.term, 'Term1');
  assert.equal((await call('hint', { questionId: q1.id }, alex)).status, 409);
  assert.equal(
    (await call('lesson?question=' + q1.id, undefined, alex)).status,
    409,
  );
  assert.equal(
    (
      await call(
        'exams/save',
        { id: exam.id, questionId: q1.id, answer: '5' },
        parent,
      )
    ).status,
    403,
  );
  assert.equal(
    (
      await call(
        'admin/students',
        {
          ...enrolment,
          id: 'alex',
          parentId: 'parent',
          name: 'Alex',
          term: 'Term2',
        },
        admin,
      )
    ).status,
    409,
  );
  await ok('exams/save', { id: exam.id, questionId: q1.id, answer: '5' }, alex);
  await ok('exams/submit', { id: exam.id }, alex);
  await ok('exams/submit', { id: exam.id }, alex);
  assert.equal(
    (await ok('state', undefined, alex)).attempts.filter(
      (a) => a.examId === exam.id,
    ).length,
    1,
  );
});
test('term progression accumulates prior covered units and empty coverage fails closed', async () => {
  await ok('admin/students', {
    ...enrolment,
    id: 'alex',
    parentId: 'parent',
    name: 'Alex',
    term: 'Term2',
    progression: ['Grade 10|Term1', 'Grade 10|Term2'],
  });
  assert.equal((await ok('state', undefined, alex)).questions.length, 1);
  await ok('admin/coverage', {
    course: 'iGCSE',
    subject: 'maths',
    grade: 'Grade 10',
    term: 'Term2',
    unitIds: [unit1.id, unit2.id],
  });
  assert.equal((await ok('state', undefined, alex)).questions.length, 2);
  assert.equal((await ok('plans', {}, alex)).items.length, 1);
  assert.equal(
    (await call('plans', { studentId: 'alex' }, otherParent)).status,
    403,
  );
});
test('expired exams reject edits but accept saved submission', async () => {
  const e = await ok('exams/start', { subject: 'maths' }, alex);
  const now = Date.now;
  Date.now = () => now() + 16 * 60000;
  try {
    assert.equal(
      (
        await call(
          'exams/save',
          { id: e.id, questionId: q1.id, answer: '5' },
          alex,
        )
      ).status,
      409,
    );
    await ok('exams/submit', { id: e.id }, alex);
  } finally {
    Date.now = now;
  }
});
test('origin and method checks; logout', async () => {
  assert.equal((await call('admin/accounts', undefined, admin)).status, 405);
  assert.equal(
    (await call('plans', {}, alex, { origin: 'http://untrusted.test' })).status,
    403,
  );
  assert.equal(
    (await call('state', undefined, alex, { host: 'untrusted.test' })).status,
    403,
  );
  await ok('logout', {}, alex);
  assert.equal((await call('state', undefined, alex)).status, 401);
});
