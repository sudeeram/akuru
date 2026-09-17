'use client';
import { useEffect, useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import {
  api,
  errorMessage,
  getDocumentExtraction,
  getLatestDocumentJob,
  getCurriculumPlan,
  createCurriculumPlanDraft,
  getOfficialMaterialReview,
  getPaperMappings,
  publishCurriculumPlan,
  publishOfficialMaterialReview,
  publishQuestionMappings,
  saveCurriculumPlan,
  saveOfficialMaterialReview,
  proposeOfficialMaterialReview,
  saveQuestionMappings,
  suggestQuestionMappings,
  removeDocument,
  retryDocument,
  uploadLearningDocument,
  type DocumentExtraction,
  type DocumentJob,
  type State,
  type Student,
  type CurriculumPlan,
  type OfficialMaterialReview,
  type PaperMappings,
  type TopicMapping,
  type AssessmentAudit,
  getAssessmentAudit,
  reassessAssessment,
  updateExtractionBlock,
  updateExtractionPage,
} from '@/lib/api';
import { ResultReview } from './result-review';
import { MediaAdmin } from './media-admin';
import { EvaluationAdmin } from './evaluation-admin';
import { OperationsAdmin } from './operations-admin';
import { TutorPresetAdmin } from './tutor-profiles';
import { TutorQuotaAdmin } from './tutor-quotas';
import { TutorHistory } from './tutor-history';
import { TextbookStructureAdmin } from './textbook-structure';
import { Heading, Picker, Empty } from './shared';

type Props = {
  data: State;
  view: string;
  refresh: () => Promise<void>;
  notify: (s: string) => void;
};
type AIAccount = {
  name: string;
  credentialAlias: string;
  priority: number;
  model: string;
  enabled: boolean;
  credentialConfigured: boolean;
  healthStatus: string;
  cooldownUntil?: string | null;
  lastErrorCode?: string | null;
  lastSuccessAt?: string | null;
  lastFailureAt?: string | null;
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
    [coverageTerm, setCoverageTerm] = useState('all'),
    [progression, setProgression] = useState<string[]>(['Grade 10|Term1']),
    [enrolled, setEnrolled] = useState<string[]>(['maths']);
  const [subject, setSubject] = useState('maths'),
    [kind, setKind] = useState('Textbook'),
    [textbookId, setTextbookId] = useState(''),
    [paperId, setPaperId] = useState('');
  const [edition, setEdition] = useState(''),
    [publicationYear, setPublicationYear] = useState(''),
    [examSession, setExamSession] = useState(''),
    [component, setComponent] = useState(''),
    [variant, setVariant] = useState(''),
    [publisher, setPublisher] = useState(''),
    [isbn, setIsbn] = useState(''),
    [sourceUrl, setSourceUrl] = useState('');
  const [docId, setDocId] = useState('');
  const [extraction, setExtraction] = useState<DocumentExtraction | null>(null);
  const [documentJob, setDocumentJob] = useState<DocumentJob | null>(null);
  const [extractionError, setExtractionError] = useState('');
  const [curriculumPlan, setCurriculumPlan] = useState<CurriculumPlan | null>(null);
  const [officialReview, setOfficialReview] = useState<OfficialMaterialReview | null>(null);
  const [paperMappings, setPaperMappings] = useState<PaperMappings | null>(null);
  const [mappingQuestionId, setMappingQuestionId] = useState('');
  const [mappingDraft, setMappingDraft] = useState<TopicMapping[]>([]);
  const [blueprintName, setBlueprintName] = useState('Term mock'),
    [blueprintMarks, setBlueprintMarks] = useState('20'),
    [blueprintMinutes, setBlueprintMinutes] = useState('30'),
    [blueprintQuestions, setBlueprintQuestions] = useState('4'),
    [blueprintSkills, setBlueprintSkills] = useState('knowledge, application');
  const parents = p.data.accounts.filter((a) => a.role === 'parent');
  const books = p.data.documents.filter(
    (d) => d.subject === subject && d.kind === 'Textbook',
  );
  const papers = p.data.documents.filter(
    (d) => d.subject === subject && d.kind === 'Past paper' && !d.legacy,
  );
  const doc = p.data.documents.find((d) => d.id === docId);
  const documentKinds = {
    Textbook: 'textbook',
    'Reference material': 'reference',
    'Past paper': 'past_paper',
    'Marking scheme': 'mark_scheme',
    'Examiner report': 'examiner_report',
  } as const;
  const processingDocuments = p.data.documents.some((document) =>
    ['queued', 'processing'].includes(document.status),
  );
  const currentView = p.view;
  const refreshPortal = p.refresh;
  useEffect(() => {
    if (currentView !== 'library' || !processingDocuments) return;
    const timer = window.setInterval(() => void refreshPortal(), 2000);
    return () => window.clearInterval(timer);
  }, [currentView, refreshPortal, processingDocuments]);
  useEffect(() => {
    if (currentView !== 'library' || !docId) return;
    const selected = p.data.documents.find((document) => document.id === docId);
    if (!selected) return;
    let active = true;
    const extractionRequest = ['needs_review', 'completed'].includes(selected.status)
      ? getDocumentExtraction(docId)
      : Promise.resolve(null);
    void Promise.all([getLatestDocumentJob(docId), extractionRequest])
      .then(([job, extracted]) => {
        if (active) {
          setDocumentJob(job);
          setExtraction(extracted);
          if (['Past paper', 'Marking scheme', 'Examiner report'].includes(selected.kind))
            void getOfficialMaterialReview(docId).then(setOfficialReview).catch(() => setOfficialReview(null));
          else setOfficialReview(null);
        }
      })
      .catch((cause) => {
        if (active) setExtractionError(errorMessage(cause));
      });
    return () => {
      active = false;
    };
  }, [currentView, docId, p.data.documents]);
  useEffect(() => {
    if (currentView !== 'coverage') return;
    let active = true;
    void getCurriculumPlan(subject)
      .then((plan) => {
        if (active) setCurriculumPlan(plan);
      })
      .catch((cause) => {
        if (active) {
          setCurriculumPlan(null);
          setError(errorMessage(cause));
        }
      });
    return () => { active = false; };
  }, [currentView, subject]);
  useEffect(() => {
    if (currentView !== 'questions' || !paperId) return;
    let active = true;
    void getPaperMappings(paperId).then((response) => {
      if (!active) return;
      setPaperMappings(response);
      const first = response.questions[0];
      setMappingQuestionId(first?.questionId || '');
      setMappingDraft(first?.mappings || []);
    }).catch((cause) => {
      if (active) { setPaperMappings(null); setError(errorMessage(cause)); }
    });
    return () => { active = false; };
  }, [currentView, paperId]);
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
  const subjectPicker = (
    <Picker
      label="Subject"
      value={subject}
      onChange={(v) => {
        setSubject(v);
        setTextbookId('');
        setPaperId('');
        setPaperMappings(null);
        setMappingQuestionId('');
        setMappingDraft([]);
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
            units: 'Textbook structure',
            coverage: 'Grade & term coverage',
            questions: 'Question mapping',
            blueprints: 'Mock paper blueprints',
            'ai-accounts': 'OpenAI account routing',
            'tutor-presets': 'Tutor presets',
            'tutor-quotas': 'Tutor allowances',
            'tutor-history': 'Tutor history and safety',
            'assessment-audit': 'Assessment audit',
            media: 'Visual media',
            evaluations: 'Evaluation & release gates',
            operations: 'Security & operations',
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
      <fieldset
        disabled={busy}
        style={{ border: 0, padding: 0, minWidth: 0 }}
      >
        {p.view === 'today' && (
          <>
            <div className="metric-grid">
              {[
                ['Parent accounts', parents.length],
                ['Students', p.data.students.length],
                ['Textbooks', p.data.documents.filter((document) => document.kind === 'Textbook').length],
                ['Official papers', p.data.officialPapers.length],
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
                  Upload a subject textbook and review its deterministic extraction.
                </li>
                <li>Choose the units covered in each grade and term.</li>
                <li>
                  Upload a past paper after that subject textbook, then its
                  marking scheme and examiner report.
                </li>
                <li>
                  Enter and map every question to one or more units. Review each
                  question, then approve the complete paper.
                </li>
              </ol>
              <p className="spaced">
                PDF and image extraction is connected and requires Admin review.
                Unit editing, curriculum coverage, question mapping and publication
                are implemented in later roadmap steps before term mocks are enabled.
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
              <h2>{editId ? `Edit ${name}` : 'Create an account'}</h2>
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
                      label: `${a.name} (@${a.username})`,
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
                    @{s.username} · Parent:{' '}
                    {parents.find((account) => account.id === s.parentId)
                      ?.name || 'Not available'}
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
                  {a.name} · @{a.username}
                </p>
              ))}
            </section>
          </>
        )}
        {p.view === 'ai-accounts' && <AIAccountsPanel notify={p.notify} />}
        {p.view === 'tutor-presets' && <TutorPresetAdmin notify={p.notify} />}
        {p.view === 'tutor-quotas' && <TutorQuotaAdmin notify={p.notify} />}
        {p.view === 'tutor-history' && <TutorHistory admin notify={p.notify} />}
        {p.view === 'assessment-audit' && <AssessmentAuditPanel notify={p.notify} />}
        {p.view === 'media' && <MediaAdmin data={p.data} notify={p.notify} />}
        {p.view === 'evaluations' && <EvaluationAdmin data={p.data} notify={p.notify} />}
        {p.view === 'operations' && <OperationsAdmin />}
        {p.view === 'blueprints' && (
          <>
            <form className="panel stack" onSubmit={(event) => {
              event.preventDefault();
              void run(() => api('assessments/admin/blueprints', {
                name: blueprintName, subjectId: subject,
                grade: Number(grade.replace('Grade ', '')), term: Number(term.replace('Term', '')),
                mode: 'mock', targetMarks: Number(blueprintMarks), durationMinutes: Number(blueprintMinutes),
                questionCount: Number(blueprintQuestions), skills: blueprintSkills.split(',').map((x) => x.trim()).filter(Boolean),
                difficultyProfile: { mixed: Number(blueprintQuestions) },
              }), 'Published mock blueprint created.');
            }}>
              {subjectPicker}
              {gradeTerm}
              <Field label="Blueprint name" value={blueprintName} onChange={setBlueprintName} />
              <div className="three-cols">
                <Field label="Target marks" type="number" value={blueprintMarks} onChange={setBlueprintMarks} />
                <Field label="Duration in minutes" type="number" value={blueprintMinutes} onChange={setBlueprintMinutes} />
                <Field label="Question count" type="number" value={blueprintQuestions} onChange={setBlueprintQuestions} />
              </div>
              <Field label="Skills, separated by commas" value={blueprintSkills} onChange={setBlueprintSkills} />
              <p className="source-note">AKURU reports a shortage if approved eligible questions cannot meet the exact marks and question count.</p>
              <Button className="primary" type="submit" disabled={busy}>Create and publish blueprint</Button>
            </form>
            <div className="learner-grid spaced">
              {p.data.assessmentBlueprints.map((blueprint) => (
                <section className="panel" key={blueprint.id}>
                  <h3>{blueprint.name}</h3>
                  <p>{p.data.subjects.find((item) => item.id === blueprint.subjectId)?.name} · Grade {blueprint.grade} · Term{blueprint.term}</p>
                  <p>{blueprint.questionCount} questions · {blueprint.targetMarks} marks · {blueprint.durationMinutes} minutes</p>
                </section>
              ))}
            </div>
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
                    label="Existing subject textbook"
                    value={textbookId}
                    onChange={setTextbookId}
                    options={books.map((b) => ({ value: b.id, label: b.name }))}
                  />
                  <p>A same-subject textbook must exist before a past paper can be uploaded. Unit approval is added in Step 6.</p>
                </>
              )}
              <Field label="Edition" value={edition} onChange={setEdition} />
              <Field label="Publication year" value={publicationYear} onChange={setPublicationYear} type="number" />
              <Field label="Exam session" value={examSession} onChange={setExamSession} />
              <Field label="Component" value={component} onChange={setComponent} />
              <Field label="Variant" value={variant} onChange={setVariant} />
              <Field label="Publisher" value={publisher} onChange={setPublisher} />
              <Field label="ISBN" value={isbn} onChange={setIsbn} />
              <Field label="Source URL" value={sourceUrl} onChange={setSourceUrl} type="url" />
              {['Marking scheme', 'Examiner report'].includes(kind) && (
                <Picker
                  label="Related past paper"
                  value={paperId}
                  onChange={setPaperId}
                  options={papers.map((b) => ({ value: b.id, label: b.name }))}
                />
              )}
              <label htmlFor="admin-document-file">
                Document file · PDF, PNG or JPEG, up to 50 MB
                <Input
                  id="admin-document-file"
                  type="file"
                  aria-label="Document file"
                  accept="application/pdf,image/png,image/jpeg"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f)
                      void run(
                        () =>
                          uploadLearningDocument(f, {
                            courseId: 'igcse',
                            subjectId: subject,
                            kind:
                              documentKinds[
                                kind as keyof typeof documentKinds
                              ],
                            title: f.name.replace(/\.[^.]+$/, ''),
                            edition: edition || undefined,
                            year: publicationYear || undefined,
                            session: examSession || undefined,
                            component: component || undefined,
                            variant: variant || undefined,
                            publisher: publisher || undefined,
                            isbn: isbn || undefined,
                            sourceUrl: sourceUrl || undefined,
                            sourceDocumentId: ['Marking scheme', 'Examiner report'].includes(kind)
                              ? paperId
                              : undefined,
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
              {p.data.documents.map((document) => (
                <div className="stack" key={`processing-${document.id}`}>
                  <div className="spread small">
                    <span>{document.name}</span>
                    <span>
                      {document.status} · {document.processingProgress ?? 0}%
                    </span>
                  </div>
                  {document.processingError && (
                    <p className="error" role="alert">
                      {document.processingError}
                    </p>
                  )}
                  <div className="button-row">
                    {document.status === 'failed' && (
                      <Button
                        variant="outline"
                        onClick={() => void run(() => retryDocument(document.id), 'Document processing queued again.')}
                      >
                        Retry processing
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      onClick={() => {
                        if (window.confirm(`Remove ${document.name} from AKURU?`))
                          void run(() => removeDocument(document.id), 'Document removed.');
                      }}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              ))}
              <Picker
                label="Document to review"
                value={docId}
                onChange={(v) => {
                  setDocId(v);
                  setExtraction(null);
                  setDocumentJob(null);
                  setExtractionError('');
                }}
                options={p.data.documents.map((d) => ({
                  value: d.id,
                  label: `${d.name} · ${d.subject} · ${d.kind} · ${d.status}`,
                }))}
              />
              {doc && (
                <>
                  <a
                    href={`/api/v1/documents/${doc.id}/content`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open original document
                  </a>
                  {documentJob && (
                    <div className="small panel">
                      <strong>Processing details</strong>
                      <p>
                        {documentJob.stage.replaceAll('_', ' ')} · {documentJob.status.replaceAll('_', ' ')} ·{' '}
                        {documentJob.progress}% · attempt {documentJob.attemptCount}
                      </p>
                      <p>Extractor: {documentJob.extractionVersion}</p>
                    </div>
                  )}
                  {doc.kind === 'Textbook' && (
                    <section className="panel stack">
                      <strong>Topic-based textbook workflow</strong>
                      <p>Create the textbook, its Unit or Module groups, and topics in Textbook structure. Attach each scanned PDF or image directly to its topic, review extraction quality, then publish that topic independently.</p>
                    </section>
                  )}
                  {['Past paper', 'Marking scheme', 'Examiner report'].includes(doc.kind) && ['needs_review', 'completed'].includes(doc.status) && (
                    <section className="panel stack">
                      <div className="spread">
                        <div>
                          <strong>Official material review</strong>
                          <p>Reconcile every question or linked entry against the rendered source before publication.</p>
                        </div>
                        <Button variant="outline" onClick={() => void run(async () => {
                          setOfficialReview(await proposeOfficialMaterialReview(doc.id));
                        }, 'Official material proposal created from extracted evidence.')}>Propose inventory</Button>
                      </div>
                      {officialReview && (
                        <>
                          <div className="two-cols">
                            <Field label="Expected complete item count" type="number" value={String(officialReview.expectedItemCount)} onChange={(value) => setOfficialReview({ ...officialReview, expectedItemCount: Number(value) })} />
                            <div className="check-label spaced"><Checkbox aria-label="Confirm the complete source inventory" checked={officialReview.completenessConfirmed} onCheckedChange={(yes) => setOfficialReview({ ...officialReview, completenessConfirmed: Boolean(yes) })} /><span>I checked the entire source and this inventory is complete</span></div>
                          </div>
                          {officialReview.questions.map((question, index) => (
                            <article className="panel stack" key={`${question.number}-${index}`}>
                              <div className="two-cols">
                                <Field label="Question / subpart number" value={question.number} onChange={(value) => setOfficialReview({ ...officialReview, questions: officialReview.questions.map((row, i) => i === index ? { ...row, number: value } : row) })} />
                                <Field label="Marks" type="number" value={String(question.marks)} onChange={(value) => setOfficialReview({ ...officialReview, questions: officialReview.questions.map((row, i) => i === index ? { ...row, marks: Number(value) } : row) })} />
                              </div>
                              <Field label="Shared stem" multiline value={question.sharedStem} onChange={(value) => setOfficialReview({ ...officialReview, questions: officialReview.questions.map((row, i) => i === index ? { ...row, sharedStem: value } : row) })} />
                              <Field label="Complete question prompt" multiline value={question.prompt} onChange={(value) => setOfficialReview({ ...officialReview, questions: officialReview.questions.map((row, i) => i === index ? { ...row, prompt: value } : row) })} />
                              <Field label="Equations · one per line" multiline value={question.equations.join('\n')} onChange={(value) => setOfficialReview({ ...officialReview, questions: officialReview.questions.map((row, i) => i === index ? { ...row, equations: value.split('\n').filter(Boolean) } : row) })} />
                              <p className="small">Source: {question.sourceLocations.map((source) => `page ${source.page}`).join(', ')} · {question.assetIds.length} retained asset(s)</p>
                            </article>
                          ))}
                          {officialReview.markSchemeEntries.map((entry, index) => (
                            <article className="panel stack" key={`${entry.questionNumber}-${index}`}>
                              <div className="two-cols">
                                <Field label="Question / subpart number" value={entry.questionNumber} onChange={(value) => setOfficialReview({ ...officialReview, markSchemeEntries: officialReview.markSchemeEntries.map((row, i) => i === index ? { ...row, questionNumber: value } : row) })} />
                                <Field label="Maximum marks" type="number" value={String(entry.maxMarks)} onChange={(value) => setOfficialReview({ ...officialReview, markSchemeEntries: officialReview.markSchemeEntries.map((row, i) => i === index ? { ...row, maxMarks: Number(value) } : row) })} />
                              </div>
                              <Field label="Marking points · one per line" multiline value={entry.markingPoints.map((point) => `${point.code}|${point.kind}|${point.text}`).join('\n')} onChange={(value) => setOfficialReview({ ...officialReview, markSchemeEntries: officialReview.markSchemeEntries.map((row, i) => i === index ? { ...row, markingPoints: value.split('\n').filter(Boolean).map((line, pointIndex) => { const [codeValue, kindValue, ...textValue] = line.split('|'); return { code: codeValue || `P${pointIndex + 1}`, kind: ['method', 'accuracy', 'independent', 'communication'].includes(kindValue) ? kindValue as 'method' | 'accuracy' | 'independent' | 'communication' : 'other', text: textValue.join('|') || kindValue || line }; }) } : row) })} />
                              <Field label="Accepted alternatives · one per line" multiline value={entry.alternatives.join('\n')} onChange={(value) => setOfficialReview({ ...officialReview, markSchemeEntries: officialReview.markSchemeEntries.map((row, i) => i === index ? { ...row, alternatives: value.split('\n').filter(Boolean) } : row) })} />
                              <p className="small">Source: {entry.sourceLocations.map((source) => `page ${source.page}`).join(', ')}</p>
                            </article>
                          ))}
                          {officialReview.examinerComments.map((comment, index) => (
                            <article className="panel stack" key={`${comment.questionNumber}-${index}`}>
                              <Field label="Question / subpart number" value={comment.questionNumber} onChange={(value) => setOfficialReview({ ...officialReview, examinerComments: officialReview.examinerComments.map((row, i) => i === index ? { ...row, questionNumber: value } : row) })} />
                              <Field label="Common mistakes · one per line" multiline value={comment.commonMistakes.join('\n')} onChange={(value) => setOfficialReview({ ...officialReview, examinerComments: officialReview.examinerComments.map((row, i) => i === index ? { ...row, commonMistakes: value.split('\n').filter(Boolean) } : row) })} />
                              <Field label="Examiner advice · one per line" multiline value={comment.advice.join('\n')} onChange={(value) => setOfficialReview({ ...officialReview, examinerComments: officialReview.examinerComments.map((row, i) => i === index ? { ...row, advice: value.split('\n').filter(Boolean) } : row) })} />
                              <p className="small">Source: {comment.sourceLocations.map((source) => `page ${source.page}`).join(', ')}</p>
                            </article>
                          ))}
                          <div className="button-row">
                            <Button variant="outline" onClick={() => void run(async () => { setOfficialReview(await saveOfficialMaterialReview(doc.id, officialReview)); }, 'Official material review saved.')}>Save review</Button>
                            <Button className="primary" disabled={officialReview.status === 'published' || !officialReview.completenessConfirmed} onClick={() => {
                              if (window.confirm(`Publish the attested ${officialReview.expectedItemCount}-item inventory for ${doc.name}?`)) void run(async () => { setOfficialReview(await publishOfficialMaterialReview(doc.id, officialReview.kind !== 'past_paper')); }, 'Official material published.');
                            }}>Publish official material</Button>
                          </div>
                        </>
                      )}
                    </section>
                  )}
                  {extractionError && <p className="error" role="alert">{extractionError}</p>}
                  {extraction?.pages.map((page) => (
                    <article className="panel stack" key={`page-${page.pageNumber}`}>
                      <div className="spread small">
                        <strong>Extracted page {page.pageNumber}</strong>
                        <span>
                          {page.method} · {Math.round(page.confidence * 100)}%
                          {page.needsReview ? ' · review required' : ''}
                        </span>
                      </div>
                      <div className="two-cols"><Field label="Printed page label" value={page.printedPageLabel || ''} onChange={(value) => setExtraction({ ...extraction, pages: extraction.pages.map((row) => row.id === page.id ? { ...row, printedPageLabel: value } : row) })}/><Button variant="outline" onClick={() => void run(async () => { setExtraction(await updateExtractionPage(doc.id, page.id, page.printedPageLabel || '')); }, 'Printed page label saved.')}>Save page label</Button></div>
                      <div className="extraction-review-grid"><div><strong className="small">Original page</strong><Image
                        src={`/api/v1/documents/${doc.id}/assets/${page.originalRenderAssetId || page.renderAssetId}/content`}
                        alt={`Rendered source page ${page.pageNumber}`}
                        width={Math.max(1, Math.round(page.widthPoints))}
                        height={Math.max(1, Math.round(page.heightPoints))}
                        unoptimized
                        loading="lazy"
                        style={{ maxWidth: '100%', maxHeight: '32rem', objectFit: 'contain' }}
                      /></div><div><strong className="small">Normalized review page</strong><Image
                        src={`/api/v1/documents/${doc.id}/assets/${page.renderAssetId}/content`}
                        alt={`Normalized review page ${page.pageNumber}`}
                        width={Math.max(1, Math.round(page.widthPoints))} height={Math.max(1, Math.round(page.heightPoints))}
                        unoptimized loading="lazy" style={{ maxWidth: '100%', maxHeight: '32rem', objectFit: 'contain' }}
                      /></div><div><strong className="small">Extracted content</strong>{page.blocks.map((block) => (
                        <div className="small stack" key={`${page.pageNumber}-${block.sequenceNumber}`}>
                          <strong>{block.kind}</strong> · {block.method} ·{' '}
                          {Math.round(block.confidence * 100)}%
                          {block.needsReview ? ' · review required' : ''}
                          <div className="two-cols"><Field label="Block type" value={block.kind} onChange={(value) => setExtraction({ ...extraction, pages: extraction.pages.map((row) => row.id === page.id ? { ...row, blocks: row.blocks.map((item) => item.id === block.id ? { ...item, kind: value } : item) } : row) })}/><Field label="Reading order" type="number" value={String(block.sequenceNumber)} onChange={(value) => setExtraction({ ...extraction, pages: extraction.pages.map((row) => row.id === page.id ? { ...row, blocks: row.blocks.map((item) => item.id === block.id ? { ...item, sequenceNumber: Number(value) } : item) } : row) })}/></div>
                          <Field label="Extracted text" multiline value={block.text} onChange={(value) => setExtraction({ ...extraction, pages: extraction.pages.map((row) => row.id === page.id ? { ...row, blocks: row.blocks.map((item) => item.id === block.id ? { ...item, text: value } : item) } : row) })}/>
                          <Field label="Equation or formula (LaTeX)" multiline value={block.latex || ''} onChange={(value) => setExtraction({ ...extraction, pages: extraction.pages.map((row) => row.id === page.id ? { ...row, blocks: row.blocks.map((item) => item.id === block.id ? { ...item, latex: value } : item) } : row) })}/>
                          {block.sourceAssetId && (
                            <Image
                              src={`/api/v1/documents/${doc.id}/assets/${block.sourceAssetId}/content`}
                              alt={`Source crop for ${block.kind} on page ${page.pageNumber}`}
                              width={320}
                              height={180}
                              unoptimized
                              loading="lazy"
                              style={{ maxWidth: '20rem', height: 'auto', objectFit: 'contain' }}
                            />
                          )}
                          <Button variant="outline" onClick={() => void run(async () => { setExtraction(await updateExtractionBlock(doc.id, block.id, { kind: block.kind, text: block.text, latex: block.latex, sequenceNumber: block.sequenceNumber })); }, 'Extracted block reviewed and saved.')}>Save reviewed block</Button>
                        </div>
                      ))}</div></div>
                    </article>
                  ))}
                  <p className="small">
                    Editing extracted blocks, saving review notes, and publishing documents are part of the Step 6 Admin approval workflow.
                  </p>
                </>
              )}
            </section>
          </>
        )}
        {p.view === 'units' && (
          <TextbookStructureAdmin subjects={p.data.subjects} notify={p.notify} refreshPortal={p.refresh} />
        )}
        {p.view === 'coverage' && (
          <section className="panel stack">
            {subjectPicker}
            {curriculumPlan ? (
              <>
                <div className="spread">
                  <div>
                    <h2>{curriculumPlan.textbookTitle}</h2>
                    <p>Edition {curriculumPlan.textbookEdition} · Plan {curriculumPlan.versionNumber || 'not saved'} · {curriculumPlan.status.replaceAll('_', ' ')}</p>
                  </div>
                </div>
                <p>Assign each published topic to the Grade and Term where it is first taught. Grade 10 Term1 and Term2 are combined for a student who has reached Term2, and coverage continues accumulating through later periods.</p>
                {curriculumPlan.status === 'published' && <Button variant="outline" onClick={() => void run(async () => {
                  setCurriculumPlan(await createCurriculumPlanDraft(subject));
                }, `Plan ${curriculumPlan.versionNumber + 1} draft created from the published plan.`)}>Add topics covered now</Button>}
                <div className="toolbar"><Picker label="Term to review" value={coverageTerm} onChange={setCoverageTerm} options={[{ value: 'all', label: 'All terms' }, ...[1, 2, 3].map((value) => ({ value: String(value), label: `Term ${value}` }))]} /><p className="small">Use this keyboard-friendly filter to focus on the term being planned. A student receives cumulative coverage from earlier terms.</p></div>
                {curriculumPlan.periods.filter((period) => coverageTerm === 'all' || String(period.term) === coverageTerm).map((period) => {
                  const index = curriculumPlan.periods.findIndex((row) => row.grade === period.grade && row.term === period.term);
                  const cumulativeIds = curriculumPlan.periods
                    .filter((row) => (row.grade < period.grade) || (row.grade === period.grade && row.term <= period.term))
                    .flatMap((row) => row.topicRefs || []);
                  const publishedIds = curriculumPlan.publishedPeriods.find((row) => row.grade === period.grade && row.term === period.term)?.topicRefs || [];
                  return (
                    <section className="panel stack" aria-labelledby={`coverage-${period.grade}-${period.term}`} key={`${period.grade}-${period.term}`}>
                      <h3 id={`coverage-${period.grade}-${period.term}`}>Grade {period.grade} · Term{period.term}</h3>
                      {curriculumPlan.groups.map((group) => <Checks key={group.groupRef}
                        label={`${curriculumPlan.groupLabel === 'module' ? 'Module' : 'Unit'} ${group.code} · ${group.title}`}
                        items={group.topics.map((topic) => ({ id: topic.topicRef, name: `${topic.code} · ${topic.title}${publishedIds.includes(topic.topicRef) ? ' · published' : ''}` }))}
                        selected={period.topicRefs || []}
                        change={(ids) => setCurriculumPlan({ ...curriculumPlan, periods: curriculumPlan.periods.map((row, i) => i === index
                          ? { ...row, topicRefs: [...(row.topicRefs || []).filter((ref) => !group.topics.some((topic) => topic.topicRef === ref)), ...ids] }
                          : { ...row, topicRefs: (row.topicRefs || []).filter((ref) => !ids.includes(ref)) }) })} />)}
                      <p className="small"><strong>Cumulative coverage preview:</strong>{' '}{curriculumPlan.groups.flatMap((group) => group.topics).filter((topic) => cumulativeIds.includes(topic.topicRef)).map((topic) => topic.code).join(', ') || 'No topics configured'}</p>
                    </section>
                  );
                })}
                {!!curriculumPlan.changes.length && <section className="callout stack"><strong>Changes from published plan {curriculumPlan.basedOnVersion}</strong>
                  {curriculumPlan.changes.map((change) => <span key={change.topicRef}>{change.code} · {change.change}{change.fromPeriod ? ` from ${change.fromPeriod}` : ''}{change.toPeriod ? ` to ${change.toPeriod}` : ''}</span>)}
                  {curriculumPlan.requiresPublishedChangeConfirmation && <p>Moving or removing published coverage can change future practice, mock papers and Tutor access. Existing assessments retain their original snapshot.</p>}
                </section>}
                <div className="button-row">
                  <Button variant="outline" onClick={() => void run(async () => {
                    setCurriculumPlan(await saveCurriculumPlan(subject, curriculumPlan.periods));
                  }, 'Curriculum plan draft saved.')}>Save draft</Button>
                  <Button className="primary" disabled={curriculumPlan.status !== 'draft'} onClick={() => {
                    if (window.confirm(`Publish curriculum plan ${curriculumPlan.versionNumber} for ${curriculumPlan.textbookTitle}? Existing assessments keep their current snapshot.`))
                      void run(async () => { setCurriculumPlan(await publishCurriculumPlan(subject, curriculumPlan.requiresPublishedChangeConfirmation)); }, 'Curriculum plan published.');
                  }}>Publish plan</Button>
                </div>
              </>
            ) : <p>Loading the published textbook and curriculum plan…</p>}
          </section>
        )}
        {p.view === 'questions' && (
          <section className="panel stack">
            {subjectPicker}
            <Picker label="Published past paper" value={paperId} onChange={(value) => {
              setPaperId(value); setPaperMappings(null); setMappingQuestionId(''); setMappingDraft([]);
            }} options={papers.map((item) => ({ value: item.id, label: item.name }))} />
            {paperMappings && (
              <>
                <p><strong>{paperMappings.paperTitle}</strong> · {paperMappings.textbookTitle}, {paperMappings.textbookEdition} · {paperMappings.confirmedQuestionCount}/{paperMappings.totalQuestionCount} questions confirmed</p>
                <div className="button-row">
                  {paperMappings.questions.map((question) => (
                    <Button key={question.questionId} variant={mappingQuestionId === question.questionId ? 'default' : 'outline'} onClick={() => {
                      setMappingQuestionId(question.questionId); setMappingDraft(question.mappings);
                    }}>Q{question.number} · {question.status}</Button>
                  ))}
                </div>
                {paperMappings.questions.filter((question) => question.questionId === mappingQuestionId).map((question) => (
                  <article className="panel stack" key={question.questionId}>
                    <h2>Question {question.number} · {question.marks} marks</h2>
                    {question.sharedStem && <p><strong>Shared evidence:</strong> {question.sharedStem}</p>}
                    <p>{question.prompt}</p>
                    <p className="small">Extracted evidence: {question.sourceLocations.map((source) => `page ${source.page}`).join(', ') || 'source page retained'}</p>
                    <p>Choose every related topic, assign weights totaling exactly 100%, and mark the topics that every student must have covered.</p>
                    {paperMappings.groups.map((group) => <fieldset className="panel stack" key={group.groupRef}><legend>{paperMappings.groupLabel === 'module' ? 'Module' : 'Unit'} {group.code} · {group.title}</legend>{group.topics.map((topic) => {
                      const mapped = mappingDraft.find((row) => row.topicRef === topic.topicRef);
                      return <div className="spread" key={topic.topicRef}><div className="check-label"><Checkbox aria-label={`Map ${topic.code}`} disabled={question.status === 'confirmed'} checked={Boolean(mapped)} onCheckedChange={(yes) => setMappingDraft(yes ? [...mappingDraft, { topicRef: topic.topicRef, weight: 0, required: true, rationale: '', method: 'admin' }] : mappingDraft.filter((row) => row.topicRef !== topic.topicRef))} /><span>{topic.code} · {topic.title}</span></div>{mapped && <div className="button-row"><label className="check-label" htmlFor={`required-${question.questionId}-${topic.topicRef}`}><Checkbox id={`required-${question.questionId}-${topic.topicRef}`} disabled={question.status === 'confirmed'} checked={mapped.required} onCheckedChange={(value) => setMappingDraft(mappingDraft.map((row) => row.topicRef === topic.topicRef ? { ...row, required: Boolean(value) } : row))} />Required</label><Input aria-label={`${topic.code} weight percentage`} disabled={question.status === 'confirmed'} type="number" min="1" max="100" value={mapped.weight} onChange={(event) => setMappingDraft(mappingDraft.map((row) => row.topicRef === topic.topicRef ? { ...row, weight: Number(event.target.value) } : row))} style={{ maxWidth: '7rem' }} /></div>}</div>;
                    })}</fieldset>)}
                    {!!Object.keys(question.groupWeights).length && <p className="small"><strong>Group summary:</strong> {Object.entries(question.groupWeights).map(([code, weight]) => `${code} ${weight}%`).join(' · ')}</p>}
                    <p className={mappingDraft.reduce((sum, row) => sum + row.weight, 0) === 100 ? 'small' : 'error'}>Total weight: {mappingDraft.reduce((sum, row) => sum + row.weight, 0)}%</p>
                    <div className="button-row">
                      <Button variant="outline" disabled={question.status === 'confirmed'} onClick={() => void run(async () => {
                        const response = await suggestQuestionMappings(question.questionId); setMappingDraft(response.suggestions);
                      }, 'Mapping suggestions prepared for Admin review.')}>Suggest mappings</Button>
                      <Button variant="outline" disabled={question.status === 'confirmed' || mappingDraft.reduce((sum, row) => sum + row.weight, 0) !== 100} onClick={() => void run(async () => {
                        const response = await saveQuestionMappings(question.questionId, mappingDraft);
                        setPaperMappings({ ...paperMappings, questions: paperMappings.questions.map((row) => row.questionId === response.questionId ? response : row) });
                      }, 'Mapping draft saved.')}>Save mapping</Button>
                      <Button className="primary" disabled={question.status !== 'draft'} onClick={() => {
                        if (window.confirm(`Confirm the topic mapping for question ${question.number}? It becomes immutable.`)) void run(async () => {
                          const response = await publishQuestionMappings(question.questionId);
                          setPaperMappings({ ...paperMappings, questions: paperMappings.questions.map((row) => row.questionId === response.questionId ? response : row) }); setMappingDraft(response.mappings);
                        }, 'Question mapping confirmed.');
                      }}>Confirm mapping</Button>
                    </div>
                  </article>
                ))}
              </>
            )}
          </section>
        )}
      </fieldset>
    </>
  );
}

function AssessmentAuditPanel({ notify }: { notify: (message: string) => void }) {
  const [results, setResults] = useState<AssessmentAudit[]>([]);
  const [loading, setLoading] = useState(true);
  const [requestKeys] = useState(() => new Map<string, string>());
  const [chosen, setChosen] = useState<AssessmentAudit | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function load() {
    setError(''); setLoading(true);
    try { setResults((await getAssessmentAudit()).results); }
    catch (cause) { setError(errorMessage(cause)); } finally { setLoading(false); }
  }
  useEffect(() => {
    let active = true;
    void getAssessmentAudit().then(data => { if (active) setResults(data.results); }).catch(cause => { if (active) setError(errorMessage(cause)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);
  async function reassess(row: AssessmentAudit) {
    setBusy(true); setError('');
    try { await reassessAssessment(row.assessmentId, requestKeys.get(row.resultId) || (() => { const key = crypto.randomUUID(); requestKeys.set(row.resultId, key); return key; })()); await load(); setChosen(null); notify('AKURU created a new, fully versioned assessment result.'); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  }
  return <>
    {error && <div className="error" role="alert">{error} <Button variant="outline" onClick={() => void load()}>Retry</Button></div>}
    <section className="panel stack">
      <div className="spread"><div><h2>AI-derived assessment results</h2><p>Inspect evidence, versions and confidence before asking AKURU to reassess.</p></div><Button variant="outline" onClick={() => void load()}>Refresh</Button></div>
      {results.map((row) => <button className="attempt-row" key={row.resultId} onClick={() => setChosen(row)}>
        <div><h3>{row.studentName} · {row.assessmentTitle} · Q{row.questionNumber}</h3><p>{row.subjectId} · result v{row.version} · {row.provider}/{row.model}</p></div>
        <span>{Math.round(row.confidence * 100)}% confidence</span><strong>{row.awardedMarks}/{row.maxMarks}</strong>
      </button>)}
      {loading && <output>Loading assessment audit…</output>}
      {!loading && !results.length && !error && <Empty title="No assessment results yet">Submitted, evaluated answers will appear here with their full audit trail.</Empty>}
    </section>
    <Dialog open={!!chosen} onOpenChange={(open) => !open && setChosen(null)}><DialogContent className="wide-dialog"><DialogHeader><DialogTitle>{chosen?.studentName} · Question {chosen?.questionNumber}</DialogTitle><DialogDescription>Result audit and provenance</DialogDescription></DialogHeader>
      {chosen && <div className="stack">{error && <div className="error" role="alert">{error} Retry the action below.</div>}<p>{chosen.questionPrompt}</p><h3>Submitted answer</h3><p className="preserve">{chosen.answer || 'No typed answer.'}</p>{chosen.workingUrl && <a href={chosen.workingUrl} target="_blank" rel="noreferrer">Open original submitted working</a>}<div className="source-note"><strong>{chosen.awardedMarks}/{chosen.maxMarks}</strong> · {Math.round(chosen.confidence * 100)}% confidence · {chosen.status.replaceAll('_', ' ')} · version {chosen.version}</div>
        {!!chosen.reviewReasons.length && <div className="error"><strong>Review required</strong><ul>{chosen.reviewReasons.map(x => <li key={x}>{x}</li>)}</ul></div>}
        <h3>Marking decisions and student evidence</h3>{chosen.markingDecisions.map(point => <article className="source-note" key={point.pointId}><div className="spread"><strong>{point.pointId} · {point.criterion}</strong><strong>{point.marksAwarded}/{point.maxMarks}</strong></div><p>Evidence: {point.studentEvidence}</p><p>{point.rationale} · {Math.round(point.confidence * 100)}% confidence</p></article>)}
        <h3>Versions and checks</h3><p className="small">Prompt {chosen.promptName} v{chosen.promptVersion} · engine {chosen.subjectEngine} v{chosen.subjectEngineVersion} · {chosen.provider}/{chosen.model}</p><pre className="source-note">{JSON.stringify(chosen.deterministicChecks, null, 2)}</pre>
        <h3>Source manifest</h3>{chosen.sourceManifest.map((source, index) => <pre className="source-note" key={index}>{JSON.stringify(source, null, 2)}</pre>)}
        <ResultReview key={chosen.resultId} resultId={chosen.resultId} decisions={chosen.markingDecisions} feedback={chosen.teachingExplanation} improvedAnswer={chosen.improvedAnswer} strengths={chosen.strengths} smallMistakes={chosen.smallMistakes} conceptualMistakes={chosen.conceptualMistakes} saved={async () => { await load(); setChosen(null); notify('Reviewed result published.'); }} />
        <p className="small">Reassessment evaluates every question in this assessment using OpenAI.</p>
        <Button className="primary" disabled={busy} onClick={() => void reassess(chosen)}>{busy ? 'Reassessing…' : 'Reassess and create new version'}</Button>
      </div>}
    </DialogContent></Dialog>
  </>;
}

function AIAccountsPanel({ notify }: { notify: (message: string) => void }) {
  const [accounts, setAccounts] = useState<AIAccount[]>([]);
  const [name, setName] = useState('');
  const [credentialAlias, setCredentialAlias] = useState('');
  const [priority, setPriority] = useState('0');
  const [model, setModel] = useState('');
  const [enabled, setEnabled] = useState(true);
  const [editingAlias, setEditingAlias] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    const result = (await api('admin/ai-accounts')) as AIAccount[];
    setAccounts(result);
  }
  useEffect(() => {
    let active = true;
    void api('admin/ai-accounts')
      .then((result) => {
        if (active) setAccounts(result as AIAccount[]);
      })
      .catch((cause) => {
        if (active) setError(errorMessage(cause));
      });
    return () => {
      active = false;
    };
  }, []);
  function edit(account: AIAccount) {
    setEditingAlias(account.credentialAlias);
    setName(account.name);
    setCredentialAlias(account.credentialAlias);
    setPriority(String(account.priority));
    setModel(account.model);
    setEnabled(account.enabled);
    setError('');
  }
  function clear() {
    setEditingAlias('');
    setName('');
    setCredentialAlias('');
    setPriority('0');
    setModel('');
    setEnabled(true);
  }
  return (
    <>
      {error && <div className="error" role="alert">{error}</div>}
      <section className="panel stack">
        <h2>{editingAlias ? `Edit ${name}` : 'Add an OpenAI account'}</h2>
        <p>
          Add the key to the backend dotenv JSON map first. AKURU stores only its alias.
          Priorities must be unique; the lowest number is selected first.
        </p>
        <form
          className="stack"
          onSubmit={(event) => {
            event.preventDefault();
            setBusy(true);
            setError('');
            void api(
              editingAlias ? `admin/ai-accounts/${editingAlias}` : 'admin/ai-accounts',
              { name, credentialAlias, priority: Number(priority), model, enabled },
            )
              .then(load)
              .then(() => {
                notify(editingAlias ? 'OpenAI account updated.' : 'OpenAI account added.');
                clear();
              })
              .catch((cause) => setError(errorMessage(cause)))
              .finally(() => setBusy(false));
          }}
        >
          <Field label="Account name" value={name} onChange={setName} />
          <Field
            label="Credential alias"
            value={credentialAlias}
            onChange={setCredentialAlias}
          />
          <Field label="Priority (0–100)" value={priority} onChange={setPriority} type="number" />
          <Field label="OpenAI model" value={model} onChange={setModel} />
          <label className="check-label" htmlFor="ai-account-enabled">
            <Checkbox id="ai-account-enabled" checked={enabled} onCheckedChange={(value) => setEnabled(Boolean(value))} />
            Enabled for new AI operations
          </label>
          <div className="button-row">
            <Button className="primary" type="submit" disabled={busy}>
              {editingAlias ? 'Save account' : 'Add account'}
            </Button>
            {editingAlias && <Button type="button" variant="outline" onClick={clear}>Cancel edit</Button>}
          </div>
        </form>
      </section>
      <div className="learner-grid spaced">
        {accounts.map((account) => (
          <section className="panel stack" key={account.credentialAlias}>
            <div className="spread">
              <h3>{account.name}</h3>
              <strong>Priority {account.priority}</strong>
            </div>
            <p>{account.credentialAlias} · {account.model}</p>
            <p>
              {account.enabled ? 'Enabled' : 'Disabled'} · {account.healthStatus.replaceAll('_', ' ')} ·{' '}
              {account.credentialConfigured ? 'Credential configured' : 'Credential missing'}
            </p>
            {account.lastErrorCode && <p>Last error: {account.lastErrorCode.replaceAll('_', ' ')}</p>}
            <Button variant="outline" onClick={() => edit(account)}>Edit configuration</Button>
          </section>
        ))}
      </div>
      {!accounts.length && (
        <Empty title="No OpenAI accounts configured">
          Add credential aliases to the backend dotenv, then create the first account here.
        </Empty>
      )}
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
