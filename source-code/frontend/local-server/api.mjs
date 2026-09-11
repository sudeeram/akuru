import {
  readFileSync,
  writeFileSync,
  mkdirSync,
  existsSync,
  renameSync,
} from 'node:fs';
import {
  randomBytes,
  scryptSync,
  timingSafeEqual,
  randomUUID,
} from 'node:crypto';
import { resolve } from 'node:path';
import {
  questions as seedQuestions,
  credentials,
  initialState,
} from './seed.mjs';
import {
  subjects,
  courseCatalog,
  grades,
  terms,
  kinds,
  migrate,
  eligible,
} from './curriculum.mjs';
import { adminRoutes } from './admin.mjs';

const DATA = resolve(
  process.env.PORTAL_DATA_DIR ||
    new URL('../.local-data/', import.meta.url).pathname,
);
mkdirSync(DATA, { recursive: true });
const dbPath = resolve(DATA, 'state.json');
const fresh = !existsSync(dbPath);
let db = !fresh ? JSON.parse(readFileSync(dbPath, 'utf8')) : initialState();
if (!fresh && db.schemaVersion !== 2)
  writeFileSync(
    resolve(DATA, `state-before-v2-${Date.now()}.json`),
    JSON.stringify(db, null, 2),
  );
for (const s of db.students) {
  s.grade ??=
    s.id === 'jamie' ? 'Year 5' : s.id === 'sam' ? 'Year 10' : 'Year 8';
  s.courses ??= Object.fromEntries(
    s.subjects.map((id) => [
      id,
      {
        level: s.level,
        syllabus: 'Demo course — select specification before real use',
      },
    ]),
  );
}
migrate(db, credentials, seedQuestions, fresh);
const users = db.users;
const questions = db.questions;
db.drafts ??= {};
const sessions = new Map();
const failures = new Map();
const save = () => {
  writeFileSync(dbPath + '.tmp', JSON.stringify(db, null, 2));
  renameSync(dbPath + '.tmp', dbPath);
};
save();
const fail = (status, message) => {
  throw Object.assign(new Error(message), { status });
};
const str = (v, max = 10000) =>
  typeof v === 'string' ? v.trim().slice(0, max) : '';
const parent = (u) => {
  if (u.role !== 'parent') fail(403, 'Parent access required.');
};
const own = (u, id) => {
  if (!canSeeStudent(u, id))
    fail(403, 'Student is not available to this account.');
};
const canSeeStudent = (u, id) =>
  db.students.some(
    (s) =>
      s.id === id &&
      (u.role === 'admin' ||
        (u.role === 'parent' ? s.parentId === u.id : s.id === u.id)),
  );
const allowedQuestion = (u, q) =>
  !!q &&
  (u.role === 'admin' ||
    db.students.some((s) => canSeeStudent(u, s.id) && eligible(db, s, q)));
const publicQ = (q) => {
  const { answer, hints, explanation, points, ...safe } = q;
  return safe;
};
const visible = (u, x) => canSeeStudent(u, x.studentId);
const resultFor = (q, answer, hasFile) => {
  let mark = null;
  let status = 'needs-review';
  if (q.type === 'numeric' && !hasFile) {
    const clean = answer.replace(/[%°N\s]/g, '');
    const number = clean !== '' ? Number(clean) : NaN;
    if (Number.isFinite(number) && Math.abs(number - q.answer) < 1e-8) {
      mark = q.marks;
      status = 'checked';
    }
  }
  return {
    mark,
    status,
    explanation: q.explanation,
    points: q.points,
    feedback:
      mark !== null
        ? 'Your final answer is correct. Compare your method with the worked example.'
        : 'Saved for parent review. A final answer alone may not show all method marks.',
  };
};
export function localApi() {
  return {
    name: 'family-local-api',
    configureServer(server) {
      server.middlewares.use(handler);
    },
    configurePreviewServer(server) {
      server.middlewares.use(handler);
    },
  };
}
export async function handler(req, res, next) {
  const url = new URL(req.url, 'http://localhost');
  if (!url.pathname.startsWith('/api/')) return next();
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('X-Content-Type-Options', 'nosniff');
  const json = (status, data) => {
    res.statusCode = status;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify(data));
  };
  try {
    if (
      !['GET', 'HEAD'].includes(req.method) &&
      req.headers.origin &&
      req.headers.origin !== `http://${req.headers.host}`
    )
      fail(403, 'Origin not allowed.');
    let body = {};
    if (req.method === 'POST') {
      let raw = '';
      for await (const part of req) {
        raw += part;
        if (raw.length > 9_000_000)
          fail(413, 'File too large. Maximum upload is 5 MB.');
      }
      try {
        body = raw ? JSON.parse(raw) : {};
      } catch {
        fail(400, 'Invalid JSON.');
      }
    }
    const path = url.pathname;
    if (
      !['127.0.0.1', 'localhost'].includes(
        (req.headers.host || '').split(':')[0],
      )
    )
      fail(403, 'Local access only.');
    const reads =
      path === '/api/state' ||
      path === '/api/lesson' ||
      path.startsWith('/api/files/');
    if (
      (reads && !['GET', 'HEAD'].includes(req.method)) ||
      (!reads && req.method !== 'POST')
    )
      fail(405, 'Method not allowed.');
    if (path === '/api/login' && req.method === 'POST') {
      const key = req.socket.remoteAddress;
      const f = failures.get(key);
      if (f && f.count >= 10 && Date.now() - f.at < 60000)
        fail(429, 'Too many attempts. Please wait a minute.');
      const u = users.find(
        (u) => u.id === str(body.username, 40).toLowerCase(),
      );
      const valid =
        u &&
        timingSafeEqual(
          Buffer.from(u.hash, 'hex'),
          scryptSync(str(body.password, 100), u.salt, 64),
        );
      if (!valid) {
        failures.set(key, {
          count: (f && Date.now() - f.at < 60000 ? f.count : 0) + 1,
          at: Date.now(),
        });
        fail(401, 'The username or password is incorrect.');
      }
      failures.delete(key);
      const token = randomBytes(32).toString('hex');
      sessions.set(token, { id: u.id, expires: Date.now() + 86400000 });
      res.setHeader(
        'Set-Cookie',
        `portal_session=${token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400`,
      );
      return json(200, { id: u.id, name: u.name, role: u.role });
    }
    const token = (req.headers.cookie || '').match(
      /(?:^|; )portal_session=([^;]+)/,
    )?.[1];
    const session = sessions.get(token);
    const u =
      session && session.expires > Date.now()
        ? users.find((u) => u.id === session.id)
        : null;
    if (!u) fail(401, 'Please sign in.');
    if (adminRoutes({ path, body, user: u, db, fail, save, json })) return;
    if (path === '/api/logout') {
      sessions.delete(token);
      res.setHeader(
        'Set-Cookie',
        'portal_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0',
      );
      return json(200, { ok: true });
    }
    if (path === '/api/state')
      return json(200, {
        user: { id: u.id, name: u.name, role: u.role },
        subjects,
        catalog: {
          courses: courseCatalog,
          activeCourses: ['iGCSE'],
          grades,
          terms,
          kinds,
          progressionPairs: grades.flatMap((grade) =>
            terms.map((term) => ({ grade, term })),
          ),
        },
        accounts:
          u.role === 'admin'
            ? users.map(({ id, name, role }) => ({ id, name, role }))
            : [],
        units: db.units,
        coverage: db.coverage,
        questionBank:
          u.role === 'admin'
            ? questions.filter((q) => q.status !== 'legacy')
            : [],
        questions: questions
          .filter(
            (q) =>
              allowedQuestion(u, q) ||
              db.exams.some(
                (e) =>
                  e.status === 'active' &&
                  visible(u, e) &&
                  e.questionIds.includes(q.id),
              ),
          )
          .map(publicQ),
        students: db.students.filter((s) => canSeeStudent(u, s.id)),
        attempts: db.attempts.filter((x) => visible(u, x)),
        assignments: db.assignments.filter(
          (x) =>
            visible(u, x) &&
            questions.some(
              (q) =>
                q.id === x.questionId &&
                eligible(
                  db,
                  db.students.find((s) => s.id === x.studentId),
                  q,
                ),
            ),
        ),
        reviews: db.reviews.filter((x) => visible(u, x)),
        documents:
          u.role === 'admin'
            ? db.documents
            : db.documents.filter(
                (d) =>
                  d.status === 'approved' &&
                  ['Textbook', 'Reference material'].includes(d.kind) &&
                  db.students.some(
                    (s) =>
                      canSeeStudent(u, s.id) && s.subjects.includes(d.subject),
                  ),
              ),
        exams: db.exams.filter((x) => visible(u, x)),
        drafts: u.role === 'student' ? db.drafts[u.id] || {} : {},
        plans: Object.fromEntries(
          Object.entries(db.plans).filter(([id]) => canSeeStudent(u, id)),
        ),
      });
    if (path === '/api/lesson' && req.method === 'GET') {
      const q = questions.find(
        (q) => q.id === url.searchParams.get('question'),
      );
      if (!q) fail(404, 'Question not found.');
      if (!allowedQuestion(u, q))
        fail(403, 'Question is outside your covered units.');
      if (
        u.role === 'student' &&
        db.exams.some((e) => e.studentId === u.id && e.status === 'active')
      )
        fail(409, 'Finish your mock exam before opening explanations.');
      return json(200, {
        explanation: q.explanation,
        points: q.points,
        hints: q.hints,
      });
    }
    if (path === '/api/hint' && req.method === 'POST') {
      if (u.role !== 'student') fail(403, 'Sign in as a student.');
      if (db.exams.some((e) => e.studentId === u.id && e.status === 'active'))
        fail(409, 'Hints are unavailable during mock exams.');
      const q = questions.find((q) => q.id === body.questionId);
      if (!q) fail(404, 'Question not found.');
      if (!allowedQuestion(u, q))
        fail(403, 'Question is outside your covered units.');
      return json(200, {
        hint: q.hints[
          Math.max(0, Math.min(Number(body.index) || 0, q.hints.length - 1))
        ],
        total: q.hints.length,
      });
    }
    if (path === '/api/drafts' && req.method === 'POST') {
      if (u.role !== 'student') fail(403, 'Student access required.');
      const q = questions.find((q) => q.id === body.questionId);
      if (!q) fail(404, 'Question not found.');
      if (!allowedQuestion(u, q))
        fail(403, 'Question is outside your covered units.');
      if (!db.students.find((s) => s.id === u.id).subjects.includes(q.subject))
        fail(403, 'Subject not enrolled.');
      db.drafts[u.id] ??= {};
      db.drafts[u.id][q.id] = str(body.answer);
      save();
      return json(200, { saved: true });
    }
    if (path === '/api/attempt' && req.method === 'POST') {
      if (u.role !== 'student') fail(403, 'Sign in as a student.');
      if (db.exams.some((e) => e.studentId === u.id && e.status === 'active'))
        fail(409, 'Submit your active mock exam first.');
      const q = questions.find((q) => q.id === body.questionId);
      if (!q) fail(404, 'Question not found.');
      if (!allowedQuestion(u, q))
        fail(403, 'Question is outside your covered units.');
      const answer = str(body.answer);
      const fileId = str(body.fileId, 100);
      if (!answer && !fileId)
        fail(400, 'Enter an answer or upload your working.');
      if (
        fileId &&
        !db.files.some((f) => f.id === fileId && f.studentId === u.id)
      )
        fail(403, 'File unavailable.');
      const s = db.students.find((s) => s.id === u.id);
      if (!s.subjects.includes(q.subject))
        fail(403, 'You are not enrolled in this subject.');
      const a = {
        id: randomUUID(),
        studentId: u.id,
        subject: q.subject,
        questionId: q.id,
        title: q.title,
        answer,
        fileId,
        hints: Math.max(0, Math.min(10, Number(body.hints) || 0)),
        maxMarks: q.marks,
        createdAt: new Date().toISOString(),
        ...resultFor(q, answer, !!fileId),
      };
      db.attempts.push(a);
      if (db.drafts[u.id]) delete db.drafts[u.id][q.id];
      for (const x of db.assignments) {
        if (x.studentId === u.id && x.questionId === q.id) x.completed = true;
      }
      save();
      return json(201, a);
    }
    if (path === '/api/exams/start' && req.method === 'POST') {
      if (u.role !== 'student') fail(403, 'Student access required.');
      const active = db.exams.find(
        (e) => e.studentId === u.id && e.status === 'active',
      );
      if (active) return json(200, active);
      if (
        !db.students.find((s) => s.id === u.id).subjects.includes(body.subject)
      )
        fail(403, 'Subject not enrolled.');
      const student = db.students.find((s) => s.id === u.id);
      const qs = questions.filter(
        (q) => q.subject === body.subject && eligible(db, student, q),
      );
      if (!qs.length)
        fail(
          409,
          'No approved questions match the covered units for your grade and term. Ask an admin to configure coverage and question mappings.',
        );
      const e = {
        id: randomUUID(),
        studentId: u.id,
        subject: body.subject,
        status: 'active',
        startedAt: new Date().toISOString(),
        endsAt: new Date(Date.now() + 15 * 60000).toISOString(),
        questionIds: qs.map((q) => q.id),
        scope: {
          course: student.level,
          grade: student.grade,
          term: student.term,
          unitIds: [...new Set(qs.flatMap((q) => q.unitIds))],
        },
        answers: {},
        files: {},
      };
      db.exams.push(e);
      save();
      return json(201, e);
    }
    if (path === '/api/exams/save' && req.method === 'POST') {
      if (u.role !== 'student') fail(403, 'Student access required.');
      const e = db.exams.find((e) => e.id === body.id);
      if (!e) fail(404, 'Exam not found.');
      own(u, e.studentId);
      if (e.status !== 'active' || Date.now() > Date.parse(e.endsAt))
        fail(409, 'Exam time has ended. Submit your saved answers.');
      if (!e.questionIds.includes(body.questionId))
        fail(400, 'Question is not in this exam.');
      e.answers[body.questionId] = str(body.answer);
      if (body.fileId) {
        if (!db.files.some((f) => f.id === body.fileId && f.studentId === u.id))
          fail(403, 'File unavailable.');
        e.files[body.questionId] = body.fileId;
      }
      save();
      return json(200, e);
    }
    if (path === '/api/exams/submit' && req.method === 'POST') {
      if (u.role !== 'student') fail(403, 'Student access required.');
      const e = db.exams.find((e) => e.id === body.id);
      if (!e) fail(404, 'Exam not found.');
      own(u, e.studentId);
      if (e.status !== 'active') return json(200, e);
      for (const id of e.questionIds) {
        const q = questions.find((q) => q.id === id);
        const answer = e.answers[id] || '';
        db.attempts.push({
          id: randomUUID(),
          examId: e.id,
          studentId: e.studentId,
          subject: q.subject,
          questionId: q.id,
          title: q.title,
          answer,
          fileId: e.files?.[id] || '',
          hints: 0,
          maxMarks: q.marks,
          createdAt: new Date().toISOString(),
          ...(answer || e.files?.[id]
            ? resultFor(q, answer, !!e.files?.[id])
            : {
                mark: 0,
                status: 'checked',
                feedback: 'No answer submitted.',
                explanation: q.explanation,
                points: q.points,
              }),
        });
      }
      e.status = 'submitted';
      e.submittedAt = new Date().toISOString();
      save();
      return json(200, e);
    }
    if (path === '/api/upload' && req.method === 'POST') {
      if (
        u.role !== 'admin' &&
        !(u.role === 'student' && body.purpose === 'working')
      )
        fail(
          403,
          'Only admins can upload learning documents. Students may attach their own answer working.',
        );
      let book, linkedPaper;
      if (u.role === 'admin') {
        if (
          body.course !== 'iGCSE' ||
          !subjects.some((s) => s.id === body.subject) ||
          !kinds.includes(body.kind)
        )
          fail(400, 'Choose an iGCSE subject and document type.');
        if (body.kind === 'Past paper') {
          book = db.documents.find(
            (d) =>
              d.id === body.textbookId &&
              d.kind === 'Textbook' &&
              d.status === 'approved' &&
              d.subject === body.subject &&
              d.course === body.course,
          );
          if (!book || !db.units.some((unit) => unit.textbookId === book.id))
            fail(
              400,
              'Upload and approve a textbook with units for this subject before uploading past papers.',
            );
        }
        if (['Marking scheme', 'Examiner report'].includes(body.kind)) {
          linkedPaper = db.documents.find(
            (d) =>
              d.id === body.paperId &&
              d.kind === 'Past paper' &&
              !d.legacy &&
              d.subject === body.subject &&
              d.course === body.course,
          );
          if (!linkedPaper)
            fail(
              400,
              'Link this document to a past paper in the same subject.',
            );
        }
      }
      const name = str(body.name, 180);
      const match = String(body.data || '').match(
        /^data:(application\/pdf|image\/png|image\/jpeg|image\/webp);base64,([A-Za-z0-9+/=]+)$/,
      );
      if (!match) fail(400, 'Choose a PDF, PNG, JPEG or WebP file.');
      const data = Buffer.from(match[2], 'base64');
      if (data.length > 5 * 1024 * 1024)
        fail(413, 'Maximum file size is 5 MB.');
      const id = randomUUID();
      writeFileSync(resolve(DATA, id), data);
      db.files.push({
        id,
        name,
        type: match[1],
        studentId: u.role === 'student' ? u.id : null,
        owner: u.id,
      });
      if (u.role === 'admin')
        db.documents.push({
          id,
          name,
          subject: body.subject,
          course: 'iGCSE',
          textbookId: book?.id || null,
          paperId: linkedPaper?.id || null,
          mappingComplete: false,
          kind: str(body.kind, 60) || 'Textbook',
          status: 'pending',
          notes: '',
          createdAt: new Date().toISOString(),
        });
      save();
      return json(201, { id, name });
    }
    if (path.startsWith('/api/files/')) {
      const f = db.files.find((f) => f.id === path.split('/').pop());
      if (!f) fail(404, 'File not found.');
      if (
        u.role !== 'admin' &&
        !canSeeStudent(u, f.studentId) &&
        !db.documents.some(
          (d) =>
            d.id === f.id &&
            d.status === 'approved' &&
            ['Textbook', 'Reference material'].includes(d.kind) &&
            db.students.some(
              (s) => canSeeStudent(u, s.id) && s.subjects.includes(d.subject),
            ),
        )
      )
        fail(403, 'File unavailable.');
      res.setHeader('Content-Type', f.type);
      res.setHeader(
        'Content-Disposition',
        `inline; filename="${f.name.replace(/[^a-zA-Z0-9._-]/g, '_')}"`,
      );
      res.setHeader('Content-Security-Policy', "default-src 'none'; sandbox");
      return res.end(readFileSync(resolve(DATA, f.id)));
    }
    if (path === '/api/documents/review' && req.method === 'POST') {
      if (u.role !== 'admin') fail(403, 'Admin access required.');
      const d = db.documents.find((d) => d.id === body.id);
      if (!d) fail(404, 'Document not found.');
      if (!['approved', 'pending'].includes(body.status))
        fail(400, 'Invalid status.');
      if (body.status === 'approved' && d.legacy)
        fail(
          400,
          'Legacy upload needs re-import with curriculum metadata. Original file is retained.',
        );
      if (body.status === 'approved' && d.kind === 'Past paper') {
        const mapped = questions.filter((q) => q.paperId === d.id);
        if (
          body.mappingComplete !== true ||
          !mapped.length ||
          mapped.some((q) => q.status !== 'approved' || !q.unitIds.length)
        )
          fail(
            400,
            'Map and approve every question and confirm the complete paper has been entered.',
          );
        if (
          !db.documents.some(
            (b) => b.id === d.textbookId && b.status === 'approved',
          )
        )
          fail(400, 'Approve the linked textbook first.');
        d.mappingComplete = true;
      }
      d.status = body.status;
      d.notes = str(body.notes);
      save();
      return json(200, d);
    }
    if (path === '/api/students' && req.method === 'POST') {
      fail(403, 'Enrolments are managed through the Admin portal.');
    }
    if (path === '/api/assignments' && req.method === 'POST') {
      parent(u);
      own(u, body.studentId);
      const q = questions.find((q) => q.id === body.questionId);
      if (!q) fail(400, 'Choose a question.');
      if (
        !eligible(
          db,
          db.students.find((s) => s.id === body.studentId),
          q,
        )
      )
        fail(400, "Question is outside this child's covered units.");
      if (
        !db.students
          .find((s) => s.id === body.studentId)
          .subjects.includes(q.subject)
      )
        fail(400, 'Student is not enrolled in this subject.');
      if (
        !/^\d{4}-\d{2}-\d{2}$/.test(body.due) ||
        !Number.isFinite(Date.parse(body.due))
      )
        fail(400, 'Choose a due date.');
      const a = {
        id: randomUUID(),
        studentId: body.studentId,
        questionId: q.id,
        subject: q.subject,
        title: str(body.title, 150) || q.title,
        due: body.due,
        completed: false,
      };
      db.assignments.push(a);
      save();
      return json(201, a);
    }
    if (path === '/api/reviews' && req.method === 'POST') {
      parent(u);
      const a = db.attempts.find((a) => a.id === body.id);
      if (!a) fail(404, 'Attempt not found.');
      own(u, a.studentId);
      const mark = Number(body.mark);
      if (!Number.isInteger(mark) || mark < 0 || mark > a.maxMarks)
        fail(400, 'Enter a whole mark within the available marks.');
      const feedback = str(body.feedback);
      if (!feedback) fail(400, 'Add feedback for the student.');
      db.reviews.push({
        id: randomUUID(),
        attemptId: a.id,
        studentId: a.studentId,
        previousMark: a.mark,
        previousFeedback: a.feedback,
        mark,
        feedback,
        createdAt: new Date().toISOString(),
      });
      a.mark = mark;
      a.feedback = feedback;
      a.status = 'reviewed';
      save();
      return json(200, a);
    }
    if (path === '/api/plans' && req.method === 'POST') {
      const id = u.role === 'parent' ? body.studentId : u.id;
      own(u, id);
      const s = db.students.find((s) => s.id === id);
      const plan = s.subjects.map((subject) => {
        const available = questions.filter(
          (q) => q.subject === subject && eligible(db, s, q),
        );
        const attempts = db.attempts.filter(
          (a) => a.studentId === id && a.subject === subject,
        );
        const recent = attempts.at(-1);
        return {
          subject,
          topic: available[0]?.topic || 'Awaiting curriculum setup',
          minutes: 15,
          reason: !available.length
            ? 'Ask an admin to approve questions and configure covered units.'
            : recent
              ? recent.mark === null
                ? 'Review your submitted working with a parent.'
                : recent.mark < recent.maxMarks
                  ? 'Revisit the method from your latest attempt.'
                  : 'Try a related question without hints.'
              : 'Start with a short practice to find your starting point.',
        };
      });
      db.plans[id] = { updatedAt: new Date().toISOString(), items: plan };
      save();
      return json(200, db.plans[id]);
    }
    fail(404, 'Endpoint not found.');
  } catch (e) {
    json(e.status || 500, {
      error: e.status ? e.message : 'Something went wrong. Please try again.',
    });
  }
}
