'use client';
/* React Compiler is not enabled here. Effects intentionally synchronise local form drafts and hash navigation. */
/* eslint-disable react/react-compiler */
import { Equation, LearningImage } from './learning-media';
import { MediaGallery } from './media-gallery';
import { useEffect, useRef, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Clock3,
  Download,
  Lightbulb,
  MessageCircle,
  Upload,
  CalendarDays,
  Check,
  ChevronRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  api,
  errorMessage,
  uploadWorking,
  type Question,
  type Attempt,
  type Lesson,
  type AssessmentApiResponse,
} from '@/lib/api';
import {
  Heading,
  SubjectIcon,
  Picker,
  Empty,
  Status,
  Evidence,
  type FeatureProps,
} from './shared';
import { Diagram } from './diagram';

export function Subjects(p: FeatureProps) {
  const enrolled = p.data.subjects.filter((s) =>
    p.child.subjects.includes(s.id),
  );
  const active = enrolled.find((s) => s.id === p.subject) || enrolled[0];
  const [lesson, setLesson] = useState<Question | null>(null);
  const [explain, setExplain] = useState<Lesson | null>(null);
  const [error, setError] = useState('');
  async function open(q: Question) {
    setError('');
    try {
      const content = await api(`lesson?question=${q.id}`);
      setLesson(q);
      setExplain(content);
    } catch (e: unknown) {
      setError(errorMessage(e));
    }
  }
  return (
    <>
      <Heading
        eyebrow={`${p.child.grade} · MY SUBJECTS`}
        title="Follow your curiosity."
      >
        Build understanding, one topic at a time.
      </Heading>
      <div className="subject-tabs">
        {enrolled.map((s) => (
          <button
            key={s.id}
            onClick={() => {
              p.setSubject(s.id);
              setLesson(null);
            }}
            className={s.id === active.id ? 'selected' : ''}
          >
            <SubjectIcon subject={s} />
            {s.name}
          </button>
        ))}
      </div>
      <div className="course-strip">
        <div>
          <strong>{active.name}</strong>
          <span>
            {p.child.courses[active.id]?.level} · {p.child.grade}
          </span>
        </div>
        <span className="pill">Demo learning collection</span>
      </div>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      {lesson ? (
        <>
          <Button variant="ghost" onClick={() => setLesson(null)}>
            <ArrowLeft size={16} />
            Back to topics
          </Button>
          <div className="workspace-grid">
            <section className="panel">
              <div className="eyebrow">{lesson.topic}</div>
              <h2>{lesson.title}</h2>
              <Diagram kind={lesson.diagram} interactive />
              <p className="lesson-prompt">{lesson.prompt}</p>
            </section>
            <section className="panel">
              <span className="pill">
                <BookOpen size={14} /> Guided explanation
              </span>
              <h2 className="spaced">Let’s make sense of it.</h2>
              <p className="lesson-explanation">{explain?.explanation}</p>
              <h3 className="spaced">What to include</h3>
              <ol className="steps">
                {explain?.points.map((point: string, i: number) => (
                  <li key={point}>
                    <span>{i + 1}</span>
                    {point}
                  </li>
                ))}
              </ol>
              <div className="source-note">
                {lesson.source}
                <br />
                Curated demo explanation, not a live AI response.
              </div>
              <Button
                className="primary"
                onClick={() => p.go('practice', active.id)}
              >
                Try it yourself
                <ArrowRight size={16} />
              </Button>
            </section>
          </div>
        </>
      ) : (
        <div className="topic-list">
          {p.data.questions
            .filter((q) => q.subject === active.id)
            .map((q, i) => (
              <button
                className="panel topic-row"
                key={q.id}
                onClick={() => open(q)}
              >
                <span className="topic-number">0{i + 1}</span>
                <div>
                  <span className="eyebrow">{q.topic}</span>
                  <h3>{q.title}</h3>
                  <p>Visual explanation · Guided example · Practice</p>
                </div>
                <ArrowRight size={20} />
              </button>
            ))}
        </div>
      )}
      <div className="source-note">
        Questions are approved by your Admin and limited to units covered for
        your grade and term. If no questions appear, ask your Admin to complete
        textbook units, term coverage and paper review.
      </div>
      <section className="panel spaced">
        <h3>Approved family resources</h3>
        {p.data.documents.filter(
          (d) => d.subject === active.id && d.status === 'approved',
        ).length ? (
          p.data.documents
            .filter((d) => d.subject === active.id && d.status === 'approved')
            .map((d) => (
              <a
                className="resource-row"
                key={d.id}
                href={'/api/files/' + d.id}
                target="_blank"
                rel="noreferrer"
              >
                <BookOpen size={18} />
                {d.name}
                <ArrowRight size={15} />
              </a>
            ))
        ) : (
          <p className="muted small spaced">
            Your Admin can add approved textbooks and reference material to this
            subject.
          </p>
        )}
      </section>
      <MediaGallery studentId={p.child.id} subjectId={active.id} />
    </>
  );
}

export function Practice(p: FeatureProps) {
  const practice = p.data.exams.find((e) => e.status === 'active' && e.mode === 'practice');
  const qs = practice ? practice.questionIds.map((id) => p.data.questions.find((q) => q.id === id)!).filter(Boolean) : [];
  const [qid, setQid] = useState(() => {
    const next =
      typeof window !== 'undefined'
        ? sessionStorage.getItem('akuru-next-question')
        : null;
    if (next) sessionStorage.removeItem('akuru-next-question');
    return next || qs[0]?.id || '';
  });
  const q = qs.find((q) => q.id === qid) || qs[0];
  const [answer, setAnswer] = useState(''),
    [hints, setHints] = useState<string[]>([]),
    [file, setFile] = useState<{ id: string; name: string } | null>(null),
    [result, setResult] = useState<Attempt | null>(null),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [explanation, setExplanation] = useState<Lesson | null>(null),
    [tab, setTab] = useState('answer');
  const activeQuestionId = q?.id;
  const serverDraft = p.data.drafts?.[activeQuestionId] || '';
  const previousQuestion = useRef('');
  useEffect(() => {
    const key = p.child.id + ':' + activeQuestionId;
    if (previousQuestion.current === key) return;
    previousQuestion.current = key;
    setAnswer(serverDraft);
    setHints([]);
    setFile(null);
    setResult(null);
    setExplanation(null);
    setError('');
    setTab('answer');
  }, [activeQuestionId, p.child.id, serverDraft]);
  async function hint() {
    setBusy(true);
    try {
      if (!practice) return;
      const r = await api(`assessments/${practice.id}/questions/${q.id}/hint`, { idempotencyKey: crypto.randomUUID() }) as { hint: string; total: number };
      if (hints.length < r.total) setHints([...hints, r.hint]);
      else p.notify('You have opened all hints for this question.');
    } catch (e: unknown) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  async function submit(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (!practice) return;
      await api(`assessments/${practice.id}/answers`, {
        questionId: q.id,
        answer,
        fileId: file?.id,
        idempotencyKey: crypto.randomUUID(),
      });
      const completed = await api(`assessments/${practice.id}/submit`, { idempotencyKey: crypto.randomUUID() }) as AssessmentApiResponse;
      const assessed = await api(`assessments/${practice.id}/evaluate`, { idempotencyKey: crypto.randomUUID() }) as AssessmentApiResponse;
      const frozen = assessed.questions[0];
      const feedback = frozen.result;
      setResult({ id: completed.id, studentId: p.child.id, subject: completed.subjectId,
        questionId: q.id, title: q.title, answer, fileId: file?.id || '', hints: hints.length,
        mark: feedback?.status === 'published' ? feedback.awardedMarks : null, maxMarks: q.marks,
        status: feedback?.status === 'needs_review' ? 'needs-review' : 'assessed',
        feedback: [...(feedback?.strengths || []), ...(feedback?.smallMistakes || []), ...(feedback?.conceptualMistakes || [])].join(' ') || 'AKURU completed the assessment.',
        explanation: feedback?.teachingExplanation || '',
        points: feedback?.markingDecisions.map((point) => `${point.awarded ? 'Awarded' : 'Missed'}: ${point.rationale} Evidence: ${point.studentEvidence}`) || [],
        improvedAnswer: feedback?.improvedAnswer,
        recommendations: feedback?.recommendations,
        createdAt: completed.submittedAt || new Date().toISOString() });
      await p.refresh();
    } catch (e: unknown) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  if (!q)
    return (
      <Empty title="No questions available for this term">
        <Button className="primary spaced" onClick={async () => {
          setBusy(true); setError('');
          try { await api('assessments/start', { mode: 'practice', subjectId: p.subject }); await p.refresh(); }
          catch (e: unknown) { setError(errorMessage(e)); } finally { setBusy(false); }
        }} disabled={busy}>Start eligible practice</Button>
        {error || 'AKURU selects from all mapped units covered up to your current term.'}
      </Empty>
    );
  const active = p.data.exams.find((e) => e.status === 'active' && e.mode !== 'practice');
  if (active)
    return (
      <>
        <Heading title="Your mock exam is in progress." />
        <div className="panel">
          <p>Practice and hints resume after you submit your exam.</p>
          <Button
            className="primary spaced"
            onClick={() => p.go('exams', active.subject)}
          >
            Resume exam
            <ArrowRight size={16} />
          </Button>
        </div>
      </>
    );
  return (
    <>
      <Heading
        eyebrow="A SAFE SPACE TO TRY"
        title="A little practice goes a long way."
      >
        Show your thinking. Use a hint when you need one.
      </Heading>
      <div className="toolbar">
        <Picker
          label="Subject"
          value={p.subject}
          onChange={p.setSubject}
          options={p.data.subjects
            .filter((s) => p.child.subjects.includes(s.id))
            .map((s) => ({ value: s.id, label: s.name }))}
        />
        <Picker
          label="Question"
          value={q.id}
          onChange={setQid}
          options={qs.map((q) => ({ value: q.id, label: q.title }))}
        />
        <span className="pill">
          {p.child.courses[p.subject]?.level} · {p.child.grade}
        </span>
      </div>
      <div className="workspace-grid">
        <section className="panel question-panel">
          <div className="spread">
            <span className="eyebrow">{q.topic}</span>
            <span className="pill">{q.marks} marks</span>
          </div>
          <h2>{q.title}</h2>
          <p className="question-text">{q.prompt}</p>
          {!!q.equations?.length && <div className="equations" aria-label="Equations supplied with this question">{q.equations.map((equation) => <Equation key={equation} value={equation} />)}</div>}
          <Diagram kind={q.diagram} />
          {q.assetIds?.map((assetId) => (
            <LearningImage key={assetId} src={`/api/v1/assessments/${q.assessmentId}/assets/${assetId}`} description={`Source diagram for ${q.title}: ${q.prompt}`} />
          ))}
          <div className="source-note">
            <BookOpen size={14} />
            {q.source}
          </div>
        </section>
        <section className="panel answer-panel">
          <Tabs value={tab} onValueChange={setTab}>
            <TabsList>
              <TabsTrigger value="answer">Your answer</TabsTrigger>
              <TabsTrigger value="tutor">Guided tutor</TabsTrigger>
            </TabsList>
            <TabsContent value="answer">
              <form onSubmit={submit}>
                <label className="spaced" htmlFor="answer">
                  {q.type === 'numeric'
                    ? 'Your answer and working'
                    : 'Explain your thinking'}
                </label>
                <Textarea
                  id="answer"
                  value={answer}
                  placeholder={
                    q.type === 'numeric'
                      ? `Enter your answer${q.unit ? ' in ' + q.unit : ''}. Add working if you like.`
                      : 'Write your response here…'
                  }
                  onChange={(e) => {
                    setAnswer(e.target.value);
                  }}
                  disabled={!!result}
                />
                <div className="answer-tools">
                  <label className="upload-button">
                    <Upload size={16} />
                    {file ? file.name : 'Upload handwritten working'}
                    <input
                      type="file"
                      accept="image/png,image/jpeg,application/pdf"
                      disabled={busy || !!result}
                      onChange={async (e) => {
                        const f = e.target.files?.[0];
                        if (!f) return;
                        setBusy(true);
                        try {
                          if (!practice) return;
                          const uploaded = await uploadWorking(f, practice.id, q.id);
                          setFile(uploaded);
                          p.notify(uploaded.needsReview ? 'Working uploaded. AKURU will keep it for review.' : 'Working uploaded and read by AKURU.');
                        } catch (e: unknown) {
                          setError(errorMessage(e));
                        } finally {
                          setBusy(false);
                        }
                      }}
                    />
                  </label>
                  <span className="muted small">Image or PDF · up to 5 MB</span>
                </div>
                {!result && (
                  <div className="button-row">
                    <Button
                      variant="ghost"
                      type="button"
                      disabled={busy}
                      onClick={async () => {
                        try {
                          if (!practice) return;
                          await api(`assessments/${practice.id}/answers`, { questionId: q.id, answer, fileId: file?.id, idempotencyKey: crypto.randomUUID() });
                          await p.refresh();
                          p.notify('Draft saved privately to your account.');
                        } catch (e: unknown) {
                          setError(errorMessage(e));
                        }
                      }}
                    >
                      Save draft
                    </Button>
                    <Button
                      variant="outline"
                      type="button"
                      onClick={hint}
                      disabled={busy}
                    >
                      <Lightbulb size={16} />
                      Give me a hint
                    </Button>
                    <Button
                      type="submit"
                      className="primary"
                      disabled={busy || (!answer.trim() && !file)}
                    >
                      {busy ? 'Saving…' : 'Check my answer'}
                      <ArrowRight size={16} />
                    </Button>
                  </div>
                )}
              </form>
              {hints.map((h, i) => (
                <div className="hint" key={i}>
                  <Lightbulb size={18} />
                  <div>
                    <strong>Hint {i + 1}</strong>
                    <p>{h}</p>
                  </div>
                </div>
              ))}
              {result && (
                <div className="feedback">
                  <div className="spread">
                    <h3>
                      {result.mark === null
                        ? 'Your work is saved.'
                        : 'You’ve got it.'}
                    </h3>
                    <Status status={result.status} />
                  </div>
                  <p className="spaced">{result.feedback}</p>
                  {result.mark !== null && (
                    <strong className="score">
                      {result.mark} / {result.maxMarks} marks
                    </strong>
                  )}
                  <h3 className="spaced">Worked explanation</h3>
                  <p className="spaced">{result.explanation}</p>
                  {result.improvedAnswer && <><h3 className="spaced">An exam-ready answer</h3><p className="preserve">{result.improvedAnswer}</p></>}
                  <ol className="steps">
                    {result.points.map((x, i) => (
                      <li key={x}>
                        <span>{i + 1}</span>
                        {x}
                      </li>
                    ))}
                  </ol>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setResult(null);
                      setAnswer('');
                      setHints([]);
                      setFile(null);
                    }}
                  >
                    Try again
                  </Button>
                </div>
              )}
            </TabsContent>
            <TabsContent value="tutor">
              <div className="tutor-heading">
                <span className="subject-icon blue">
                  <MessageCircle />
                </span>
                <div>
                  <h3>Let’s work through it.</h3>
                  <p>Curated guidance for this example</p>
                </div>
              </div>
              <p>
                Try a hint first, or open the worked explanation to study the
                method.
              </p>
              <div className="button-row spaced">
                <Button variant="outline" onClick={hint} disabled={busy}>
                  <Lightbulb size={15} />
                  Show a hint
                </Button>
                <Button
                  variant="outline"
                  onClick={async () => {
                    try {
                      setExplanation(await api(`lesson?question=${q.id}`));
                    } catch (e: unknown) {
                      setError(errorMessage(e));
                    }
                  }}
                >
                  Explain the method
                </Button>
              </div>
              {hints.map((h, i) => (
                <div key={i} className="hint">
                  {h}
                </div>
              ))}
              {explanation && (
                <div className="feedback">
                  <p>{explanation.explanation}</p>
                  <Diagram kind={q.diagram} interactive />
                </div>
              )}
              <p className="source-note">
                Open-ended AI chat will connect to the future tutor backend.
                These examples do not send your work to any external service.
              </p>
            </TabsContent>
          </Tabs>
          {error && (
            <div className="error spaced" role="alert">
              {error}
            </div>
          )}
          <p className="source-note">
            Written responses and handwritten working need parent review.
            Numeric final-answer checks do not assess every method step.
          </p>
        </section>
      </div>
    </>
  );
}

export function Exams(p: FeatureProps) {
  const [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [confirm, setConfirm] = useState(false),
    [time, setTime] = useState(() => Date.now()),
    [index, setIndex] = useState(0),
    [draft, setDraft] = useState(''),
    [dirty, setDirty] = useState(false);
  const exam = p.data.exams.find((e) => e.status === 'active' && e.mode !== 'practice');
  const qs = exam
    ? exam.questionIds.map((id) => p.data.questions.find((q) => q.id === id)!)
    : [];
  const q = qs[index] || qs[0];
  useEffect(() => {
    const t = setInterval(() => setTime(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const savedAnswer = exam?.answers[q?.id] || '';
  useEffect(() => {
    setDraft(savedAnswer);
    setDirty(false);
  }, [exam?.id, q?.id, savedAnswer]);
  const remaining = exam
    ? Math.max(0, Math.ceil((Date.parse(exam.endsAt) - time) / 1000))
    : 0;
  useEffect(() => {
    if (!exam || !q || !dirty || !remaining) return;
    const timer = window.setTimeout(async () => {
      try {
        await api(`assessments/${exam.id}/answers`, {
          questionId: q.id, answer: draft, idempotencyKey: crypto.randomUUID(),
        });
        setDirty(false);
        await p.refresh();
      } catch (cause: unknown) {
        setError(errorMessage(cause));
      }
    }, 1200);
    return () => window.clearTimeout(timer);
  }, [dirty, draft, exam, q, remaining, p]);
  async function save() {
    if (!exam) return;
    setBusy(true);
    try {
      await api(`assessments/${exam.id}/answers`, { questionId: q.id, answer: draft, idempotencyKey: crypto.randomUUID() });
      setDirty(false);
      await p.refresh();
      p.notify('Answer saved.');
    } catch (e: unknown) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  async function finish() {
    if (!exam) return;
    setBusy(true);
    setError('');
    try {
      if (dirty && remaining > 0)
        await api(`assessments/${exam.id}/answers`, {
          questionId: q.id,
          answer: draft,
          idempotencyKey: crypto.randomUUID(),
        });
      const storageKey = `akuru-submit-${exam.id}`;
      const idempotencyKey = sessionStorage.getItem(storageKey) || crypto.randomUUID();
      sessionStorage.setItem(storageKey, idempotencyKey);
      await api(`assessments/${exam.id}/submit`, { idempotencyKey });
      await api(`assessments/${exam.id}/evaluate`, { idempotencyKey: crypto.randomUUID() });
      sessionStorage.removeItem(storageKey);
      setConfirm(false);
      setIndex(0);
      setDirty(false);
      await p.refresh();
      p.notify('Exam submitted and assessed. Your feedback is in My progress.');
    } catch (e: unknown) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="MAKE ROOM FOR FOCUSED THINKING"
        title={
          exam ? 'Your quiet space to focus.' : 'Practise the exam experience.'
        }
      >
        {exam
          ? 'Work at your own pace within the time. Hints are off.'
          : 'Original demo papers with a timer, saved answers and a review afterwards.'}
      </Heading>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      {exam ? (
        <>
          <div className="exam-bar">
            <span>
              <Clock3 size={18} />
              {remaining
                ? `${Math.floor(remaining / 60)}:${String(remaining % 60).padStart(2, '0')} remaining`
                : 'Time is up — submit your saved work'}
            </span>
            <span>
              Question {index + 1} of {qs.length}
            </span>
            <Button
              className="primary"
              onClick={() => setConfirm(true)}
              disabled={busy}
            >
              Submit exam
            </Button>
          </div>
          <div className="workspace-grid">
            <section className="panel">
              <div className="spread">
                <h2>{q.title}</h2>
                <span className="pill">{q.marks} marks</span>
              </div>
              <p className="question-text">{q.prompt}</p>
              {!!q.equations?.length && <div className="equations" aria-label="Equations supplied with this question">{q.equations.map((equation) => <Equation key={equation} value={equation} />)}</div>}
              <Diagram kind={q.diagram} />
              {q.assetIds?.map((assetId) => (
                <LearningImage key={assetId} src={`/api/v1/assessments/${exam.id}/assets/${assetId}`} description={`Source diagram for ${q.title}: ${q.prompt}`} />
              ))}
            </section>
            <section className="panel">
              <label htmlFor="exam-answer">Your answer and working</label>
              <Textarea
                id="exam-answer"
                value={draft}
                disabled={!remaining || busy}
                onChange={(e) => {
                  setDraft(e.target.value);
                  setDirty(true);
                }}
              />
              <p className="source-note">
                {dirty
                  ? 'Unsaved changes — save before moving to another question.'
                  : 'Saved answers are restored if you reopen the portal.'}
              </p>
              <Button
                variant="outline"
                disabled={!remaining || busy || !dirty}
                onClick={save}
              >
                Save answer
              </Button>
              <label className="upload-button spaced">
                <Upload size={16} />
                Upload working
                <input
                  type="file"
                  accept="image/png,image/jpeg,application/pdf"
                  disabled={!remaining || busy}
                  onChange={async (e) => {
                    const f = e.target.files?.[0];
                    if (!f) return;
                    setBusy(true);
                    try {
                      const uploaded = await uploadWorking(f, exam.id, q.id);
                      await api(`assessments/${exam.id}/answers`, {
                        questionId: q.id,
                        answer: draft,
                        fileId: uploaded.id,
                        idempotencyKey: crypto.randomUUID(),
                      });
                      setDirty(false);
                      await p.refresh();
                      p.notify('Working attached to this question.');
                    } catch (e: unknown) {
                      setError(errorMessage(e));
                    } finally {
                      setBusy(false);
                    }
                  }}
                />
              </label>
              {exam.files?.[q.id] && (
                <p className="small spaced">Working attached ✓</p>
              )}
              <div className="button-row spaced">
                <Button
                  variant="outline"
                  disabled={index === 0 || dirty || busy}
                  onClick={() => setIndex(index - 1)}
                >
                  <ArrowLeft size={15} />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  disabled={index === qs.length - 1 || dirty || busy}
                  onClick={() => setIndex(index + 1)}
                >
                  Next
                  <ArrowRight size={15} />
                </Button>
              </div>
            </section>
          </div>
        </>
      ) : (
        <>
          <div className="toolbar">
            <Picker
              label="Subject"
              value={p.subject}
              onChange={(v) => {
                p.setSubject(v);
                setIndex(0);
              }}
              options={p.data.subjects
                .filter((s) => p.child.subjects.includes(s.id))
                .map((s) => ({ value: s.id, label: s.name }))}
            />
          </div>
          <section className="panel exam-intro">
            <span className="subject-icon blue">
              <Clock3 />
            </span>
            <div>
              <span className="eyebrow">ORIGINAL PRACTICE PAPER</span>
              <h2>
                {p.data.subjects.find((s) => s.id === p.subject)?.name} · Mini
                mock
              </h2>
              <p>
                {p.data.assessmentBlueprints.find((b) => b.subjectId === p.subject)?.questionCount || 'Configured'} questions ·{' '}
                {p.data.assessmentBlueprints.find((b) => b.subjectId === p.subject)?.targetMarks || 'configured'} marks
              </p>
              <p className="small spaced">
                Choose a quiet spot. You can upload working or type answers.
                Your timer continues if you leave this page.
              </p>
            </div>
            <div className="stack">
              <Button
                className="primary"
                disabled={busy || !p.data.assessmentBlueprints.some((b) => b.subjectId === p.subject)}
                onClick={async () => {
                  setBusy(true);
                  try {
                    await api('assessments/start', { mode: 'mock', subjectId: p.subject });
                    setIndex(0);
                    await p.refresh();
                  } catch (e: unknown) {
                    setError(errorMessage(e));
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Start mock exam
                <ArrowRight size={16} />
              </Button>
              {p.data.officialPapers.filter((paper) => paper.subjectId === p.subject).map((paper) => (
                <Button key={paper.id} variant="outline" disabled={busy} onClick={async () => {
                  setBusy(true); setError('');
                  try { await api('assessments/start', { mode: 'official_paper', subjectId: p.subject, paperId: paper.id }); setIndex(0); await p.refresh(); }
                  catch (e: unknown) { setError(errorMessage(e)); } finally { setBusy(false); }
                }}>Take {paper.title}</Button>
              ))}
              <Button variant="outline" onClick={() => window.print()}>
                <Download size={16} />
                Print practice paper
              </Button>
            </div>
          </section>
          <div className="print-paper">
            <h1>
              AKURU — {p.data.subjects.find((s) => s.id === p.subject)?.name}
            </h1>
            <p>
              Original demo practice paper · 15 minutes · Name:
              __________________
            </p>
            {qs.map((q, i) => (
              <section key={q.id}>
                <h3>
                  {i + 1}. {q.title} ({q.marks} marks)
                </h3>
                <p>{q.prompt}</p>
                {!!q.equations?.length && <div className="equations" aria-label="Equations supplied with this question">{q.equations.map((equation) => <Equation key={equation} value={equation} />)}</div>}
                <Diagram kind={q.diagram} />
                <div className="writing-lines" />
              </section>
            ))}
          </div>
          <div className="section-heading">
            <h2>Previous mock exams</h2>
          </div>
          {p.data.exams.filter((e) => ['submitted', 'expired'].includes(e.status) && e.mode !== 'practice').length ? (
            <div className="panel">
              {p.data.exams
                .filter((e) => ['submitted', 'expired'].includes(e.status) && e.mode !== 'practice')
                .map((e) => (
                  <button
                    className="resource-row"
                    key={e.id}
                    onClick={() => p.go('progress', e.subject)}
                  >
                    <ClipboardIcon />
                    <span>
                      {p.data.subjects.find((s) => s.id === e.subject)?.name}
                      <small>
                        {new Date(e.startedAt).toLocaleDateString()}
                      </small>
                    </span>
                    <Status status={e.status} />
                    <ChevronRight size={16} />
                  </button>
                ))}
            </div>
          ) : (
            <div className="panel">
              <Empty title="Your first mock starts here.">
                Completed papers and feedback will appear here.
              </Empty>
            </div>
          )}
        </>
      )}
      <Dialog open={confirm} onOpenChange={setConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ready to submit?</DialogTitle>
            <DialogDescription>
              {remaining
                ? 'Your current answer will be saved and the paper will be submitted.'
                : 'Only answers saved before the timer ended will be included.'}{' '}
              You can review feedback afterwards.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirm(false)}>
              Keep working
            </Button>
            <Button className="primary" onClick={finish} disabled={busy}>
              {busy ? 'Submitting…' : 'Submit paper'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
function ClipboardIcon() {
  return <BookOpen size={18} />;
}

export function ProgressView(p: FeatureProps) {
  const [chosen, setChosen] = useState<Attempt | null>(null);
  const own = p.data.attempts.filter((a) => a.studentId === p.child.id);
  const unitMastery = p.data.mastery?.[p.child.id] || [];
  const masteryGroups = p.data.masteryGroups?.[p.child.id] || [];
  const nextSteps = (p.data.recommendations?.[p.child.id] || []).filter((item) => item.reviewStatus === 'approved');
  return (
    <>
      <Heading
        eyebrow="PROGRESS IS PERSONAL"
        title={`${p.child.name}’s learning journey.`}
      >
        A view of the work, feedback and understanding built over time.
      </Heading>
      {p.data.user.role === 'parent' && (
        <div className="toolbar">
          <Picker
            label="Student"
            value={p.child.id}
            onChange={p.setSelected}
            options={p.data.students.map((s) => ({
              value: s.id,
              label: `${s.name} · ${s.grade}`,
            }))}
          />
        </div>
      )}
      <div className="metric-grid">
        {[
          ['Questions attempted', own.length],
          ['Assessed attempts', own.filter((a) => a.mark !== null).length],
          [
            'Awaiting review',
            own.filter((a) => a.status === 'needs-review').length,
          ],
          ['Hints used', own.reduce((n, a) => n + a.hints, 0)],
        ].map(([label, value]) => (
          <div className="panel metric" key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <div className="section-heading">
        <h2>Subject by subject</h2>
      </div>
      <div className="subject-grid">
        {p.data.subjects
          .filter((s) => p.child.subjects.includes(s.id))
          .map((s) => (
            <div className="panel" key={s.id}>
              <div className="subject-progress-heading">
                <SubjectIcon subject={s} />
                <div>
                  <h3>{s.name}</h3>
                  <p className="small">{p.child.courses[s.id]?.level}</p>
                </div>
              </div>
              <Evidence attempts={own.filter((a) => a.subject === s.id)} />
              <div className="stack spaced">
                {masteryGroups.filter((group) => group.subjectId === s.id).map((group) => <details className="source-note" key={`${group.subjectId}:${group.groupCode}`}><summary><strong>{group.groupLabel} {group.groupCode} · {group.groupTitle}</strong> · {group.score.toFixed(1)}/10</summary><p className="small">{group.explanation}</p>{group.topics.map((topic) => <div className="source-note" key={topic.topicRef}><div className="spread"><strong>Topic {topic.topicCode} · {topic.topicTitle}</strong><strong>{topic.score.toFixed(1)}/10</strong></div><p className="small">{topic.confidence} confidence · {topic.evidenceCount} assessed evidence item{topic.evidenceCount === 1 ? '' : 's'}</p></div>)}</details>)}
                {unitMastery.filter((unit) => unit.subjectId === s.id).map((unit) => (
                  <div className="source-note" key={unit.unitId}>
                        <div className="spread"><strong>{unit.unitCode} · {unit.unitTitle}</strong><strong>{unit.score.toFixed(1)}/10</strong></div>
                      <div className="spread small"><span>{unit.provisional ? 'Provisional' : unit.confidence} · {unit.confidence} confidence</span><span>{unit.trend > 0 ? '↑' : unit.trend < 0 ? '↓' : '→'} {Math.abs(unit.trend).toFixed(1)} recent trend</span></div>
                    <p className="small">{unit.evidenceCount} assessed evidence item{unit.evidenceCount === 1 ? '' : 's'}</p>
                    <div className="mastery-dimensions" aria-label={`${unit.unitTitle} skill dimensions`}>
                      {unit.dimensions.map((dimension) => <div key={dimension.dimension}><div className="spread small"><span>{dimension.dimension.replaceAll('_', ' ')}</span><span>{dimension.score.toFixed(1)}/10</span></div><progress max="10" value={dimension.score}>{dimension.score} out of 10</progress></div>)}
                    </div>
                    {!!unit.recentEvents.length && <details><summary>Latest 10 score changes</summary><ol>{unit.recentEvents.map(event => <li key={event.id}>{new Date(event.createdAt).toLocaleDateString()}: {event.previousScore == null ? 'Started' : `${event.previousScore.toFixed(1)} →`} {event.newScore.toFixed(1)}/10. {event.explanation}</li>)}</ol></details>}
                    {(p.data.recommendations?.[p.child.id] || []).filter(item => item.unitId === unit.unitId && item.reviewStatus !== 'rejected').filter((item, index, items) => items.findIndex(other => other.diagnosisId === item.diagnosisId) === index).map(item => <div className="small" key={item.id}><strong>Mistake pattern:</strong> {item.category.replaceAll('_', ' ')} ({item.occurrenceCount} observation{item.occurrenceCount === 1 ? '' : 's'})<ul>{item.observedEvidence.map(evidence => <li key={evidence}>{evidence}</li>)}</ul></div>)}
                  </div>
                ))}
                {!unitMastery.some((unit) => unit.subjectId === s.id) && <p className="muted small">Complete assessed work to build unit mastery.</p>}
              </div>
            </div>
          ))}
      </div>
          <p className="source-note">
            Unit scores use assessed evidence and are not predicted exam grades. Provisional scores need more varied evidence; pending reviews are excluded.
          </p>
          <div className="section-heading"><h2>AKURU next steps</h2></div>
          <div className="subject-grid">
            {nextSteps.map((item) => <article className="panel" key={item.id}>
              <span className="eyebrow">{item.unitCode} · {item.category.replaceAll('_', ' ')}</span>
              <h3>{item.title}</h3><p>{item.reason}</p>
              <p className="small spaced"><strong>Try this:</strong> {item.action}</p>
              <p className="small"><strong>Success:</strong> {item.successCondition}</p>
              <a href={item.sourceUrl} target="_blank" rel="noreferrer">{item.sourceTitle} · page {item.sourcePage} ↗</a>
            </article>)}
            {!nextSteps.length && <div className="panel"><Empty title="No approved next steps yet.">AKURU will add source-linked activities when assessed work shows a specific improvement area.</Empty></div>}
          </div>
      <div className="section-heading">
        <h2>Recent work & feedback</h2>
      </div>
      <div className="panel">
        {own.length ? (
          [...own].reverse().map((a) => (
            <button
              className="attempt-row"
              key={a.id}
              onClick={() => setChosen(a)}
            >
              <div>
                <h3>{a.title}</h3>
                <p>
                  {p.data.subjects.find((s) => s.id === a.subject)?.name} ·{' '}
                  {new Date(a.createdAt).toLocaleDateString()}{' '}
                  {a.examId ? '· Mock exam' : ''}
                </p>
              </div>
              <Status status={a.status} />
              <strong>
                {a.mark === null ? '—' : `${a.mark}/${a.maxMarks}`}
              </strong>
              <ChevronRight size={16} />
            </button>
          ))
        ) : (
          <Empty title="Every journey begins with a question.">
            Complete a practice activity to start your learning record.
          </Empty>
        )}
      </div>
      <Dialog open={!!chosen} onOpenChange={(v) => !v && setChosen(null)}>
        <DialogContent className="review-dialog">
          <DialogHeader>
            <DialogTitle>{chosen?.title}</DialogTitle>
            <DialogDescription>
              Saved answer and individual feedback
            </DialogDescription>
          </DialogHeader>
          {chosen && (
            <>
              <Status status={chosen.status} />
              <div className="source-note"><strong>{chosen.mark === null ? 'Awaiting human review' : `${chosen.mark}/${chosen.maxMarks} marks`}</strong>{chosen.confidence != null && <> · {Math.round(chosen.confidence * 100)}% confidence · result version {chosen.resultVersion}</>}</div>
              {!!chosen.reviewReasons?.length && <output className="error">This result needs review: {chosen.reviewReasons.join(' ')}</output>}
              <h3>Your answer</h3>
              <p className="preserve">
                {chosen.answer || 'Working uploaded without typed text.'}
              </p>
              {chosen.fileId && (
                <a
                  target="_blank"
                  rel="noreferrer"
                  href={chosen.workingUrl}
                >
                  Open submitted working ↗
                </a>
              )}
              <h3>Feedback</h3>
              <p>{chosen.feedback}</p>
              {!!chosen.strengths?.length && <><h3>What you did well</h3><ul>{chosen.strengths.map(item => <li key={item}>{item}</li>)}</ul></>}
              {!!chosen.smallMistakes?.length && <><h3>Small mistakes to fix</h3><ul>{chosen.smallMistakes.map(item => <li key={item}>{item}</li>)}</ul></>}
              {!!chosen.conceptualMistakes?.length && <><h3>Ideas to revisit</h3><ul>{chosen.conceptualMistakes.map(item => <li key={item}>{item}</li>)}</ul></>}
              <h3>Worked explanation</h3>
              <p>{chosen.explanation}</p>
              {chosen.improvedAnswer && <><h3>An exam-ready answer</h3><p className="preserve">{chosen.improvedAnswer}</p></>}
              <h3>How each mark was decided</h3>
              {(chosen.markingDecisions || []).map(point => <article className="source-note" key={point.pointId}><div className="spread"><strong>{point.pointId} · {point.criterion}</strong><strong>{point.marksAwarded}/{point.maxMarks}</strong></div><p><strong>Evidence in your answer:</strong> {point.studentEvidence}</p><p>{point.rationale}</p></article>)}
              {!!chosen.recommendations?.length && <><h3>What to do next</h3><ul>{chosen.recommendations.map((item) => <li key={item}>{item}</li>)}</ul></>}
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

export function Plan(p: FeatureProps) {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const plan = p.data.plans[p.child.id];
  const assignments = p.data.assignments.filter(
    (a) => a.studentId === p.child.id,
  );
  return (
    <>
      <Heading
        eyebrow="A LITTLE STRUCTURE. ROOM TO GROW."
        title="Your next small steps."
        action={
          <Button
            className="primary"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await api('plans', { studentId: p.child.id });
                await p.refresh();
                p.notify('Your study plan is ready.');
              } catch (e: unknown) {
                setError(errorMessage(e));
              } finally {
                setBusy(false);
              }
            }}
          >
                {busy ? 'Preparing…' : plan?.items.length ? 'Refresh my plan' : 'Create my plan'}
            <ArrowRight size={16} />
          </Button>
        }
      >
        Short sessions shaped by your own practice history.
      </Heading>
      {error && <div className="error">{error}</div>}
      <div className="two-cols">
        <section className="panel">
          <h2>Suggested revision</h2>
              {plan?.items.length ? (
            <>
              <p className="source-note">
                Updated {new Date(plan.updatedAt).toLocaleDateString()} ·
                Rule-based local suggestions
              </p>
              {plan.items.map((item) => (
                <div className="plan-item" key={item.subject}>
                  <span className="mini-icon">
                    <BookOpen size={17} />
                  </span>
                  <div>
                    <h3>{item.topic}</h3>
                        <p>{item.reason}</p>
                    <span className="small muted">
                      {p.data.subjects.find((s) => s.id === item.subject)?.name}{' '}
                          · {item.minutes} min
                        </span>
                        <p className="small spaced"><strong>Source:</strong> <a href={item.sourceUrl} target="_blank" rel="noreferrer">{item.source} ↗</a></p>
                        <p className="small"><strong>Success:</strong> {item.successCondition}</p>
                        <p className="small">Scheduled {new Date(item.scheduledFor).toLocaleDateString()}</p>
                        <button
                          className="text-button spaced"
                          onClick={async () => {
                            if (item.status === 'completed') return p.go('practice', item.subject);
                            try { await api(`plans/items/${item.id}/complete`, {}); await p.refresh(); p.notify('Study activity completed.'); }
                            catch (e: unknown) { setError(errorMessage(e)); }
                          }}
                        >
                          {item.status === 'completed' ? 'Practise again' : 'Mark complete'}
                      <ArrowRight size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </>
          ) : (
            <Empty title="Make a little time for learning.">
              Create a starting plan, then refresh it as you practise.
            </Empty>
          )}
        </section>
        <section className="panel">
          <h2>Assigned by your parent</h2>
          {assignments.length ? (
            assignments.map((a) => (
              <div key={a.id} className="plan-item">
                <span className="mini-icon">
                  {a.completed ? (
                    <Check size={17} />
                  ) : (
                    <CalendarDays size={17} />
                  )}
                </span>
                <div>
                  <h3>{a.title}</h3>
                  <p>
                    Due {a.due} · {a.completed ? 'Completed' : 'Ready to start'}
                  </p>
                  <button
                    className="text-button spaced"
                    onClick={() => {
                      sessionStorage.setItem(
                        'akuru-next-question',
                        a.questionId,
                      );
                      p.go('practice', a.subject);
                    }}
                  >
                    {a.completed ? 'Practise again' : 'Open activity'}
                    <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            ))
          ) : (
            <Empty title="No assignments right now.">
              Choose a suggested activity or explore a subject.
            </Empty>
          )}
        </section>
      </div>
    </>
  );
}
