'use client';
import { useId, useState } from 'react';
import { api, errorMessage, type Attempt } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';

type Props = { resultId: string; decisions: NonNullable<Attempt['markingDecisions']>; feedback: string; improvedAnswer: string; strengths: string[]; smallMistakes: string[]; conceptualMistakes: string[]; saved: () => Promise<void> };
export function ResultReview(props: Props) {
  const id = useId();
  const [decisions, setDecisions] = useState(props.decisions);
  const [feedback, setFeedback] = useState(props.feedback);
  const [answer, setAnswer] = useState(props.improvedAnswer);
  const [strengths, setStrengths] = useState(props.strengths.join('\n'));
  const [small, setSmall] = useState(props.smallMistakes.join('\n'));
  const [conceptual, setConceptual] = useState(props.conceptualMistakes.join('\n'));
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [requestKey, setRequestKey] = useState(() => crypto.randomUUID());
  const lines = (value: string) => value.split('\n').map(x => x.trim()).filter(Boolean);
  return <form className="stack" onChange={() => setRequestKey(crypto.randomUUID())} onSubmit={async event => {
    event.preventDefault(); setBusy(true); setError('');
    try { await api(`assessments/results/${props.resultId}/review`, { idempotencyKey: requestKey, markingDecisions: decisions, feedback, improvedAnswer: answer, strengths: lines(strengths), smallMistakes: lines(small), conceptualMistakes: lines(conceptual), reason }); await props.saved(); }
    catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); }
  }}>
    <h3>Review and publish a corrected result</h3>
    <fieldset disabled={busy} className="stack" style={{border:0,padding:0}}>
    {decisions.map((point,index) => <section className="source-note stack" key={point.pointId}>
      <strong>{point.pointId} · {point.criterion}</strong>
      <label>Marks (0–{point.maxMarks})<Input type="number" required min={0} max={point.maxMarks} value={point.marksAwarded} onChange={e => setDecisions(decisions.map((p,i) => i === index ? {...p, marksAwarded:Number(e.target.value), awarded:Number(e.target.value)>0} : p))} /></label>
      <label htmlFor={`${id}-evidence-${index}`}>Student evidence<Textarea id={`${id}-evidence-${index}`} required maxLength={2000} value={point.studentEvidence} onChange={e => setDecisions(decisions.map((p,i) => i === index ? {...p, studentEvidence:e.target.value} : p))} /></label>
      <label htmlFor={`${id}-rationale-${index}`}>Reason for this mark<Textarea id={`${id}-rationale-${index}`} required maxLength={2000} value={point.rationale} onChange={e => setDecisions(decisions.map((p,i) => i === index ? {...p, rationale:e.target.value} : p))} /></label>
    </section>)}
    <label htmlFor={`${id}-feedback`}>Teaching explanation<Textarea id={`${id}-feedback`} required maxLength={30000} value={feedback} onChange={e => setFeedback(e.target.value)} /></label>
    <label htmlFor={`${id}-answer`}>Improved answer<Textarea id={`${id}-answer`} required maxLength={20000} value={answer} onChange={e => setAnswer(e.target.value)} /></label>
    <label htmlFor={`${id}-strengths`}>Strengths, one per line<Textarea id={`${id}-strengths`} value={strengths} onChange={e => setStrengths(e.target.value)} /></label>
    <label htmlFor={`${id}-small`}>Small mistakes, one per line<Textarea id={`${id}-small`} value={small} onChange={e => setSmall(e.target.value)} /></label>
    <label htmlFor={`${id}-conceptual`}>Conceptual mistakes, one per line<Textarea id={`${id}-conceptual`} value={conceptual} onChange={e => setConceptual(e.target.value)} /></label>
    <label htmlFor={`${id}-reason`}>Reason for review<Textarea id={`${id}-reason`} required maxLength={2000} value={reason} onChange={e => setReason(e.target.value)} /></label>
    </fieldset>
    <p className="small">The original result is retained. Publishing creates a new version and updates unit mastery.</p>
    {error && <div className="error" role="alert">{error} Submit again to retry.</div>}
    <Button type="submit" disabled={busy || !decisions.length}>{busy ? 'Publishing review…' : 'Publish reviewed result'}</Button>
  </form>;
}
