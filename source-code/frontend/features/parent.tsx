'use client';
/* React Compiler is not enabled here. Effects intentionally synchronise local form drafts and hash navigation. */
/* eslint-disable react/react-compiler */
import { useState } from 'react';
import { ArrowRight, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Table,
  TableHeader,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { api, errorMessage, type Attempt } from '@/lib/api';
import { Heading, Picker, Empty, Status, type FeatureProps } from './shared';
export function Reviews(p: FeatureProps) {
  const [filter, setFilter] = useState('pending'),
    [student, setStudent] = useState('all'),
    [review, setReview] = useState<Attempt | null>(null),
    [mark, setMark] = useState(''),
    [feedback, setFeedback] = useState(''),
    [busy, setBusy] = useState(false),
    [error, setError] = useState('');
  const attempts = p.data.attempts.filter(
    (a) =>
      (student === 'all' || a.studentId === student) &&
      (filter === 'all' || a.status === 'needs-review'),
  );
  const recommendationReviews = Object.values(p.data.recommendations || {}).flat().filter(
    (item) => item.reviewStatus === 'pending_review' && (student === 'all' || item.studentId === student),
  );
  async function reviewRecommendation(id: string, decision: 'approved' | 'rejected') {
    setBusy(true); setError('');
    try { await api(`recommendations/${id}/review`, { decision, reason: decision === 'approved' ? 'Reviewed by parent.' : 'Parent declined this recommendation.' }); await p.refresh(); }
    catch (e: unknown) { setError(errorMessage(e)); } finally { setBusy(false); }
  }
  async function save(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    try {
      await api('reviews', { id: review?.id, mark: Number(mark), feedback });
      await p.refresh();
      setReview(null);
      p.notify(
        'Individual feedback saved. The student can see it in My progress.',
      );
    } catch (e: unknown) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="FEEDBACK THAT HELPS THEM GROW"
        title="Make their next step clearer."
      >
        Review written responses and working, with a separate assessment for
        each child.
      </Heading>
      <div className="toolbar">
        <Picker
          label="Student"
          value={student}
          onChange={setStudent}
          options={[
            { value: 'all', label: 'All children' },
            ...p.data.students.map((s) => ({
              value: s.id,
              label: `${s.name} · ${s.grade}`,
            })),
          ]}
        />
        <Picker
          label="Show"
          value={filter}
          onChange={setFilter}
          options={[
            { value: 'pending', label: 'Awaiting review' },
            { value: 'all', label: 'All assessments' },
          ]}
        />
      </div>
      <section className="panel">
        {attempts.length ? (
          [...attempts].reverse().map((a) => (
            <button
              className="attempt-row"
              key={a.id}
              onClick={() => {
                setReview(a);
                setMark(a.mark === null ? '' : String(a.mark));
                setFeedback(a.status === 'reviewed' ? a.feedback : '');
                setError('');
              }}
            >
              <span className="avatar">
                {p.data.students.find((s) => s.id === a.studentId)?.name[0]}
              </span>
              <div>
                <h3>{a.title}</h3>
                <p>
                  {p.data.students.find((s) => s.id === a.studentId)?.name} ·{' '}
                  {p.data.subjects.find((s) => s.id === a.subject)?.name}
                </p>
              </div>
              <Status status={a.status} />
              <ChevronIcon />
            </button>
          ))
        ) : (
          <Empty title="Nothing waiting for review.">
            Written answers and uploaded working appear here after submission.
          </Empty>
        )}
      </section>
      <div className="section-heading"><h2>AKURU recommendation review</h2></div>
      <section className="panel">
        {recommendationReviews.map((item) => <div className="resource-row" key={item.id}>
          <div><h3>{item.title}</h3><p>{p.data.students.find((s) => s.id === item.studentId)?.name} · {item.unitCode} · {item.reason}</p><small>Evidence: {item.observedEvidence.join(' ')}</small></div>
          <Button variant="outline" disabled={busy} onClick={() => reviewRecommendation(item.id, 'rejected')}>Decline</Button>
          <Button className="primary" disabled={busy} onClick={() => reviewRecommendation(item.id, 'approved')}>Approve</Button>
        </div>)}
        {!recommendationReviews.length && <Empty title="No recommendations awaiting review.">Low-confidence and subjective suggestions appear here before students can see them.</Empty>}
      </section>
      <Dialog open={!!review} onOpenChange={(v) => !v && setReview(null)}>
        <DialogContent className="wide-dialog">
          <DialogHeader>
            <DialogTitle>{review?.title}</DialogTitle>
            <DialogDescription>
              {p.data.students.find((s) => s.id === review?.studentId)?.name} ·
              Individual assessment · {review?.maxMarks} available marks
            </DialogDescription>
          </DialogHeader>
          {review && (
            <form onSubmit={save}>
              <div className="review-answer">
                <h3>Submitted answer</h3>
                <p className="preserve">
                  {review.answer || 'No typed answer.'}
                </p>
                {review.fileId && (
                  <a
                    href={'/api/files/' + review.fileId}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open handwritten working ↗
                  </a>
                )}
              </div>
              <h3 className="spaced">Demo marking guidance</h3>
              <ol className="steps">
                {review.points.map((x, i) => (
                  <li key={x}>
                    <span>{i + 1}</span>
                    {x}
                  </li>
                ))}
              </ol>
              <label htmlFor="awarded-mark">
                Awarded marks (0–{review.maxMarks})
              </label>
              <Input
                id="awarded-mark"
                type="number"
                min="0"
                max={review.maxMarks}
                step="1"
                required
                value={mark}
                onChange={(e) => setMark(e.target.value)}
              />
              <label htmlFor="review-feedback" className="spaced">
                Feedback for this student
              </label>
              <Textarea
                id="review-feedback"
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                required
                placeholder="What went well? Which step should they revisit?"
              />
              <p className="source-note">
                Previous marks and feedback are retained in the review history.
              </p>
              {error && (
                <div className="error" role="alert">
                  {error}
                </div>
              )}
              <DialogFooter>
                <Button
                  variant="outline"
                  type="button"
                  onClick={() => setReview(null)}
                >
                  Cancel
                </Button>
                <Button type="submit" className="primary" disabled={busy}>
                  Save review
                  <Check size={16} />
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
function ChevronIcon() {
  return <ArrowRight size={16} />;
}

export function Assignments(p: FeatureProps) {
  const [student, setStudent] = useState(p.child.id),
    [question, setQuestion] = useState('m1'),
    [title, setTitle] = useState(''),
    [due, setDue] = useState(() =>
      new Date(Date.now() + 86400000).toISOString().slice(0, 10),
    ),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  const child = p.data.students.find((s) => s.id === student)!;
  const qs = p.data.questions.filter(
    (q) =>
      child.subjects.includes(q.subject) &&
      q.unitIds?.every((id) =>
        p.data.coverage.some(
          (c) =>
            c.subject === q.subject &&
            c.grade === child.grade &&
            c.term === child.term &&
            c.unitIds.includes(id),
        ),
      ),
  );
  const activeQuestion = qs.some((q) => q.id === question)
    ? question
    : qs[0]?.id || '';
  async function create(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api('assignments', {
        studentId: student,
        questionId: activeQuestion,
        title,
        due,
      });
      await p.refresh();
      setTitle('');
      p.notify('Activity assigned to ' + child.name + '.');
    } catch (e: unknown) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="A LITTLE DIRECTION, JUST FOR THEM"
        title="Plan their next discovery."
      >
        Assign a question to one child, with a clear due date.
      </Heading>
      <div className="library-layout">
        <form className="panel" onSubmit={create}>
          <h2>Assign practice</h2>
          <div className="two-cols spaced">
            <Picker
              label="Student"
              value={student}
              onChange={setStudent}
              options={p.data.students.map((s) => ({
                value: s.id,
                label: `${s.name} · ${s.grade}`,
              }))}
            />
            <div>
              <label htmlFor="assignment-due">Due date</label>
              <Input
                id="assignment-due"
                type="date"
                required
                value={due}
                onChange={(e) => setDue(e.target.value)}
              />
            </div>
          </div>
          <div className="spaced">
            <Picker
              label="Practice question"
              value={activeQuestion}
              onChange={setQuestion}
              options={qs.map((q) => ({
                value: q.id,
                label: `${p.data.subjects.find((s) => s.id === q.subject)?.name}: ${q.title}`,
              }))}
            />
          </div>
          <label htmlFor="assignment-title" className="spaced">
            Activity title (optional)
          </label>
          <Input
            id="assignment-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Use the question title"
          />
          {error && (
            <div className="error spaced" role="alert">
              {error}
            </div>
          )}
          <Button type="submit" className="primary spaced" disabled={busy}>
            Assign to {child.name}
            <ArrowRight size={16} />
          </Button>
        </form>
        <section className="import-note">
          <span className="big-avatar">{child.name[0]}</span>
          <h3>
            {child.name} · {child.grade}
          </h3>
          <p>
            This activity will appear only in {child.name}’s portal. It is
            marked complete when they submit an attempt for the assigned
            question.
          </p>
          <p className="small">
            The questions in this first version are demo activities, not a
            complete grade-specific curriculum.
          </p>
        </section>
      </div>
      <div className="section-heading">
        <h2>Family assignments</h2>
      </div>
      <section className="panel table-panel">
        {p.data.assignments.length ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Activity</TableHead>
                <TableHead>Student</TableHead>
                <TableHead>Due</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[...p.data.assignments].reverse().map((a) => (
                <TableRow key={a.id}>
                  <TableCell>
                    <strong>{a.title}</strong>
                  </TableCell>
                  <TableCell>
                    {p.data.students.find((s) => s.id === a.studentId)?.name}
                  </TableCell>
                  <TableCell>{a.due}</TableCell>
                  <TableCell>
                    <span
                      className={`status ${a.completed ? 'approved' : 'pending'}`}
                    >
                      {a.completed ? 'Completed' : 'To do'}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <Empty title="No assignments yet." />
        )}
      </section>
    </>
  );
}
