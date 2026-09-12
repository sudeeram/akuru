'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { api, errorMessage, upload, type State, type Student } from '@/lib/api';
import { Heading, Picker, Empty } from './shared';

type Props = {
  data: State;
  view: string;
  refresh: () => Promise<void>;
  notify: (s: string) => void;
};
const options = (items: string[]) =>
  items.map((value) => ({ value, label: value }));
function Field({
  label,
  value,
  onChange,
  type = 'text',
  multiline = false,
  minLength,
  maxLength,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  multiline?: boolean;
  minLength?: number;
  maxLength?: number;
}) {
  return (
    <label className="stack">
      {label}
      {multiline ? (
        <Textarea
          aria-label={label}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          minLength={minLength}
          maxLength={maxLength}
          required
        />
      ) : (
        <Input
          aria-label={label}
          value={value}
          type={type}
          onChange={(e) => onChange(e.target.value)}
          required
        />
      )}
    </label>
  );
}
function Checks({
  label,
  items,
  selected,
  change,
}: {
  label: string;
  items: { id: string; name: string }[];
  selected: string[];
  change: (v: string[]) => void;
}) {
  return (
    <fieldset className="panel spaced">
      <legend>{label}</legend>
      {items.length ? (
        items.map((x) => (
          <label className="check-label spaced" key={x.id}>
            <Checkbox
              checked={selected.includes(x.id)}
              onCheckedChange={(yes) =>
                change(
                  yes
                    ? [...selected, x.id]
                    : selected.filter((id) => id !== x.id),
                )
              }
            />
            {x.name}
          </label>
        ))
      ) : (
        <p>No matching items yet.</p>
      )}
    </fieldset>
  );
}
export function AdminWorkspace(p: Props) {
  const [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  const [role, setRole] = useState('parent'),
    [username, setUsername] = useState(''),
    [name, setName] = useState(''),
    [password, setPassword] = useState('');
  const [parentId, setParentId] = useState(''),
    [editId, setEditId] = useState('');
  const [grade, setGrade] = useState('Grade 10'),
    [term, setTerm] = useState('Term1'),
    [progression, setProgression] = useState<string[]>(['Grade 10|Term1']),
    [enrolled, setEnrolled] = useState<string[]>(['maths']);
  const [subject, setSubject] = useState('maths'),
    [kind, setKind] = useState('Textbook'),
    [textbookId, setTextbookId] = useState(''),
    [paperId, setPaperId] = useState('');
  const [code, setCode] = useState(''),
    [unitTitle, setUnitTitle] = useState(''),
    [unitIds, setUnitIds] = useState<string[]>([]),
    [docId, setDocId] = useState(''),
    [notes, setNotes] = useState(''),
    [complete, setComplete] = useState(false);
  const [qid, setQid] = useState(''),
    [number, setNumber] = useState(''),
    [title, setTitle] = useState(''),
    [prompt, setPrompt] = useState(''),
    [marks, setMarks] = useState('1'),
    [type, setType] = useState('written'),
    [answer, setAnswer] = useState(''),
    [explanation, setExplanation] = useState(''),
    [points, setPoints] = useState(''),
    [hints, setHints] = useState('');
  const parents = p.data.accounts.filter((a) => a.role === 'parent');
  const books = p.data.documents.filter(
    (d) =>
      d.subject === subject && d.kind === 'Textbook' && d.status === 'approved',
  );
  const papers = p.data.documents.filter(
    (d) => d.subject === subject && d.kind === 'Past paper' && !d.legacy,
  );
  const paper = papers.find((d) => d.id === paperId);
  const doc = p.data.documents.find((d) => d.id === docId);
  const units = p.data.units.filter(
    (u) =>
      u.subject === subject &&
      (p.view === 'questions' ? u.textbookId === paper?.textbookId : true),
  );
  async function run(action: () => Promise<unknown>, message: string) {
    setBusy(true);
    setError('');
    try {
      await action();
      await p.refresh();
      p.notify(message);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  function edit(s: Student) {
    setEditId(s.id);
    setRole('student');
    setName(s.name);
    setParentId(s.parentId);
    setGrade(p.data.catalog.grades.includes(s.grade) ? s.grade : 'Grade 10');
    setTerm(s.term || 'Term1');
    setProgression(
      (s.progression || [{ grade: s.grade, term: s.term }]).map(
        (p) => `${p.grade}|${p.term}`,
      ),
    );
    setEnrolled(s.subjects);
  }
  function clearQuestion() {
    setQid('');
    setNumber('');
    setTitle('');
    setPrompt('');
    setMarks('1');
    setType('written');
    setAnswer('');
    setExplanation('');
    setPoints('');
    setHints('');
    setUnitIds([]);
  }
  const subjectPicker = (
    <Picker
      label="Subject"
      value={subject}
      onChange={(v) => {
        setSubject(v);
        setTextbookId('');
        setPaperId('');
        clearQuestion();
      }}
      options={p.data.subjects.map((s) => ({ value: s.id, label: s.name }))}
    />
  );
  const gradeTerm = (
    <div className="two-cols">
      <Picker
        label="Grade"
        value={grade}
        onChange={setGrade}
        options={options(p.data.catalog.grades)}
      />
      <Picker
        label="Term"
        value={term}
        onChange={setTerm}
        options={options(p.data.catalog.terms)}
      />
    </div>
  );
  const progressionPicker = (
    <Checks
      label="Completed/current Grade + Term progression"
      items={p.data.catalog.progressionPairs.map((x) => ({
        id: `${x.grade}|${x.term}`,
        name: `${x.grade} · ${x.term}`,
      }))}
      selected={progression}
      change={(v) => {
        setProgression(v);
        const last = v.at(-1)?.split('|');
        if (last) {
          setGrade(last[0]);
          setTerm(last[1]);
        }
      }}
    />
  );
  return (
    <>
      <Heading
        eyebrow="ADMIN · PHASE 1"
        title={
          {
            today: 'Curriculum administration',
            accounts: 'Accounts & enrolments',
            library: 'Documents & textbooks',
            units: 'Textbook units',
            coverage: 'Grade & term coverage',
            questions: 'Question mapping',
          }[p.view] || 'Administration'
        }
      >
        iGCSE · Grade 10 and Grade 11 · Term1, Term2 and Term3
      </Heading>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      <fieldset disabled={busy} style={{ border: 0, padding: 0, minWidth: 0 }}>
        {p.view === 'today' && (
          <>
            <div className="metric-grid">
              {[
                ['Parent accounts', parents.length],
                ['Students', p.data.students.length],
                ['Textbook units', p.data.units.length],
                ['Mapped questions', p.data.questionBank.length],
              ].map(([label, value]) => (
                <section className="panel metric" key={label}>
                  <strong>{value}</strong>
                  <span>{label}</span>
                </section>
              ))}
            </div>
            <section className="panel spaced">
              <h2>Prepare learning in this order</h2>
              <ol className="spaced">
                <li>
                  Create parent accounts, then children linked to those parents.
                </li>
                <li>
                  Assign each child iGCSE subjects, Grade 10 or 11, and a
                  current term.
                </li>
                <li>
                  Upload and approve a subject textbook. Register its units.
                </li>
                <li>Choose the units covered in each grade and term.</li>
                <li>
                  Upload a past paper linked to that subject textbook, then its
                  marking scheme and examiner report.
                </li>
                <li>
                  Enter and map every question to one or more units. Review each
                  question, then approve the complete paper.
                </li>
              </ol>
              <p className="spaced">
                Term mocks include a question only when all its units are
                covered. PDF extraction is not connected: enter question text
                and mappings manually.
              </p>
            </section>
            {p.data.students.some((s) => s.needsConfiguration) && (
              <div className="error spaced">
                Some existing learners need grade, term and subject confirmation
                in Accounts & enrolments. Historical work is preserved.
              </div>
            )}
          </>
        )}
        {p.view === 'accounts' && (
          <>
            <form
              className="panel stack"
              onSubmit={(e) => {
                e.preventDefault();
                void run(
                  async () => {
                    await api(
                      editId ? 'admin/students' : 'admin/accounts',
                      editId || role === 'student'
                        ? {
                            id: editId,
                            username,
                            name,
                            password,
                            role,
                            parentId,
                            level: 'iGCSE',
                            grade,
                            term,
                            progression,
                            subjects: enrolled,
                          }
                        : { username, name, password, role },
                    );
                    setPassword('');
                    setEditId('');
                    setUsername('');
                    setName('');
                  },
                  editId ? 'Enrolment saved.' : 'Account created.',
                );
              }}
            >
              <h2>{editId ? `Edit ${editId}` : 'Create an account'}</h2>
              {!editId && (
                <>
                  <Picker
                    label="Role"
                    value={role}
                    onChange={setRole}
                    options={options(['parent', 'student'])}
                  />
                  <Field
                    label="Username"
                    value={username}
                    onChange={setUsername}
                    minLength={3}
                    maxLength={40}
                  />
                  <Field
                    label="Temporary password (at least 12 characters)"
                    type="password"
                    value={password}
                    onChange={setPassword}
                    minLength={12}
                    maxLength={200}
                  />
                </>
              )}
              <Field label="Full name" value={name} onChange={setName} />
              {role === 'student' && (
                <>
                  <Picker
                    label="Parent account"
                    value={parentId}
                    onChange={setParentId}
                    options={parents.map((a) => ({
                      value: a.id,
                      label: `${a.name} (${a.id})`,
                    }))}
                  />
                  <Picker
                    label="Course"
                    value="iGCSE"
                    onChange={() => {}}
                    options={options(p.data.catalog.activeCourses)}
                  />
                  {gradeTerm}
                  {progressionPicker}
                  <Checks
                    label="Subjects"
                    items={p.data.subjects}
                    selected={enrolled}
                    change={setEnrolled}
                  />
                </>
              )}
              <div className="button-row">
                <Button type="submit" className="primary">
                  {editId ? 'Save enrolment' : 'Create account'}
                </Button>
                {editId && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setEditId('');
                      setName('');
                    }}
                  >
                    Cancel edit
                  </Button>
                )}
              </div>
            </form>
            <div className="learner-grid spaced">
              {p.data.students.map((s) => (
                <section className="panel" key={s.id}>
                  <h3>{s.name}</h3>
                  <p>
                    {s.id} · Parent: {s.parentId}
                  </p>
                  <p>
                    {s.grade} · {s.term || 'Term not configured'} ·{' '}
                    {(s.progression || []).length} progression step(s)
                  </p>
                  <p>
                    {s.needsConfiguration
                      ? 'Admin configuration required'
                      : 'iGCSE'}
                  </p>
                  <Button
                    className="spaced"
                    variant="outline"
                    onClick={() => edit(s)}
                  >
                    Edit {s.name}
                  </Button>
                </section>
              ))}
            </div>
            <section className="panel spaced">
              <h2>Parent accounts</h2>
              {parents.map((a) => (
                <p key={a.id}>
                  {a.name} · {a.id}
                </p>
              ))}
            </section>
          </>
        )}
        {p.view === 'library' && (
          <>
            <section className="panel stack">
              <h2>Upload a learning document</h2>
              {subjectPicker}
              <Picker
                label="Document type"
                value={kind}
                onChange={setKind}
                options={options(p.data.catalog.kinds)}
              />
              {kind === 'Past paper' && (
                <>
                  <Picker
                    label="Approved subject textbook"
                    value={textbookId}
                    onChange={setTextbookId}
                    options={books.map((b) => ({ value: b.id, label: b.name }))}
                  />
                  <p>Register textbook units before uploading a past paper.</p>
                </>
              )}
              {['Marking scheme', 'Examiner report'].includes(kind) && (
                <Picker
                  label="Related past paper"
                  value={paperId}
                  onChange={setPaperId}
                  options={papers.map((b) => ({ value: b.id, label: b.name }))}
                />
              )}
              <label htmlFor="admin-document-file">
                Document file · PDF or image, up to 5 MB
                <Input
                  id="admin-document-file"
                  type="file"
                  aria-label="Document file"
                  accept="application/pdf,image/png,image/jpeg,image/webp"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f)
                      void run(
                        () =>
                          upload(f, {
                            purpose: 'document',
                            course: 'iGCSE',
                            subject,
                            kind,
                            textbookId,
                            paperId,
                          }),
                        'Uploaded for admin review.',
                      );
                    e.target.value = '';
                  }}
                />
              </label>
            </section>
            <section className="panel spaced stack">
              <h2>Review documents</h2>
              <Picker
                label="Document to review"
                value={docId}
                onChange={(v) => {
                  setDocId(v);
                  setNotes(
                    p.data.documents.find((d) => d.id === v)?.notes || '',
                  );
                  setComplete(false);
                }}
                options={p.data.documents.map((d) => ({
                  value: d.id,
                  label: `${d.name} · ${d.subject} · ${d.kind} · ${d.status}`,
                }))}
              />
              {doc && (
                <>
                  <a
                    href={`/api/files/${doc.id}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open original document
                  </a>
                  <label htmlFor="admin-review-notes">
                    Review notes
                    <Textarea
                      id="admin-review-notes"
                      aria-label="Review notes"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                    />
                  </label>
                  {doc.kind === 'Past paper' && (
                    <label className="check-label" htmlFor="paper-completeness">
                      <Checkbox
                        id="paper-completeness"
                        checked={complete}
                        onCheckedChange={(v) => setComplete(!!v)}
                      />
                      I have entered every question, checked its unit mappings
                      and approved each question.
                    </label>
                  )}
                  <div className="button-row">
                    <Button
                      variant="outline"
                      onClick={() =>
                        void run(
                          () =>
                            api('documents/review', {
                              id: doc.id,
                              status: 'pending',
                              notes,
                            }),
                          'Document held for review.',
                        )
                      }
                    >
                      Keep in review
                    </Button>
                    <Button
                      className="primary"
                      onClick={() =>
                        void run(
                          () =>
                            api('documents/review', {
                              id: doc.id,
                              status: 'approved',
                              notes,
                              mappingComplete: complete,
                            }),
                          'Document approved.',
                        )
                      }
                    >
                      Approve document
                    </Button>
                  </div>
                </>
              )}
            </section>
          </>
        )}
        {p.view === 'units' && (
          <>
            <form
              className="panel stack"
              onSubmit={(e) => {
                e.preventDefault();
                void run(async () => {
                  await api('admin/units', {
                    textbookId,
                    code,
                    title: unitTitle,
                  });
                  setCode('');
                  setUnitTitle('');
                }, 'Textbook unit added.');
              }}
            >
              {subjectPicker}
              <Picker
                label="Textbook"
                value={textbookId}
                onChange={setTextbookId}
                options={books.map((b) => ({ value: b.id, label: b.name }))}
              />
              <Field label="Unit code" value={code} onChange={setCode} />
              <Field
                label="Unit title"
                value={unitTitle}
                onChange={setUnitTitle}
              />
              <Button type="submit" className="primary">
                Add unit
              </Button>
            </form>
            <section className="panel spaced">
              <h2>Registered units</h2>
              {units.map((u) => (
                <p key={u.id}>
                  {u.code} · {u.title} ·{' '}
                  {p.data.documents.find((d) => d.id === u.textbookId)?.name}
                </p>
              ))}
            </section>
          </>
        )}
        {p.view === 'coverage' && (
          <section className="panel stack">
            {subjectPicker}
            {gradeTerm}
            <p>
              Choose the complete set covered for this term exam. Earlier terms
              are included only when you explicitly select their units here.
            </p>
            <Button
              variant="outline"
              onClick={() =>
                setUnitIds(
                  p.data.coverage.find(
                    (c) =>
                      c.subject === subject &&
                      c.grade === grade &&
                      c.term === term,
                  )?.unitIds || [],
                )
              }
            >
              Load saved coverage
            </Button>
            <Checks
              label="Covered units"
              items={units.map((u) => ({
                id: u.id,
                name: `${u.code} · ${u.title}`,
              }))}
              selected={unitIds}
              change={setUnitIds}
            />
            <Button
              className="primary"
              onClick={() =>
                void run(
                  () =>
                    api('admin/coverage', {
                      course: 'iGCSE',
                      subject,
                      grade,
                      term,
                      unitIds,
                    }),
                  'Term coverage saved.',
                )
              }
            >
              Save term coverage
            </Button>
            <h3>Saved coverage</h3>
            {p.data.coverage
              .filter((c) => c.subject === subject)
              .map((c) => (
                <p key={c.grade + c.term}>
                  {c.grade} · {c.term}:{' '}
                  {c.unitIds
                    .map((id) => p.data.units.find((u) => u.id === id)?.title)
                    .join(', ') || 'No units'}
                </p>
              ))}
          </section>
        )}
        {p.view === 'questions' && (
          <>
            <form
              className="panel stack"
              onSubmit={(e) => {
                e.preventDefault();
                void run(async () => {
                  await api('admin/questions', {
                    id: qid || undefined,
                    paperId,
                    number,
                    title,
                    prompt,
                    marks: Number(marks),
                    type,
                    answer,
                    explanation,
                    points,
                    hints,
                    unitIds,
                    status: 'approved',
                  });
                  clearQuestion();
                }, 'Question reviewed and mapped. Approve the complete paper in Documents & textbooks when all questions are entered.');
              }}
            >
              {subjectPicker}
              <Picker
                label="Past paper"
                value={paperId}
                onChange={(v) => {
                  setPaperId(v);
                  clearQuestion();
                }}
                options={papers.map((b) => ({ value: b.id, label: b.name }))}
              />
              <p>
                Use the source document and its marking scheme to enter each
                question manually. Include all subparts as separate numbered
                questions when they can be assessed independently.
              </p>
              <Field
                label="Question number / subpart"
                value={number}
                onChange={setNumber}
              />
              <Field label="Question title" value={title} onChange={setTitle} />
              <Field
                label="Question text (include equations and describe any required diagram)"
                value={prompt}
                onChange={setPrompt}
                multiline
              />
              <div className="two-cols">
                <Field
                  label="Available marks"
                  value={marks}
                  onChange={setMarks}
                  type="number"
                />
                <Picker
                  label="Answer type"
                  value={type}
                  onChange={setType}
                  options={options(['written', 'numeric'])}
                />
              </div>
              {type === 'numeric' && (
                <Field
                  label="Correct numeric answer"
                  value={answer}
                  onChange={setAnswer}
                  type="number"
                />
              )}
              <Field
                label="Worked explanation"
                value={explanation}
                onChange={setExplanation}
                multiline
              />
              <Field
                label="Marking points (one per line)"
                value={points}
                onChange={setPoints}
                multiline
              />
              <label htmlFor="question-hints">
                Optional hints (one per line)
                <Textarea
                  id="question-hints"
                  aria-label="Optional hints"
                  value={hints}
                  onChange={(e) => setHints(e.target.value)}
                />
              </label>
              <Checks
                label="Required units from this paper's textbook"
                items={units.map((u) => ({
                  id: u.id,
                  name: `${u.code} · ${u.title}`,
                }))}
                selected={unitIds}
                change={setUnitIds}
              />
              <Button type="submit" className="primary">
                Save reviewed question
              </Button>
            </form>
            <section className="panel spaced">
              <h2>Questions in this paper</h2>
              {p.data.questionBank
                .filter((q) => q.paperId === paperId)
                .map((q) => (
                  <div className="spread spaced" key={q.id}>
                    <span>
                      {q.number} · {q.title} · {q.unitIds.length} unit(s)
                    </span>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setQid(q.id);
                        setNumber(q.number);
                        setTitle(q.title);
                        setPrompt(q.prompt);
                        setMarks(String(q.marks));
                        setType(q.type);
                        setAnswer(q.answer === null ? '' : String(q.answer));
                        setExplanation(q.explanation);
                        setPoints(q.points.join('\n'));
                        setHints(q.hints.join('\n'));
                        setUnitIds(q.unitIds);
                      }}
                    >
                      Edit question {q.number}
                    </Button>
                  </div>
                ))}
            </section>
          </>
        )}
      </fieldset>
    </>
  );
}

export function FamilyCourses({ data }: { data: State }) {
  return (
    <>
      <Heading title="Your children's courses">
        An Admin manages accounts, grades, terms and subject enrolments. Contact
        your Admin to request a change.
      </Heading>
      <div className="learner-grid">
        {data.students.map((s) => (
          <section className="panel" key={s.id}>
            <h2>{s.name}</h2>
            <p>
              {s.level} · {s.grade} · {s.term || 'Term not configured'}
            </p>
            {s.needsConfiguration && (
              <p>Admin confirmation required before term practice.</p>
            )}
            <ul>
              {s.subjects.map((id) => (
                <li key={id}>{data.subjects.find((x) => x.id === id)?.name}</li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </>
  );
}
export function FamilyLibrary({ data }: { data: State }) {
  return (
    <>
      <Heading title="Approved learning resources">
        Your Admin uploads and reviews textbooks and reference material. Full
        past papers remain in the Admin library; term practice uses only
        eligible mapped questions.
      </Heading>
      <section className="panel">
        {data.documents.length ? (
          data.documents.map((d) => (
            <a
              className="resource-row"
              key={d.id}
              href={`/api/files/${d.id}`}
              target="_blank"
              rel="noreferrer"
            >
              {d.name} · {d.subject} · {d.kind}
            </a>
          ))
        ) : (
          <Empty title="No approved resources yet">
            Ask your Admin to prepare your subjects.
          </Empty>
        )}
      </section>
    </>
  );
}
