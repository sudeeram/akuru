'use client';
/* React Compiler is not enabled here. Effects intentionally synchronise local form drafts and hash navigation. */
/* eslint-disable react/react-compiler */
import { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ResultReview } from './result-review';
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
} from '@/components/ui/dialog';
import { api, errorMessage, type Attempt } from '@/lib/api';
import { Heading, Picker, Empty, Status, type FeatureProps } from './shared';
import { TutorSignals } from './tutor-signals';
export function Reviews(p: FeatureProps) {
  const [filter, setFilter] = useState('pending'),
    [student, setStudent] = useState('all'),
    [review, setReview] = useState<Attempt | null>(null),
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
      <div className="section-heading"><h2>Child-by-child learning summary</h2></div>
      <div className="learner-grid">
        {p.data.students.filter(child => student === 'all' || child.id === student).map(child => {
          const topics = p.data.mastery?.[child.id] || [];
          const groups = p.data.masteryGroups?.[child.id] || [];
          const pending = (p.data.recommendations?.[child.id] || []).filter(item => item.reviewStatus === 'pending_review').length;
          const average = topics.length ? topics.reduce((total, topic) => total + topic.score, 0) / topics.length : null;
          return <section className="panel stack" key={child.id}><div className="spread"><h3>{child.name}</h3><strong>{average == null ? 'More evidence needed' : `${average.toFixed(1)}/10 average`}</strong></div>
            <p>{child.grade} · {child.term} · {topics.length} measured topic{topics.length === 1 ? '' : 's'} · {pending} review task{pending === 1 ? '' : 's'}</p>
            {topics.map(topic => <div className="source-note" key={topic.topicRef}><div className="spread"><span>{topic.groupCode} · {topic.topicCode} · {topic.topicTitle}</span><strong>{topic.score.toFixed(1)}/10</strong></div><p className="small">{topic.trend > 0 ? 'Improving' : topic.trend < 0 ? 'Declining' : 'Steady'} ({topic.trend > 0 ? '+' : ''}{topic.trend.toFixed(1)}) · {topic.confidence} confidence</p><details><summary>Latest 10 score changes</summary><ol>{topic.recentEvents.map(event => <li key={event.id}>{new Date(event.createdAt).toLocaleDateString()}: {event.newScore.toFixed(1)}/10 — {event.explanation}</li>)}</ol></details></div>)}
            {groups.map(group => <details className="source-note" key={`${group.subjectId}:${group.groupCode}`}><summary>{group.groupLabel} {group.groupCode} · {group.groupTitle} · {group.score.toFixed(1)}/10</summary><p className="small">{group.explanation}</p>{group.topics.filter(topic => topic.score < 7).map(topic => <p className="small" key={topic.topicRef}><strong>Action:</strong> Topic {topic.topicCode} · {topic.topicTitle} needs focused practice ({topic.score.toFixed(1)}/10).</p>)}</details>)}
            {!topics.length && <p className="source-note">Insufficient evidence: this child needs assessed work before AKURU can calculate a topic trend.</p>}
            <TutorSignals studentId={child.id} />
          </section>;
        })}
      </div>
      {error && <div className="error" role="alert">{error} Retry the review action.</div>}
      <section className="panel">
        {attempts.length ? (
          [...attempts].reverse().map((a) => (
            <button
              className="attempt-row"
              key={a.id}
              onClick={() => {
                setReview(a);
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
          <div><h3>{item.title}</h3><p>{p.data.students.find((s) => s.id === item.studentId)?.name} · {item.groupCode} · {item.topicCode} · {item.reason}</p><small>Evidence: {item.observedEvidence.join(' ')}</small></div>
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
            <div className="stack">
              <div className="review-answer">
                <h3>Submitted answer</h3>
                <p className="preserve">
                  {review.answer || 'No typed answer.'}
                </p>
                {review.fileId && (
                  <a
                    href={review.workingUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open handwritten working ↗
                  </a>
                )}
              </div>
              <ResultReview key={review.id} resultId={review.id} decisions={review.markingDecisions || []} feedback={review.explanation} improvedAnswer={review.improvedAnswer || ''} strengths={review.strengths || []} smallMistakes={review.smallMistakes || []} conceptualMistakes={review.conceptualMistakes || []} saved={async () => { await p.refresh(); setReview(null); p.notify('Reviewed result published.'); }} />
            </div>
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
  const qs = p.data.questions.filter((q) => child.subjects.includes(q.subject));
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
