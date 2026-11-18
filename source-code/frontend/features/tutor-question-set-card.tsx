'use client';
import { useState } from 'react';
import type { TutorQuestionSet } from '@/api/tutoring/tutor.types';
import { Button } from '@/components/ui/button';
import { LearningImage } from './learning-media';
import { TutorMessageContent } from './tutor-chat-elements';

export function TutorQuestionSetCard({value, busy, send}: {
  value: TutorQuestionSet; busy: boolean; send: (text: string) => Promise<void>;
}) {
  const [draft, setDraft] = useState('');
  const q = value.question;
  const f = value.feedback;
  const waiting = value.itemStatus === 'awaiting_answer';
  return <section className="panel stack" aria-label="Topic practice set">
    <header>
      <small>{value.sourceKind === 'generated' ? 'AKURU-GENERATED EXAM-STYLE PRACTICE' : 'ORIGINAL PAST-PAPER PRACTICE'}</small>
      <h3>{value.topicTitles.join(' · ')}</h3>
      <p>Question {Math.min(value.position, value.availableCount)} of {value.availableCount} · {value.completedCount} completed · {value.status}</p>
      <progress aria-label="Practice set progress" value={value.completedCount} max={value.availableCount} style={{width: '100%'}} />
      {value.message && <output>{value.message}</output>}
    </header>
    {value.status === 'active' && q && <>
      <p><strong>{q.sourceLabel} · {q.label}</strong> · {q.marks} marks</p>
      {q.sharedStem && <TutorMessageContent content={q.sharedStem} formatted={false} />}
      <TutorMessageContent content={q.prompt} formatted={false} />
      {q.assets?.map(asset => <figure key={asset.url} style={{margin: 0, maxWidth: 560}}>
        <LearningImage src={asset.url} description={asset.alt} />
      </figure>)}
      {value.answer !== null && <details><summary>Your saved response</summary><p style={{whiteSpace: 'pre-wrap'}}>{value.answer}</p></details>}
      {waiting && <form className="stack" onSubmit={async event => {
        event.preventDefault();
        if (draft.trim() && !busy) { await send(`My answer: ${draft.trim()}`); setDraft(''); }
      }}>
        <label htmlFor="practice-set-answer">Your answer</label>
        <textarea id="practice-set-answer" rows={4} maxLength={7500} value={draft} disabled={busy || value.processing}
          onChange={event => setDraft(event.target.value)} />
        <Button type="submit" disabled={busy || value.processing || !draft.trim()}>Submit for feedback</Button>
      </form>}
      {f && <div className="stack" aria-live="polite">
        <h4>{f.score === null ? 'Guidance without a score' : `Indicative AI score: ${f.score}/${f.maximum}`}</h4>
        <p>Learning feedback, not a certified exam result.</p>
        {([['Correct points', f.correctPoints], ['Mistakes', f.mistakes], ['Missing points', f.omissions]] as const).map(([label, items]) => items.length > 0 && <div key={label}>
          <strong>{label}</strong><ul>{items.map((item, index) => <li key={index}>{item}</li>)}</ul>
        </div>)}
        <div className="panel"><h4>AKURU suggested better answer</h4><TutorMessageContent content={f.improvedAnswer} /></div>
        <details><summary>Why this answer is better</summary><TutorMessageContent content={f.explanation} /></details>
        {f.uncertainty && <p><strong>Uncertainty:</strong> {f.uncertainty}</p>}
      </div>}
      {q.markingGuidance && <details><summary>{value.sourceKind === 'generated' ? 'Generated suggested marking guidance' : 'Approved marking guidance'}</summary>
        {q.suggestedAnswer && <TutorMessageContent content={q.suggestedAnswer} />}
        <ul>{q.markingGuidance.map(point => <li key={point.code}>{point.text}</li>)}</ul>
        {q.answerAssets?.map(asset => <figure key={asset.url} style={{margin: 0, maxWidth: 560}}>
          <LearningImage src={asset.url} description={asset.alt} />
          <figcaption>{asset.origin === 'ai_generated' ? 'AI-generated worked answer · reviewed' : 'Approved mark-scheme answer visual'}{asset.caption ? ` · ${asset.caption}` : ''}</figcaption>
        </figure>)}
        {q.alternatives?.map((text, i) => <p key={i}>{text}</p>)}
        {q.examinerAdvice && q.examinerAdvice.length > 0 && <details><summary>Reviewed examiner guidance</summary>{q.examinerAdvice.map((text, i) => <p key={i}>{text}</p>)}</details>}
      </details>}
    </>}
    {value.status === 'active' && <div className="row" style={{flexWrap: 'wrap'}}>
      {!q && <Button disabled={busy} onClick={() => void send('Retry generation')}>Retry generation</Button>}
      {value.itemStatus === 'feedback_unavailable' && <Button disabled={busy} onClick={() => void send('Retry feedback')}>Retry feedback</Button>}
      {waiting && <>
        <Button disabled={busy} variant="outline" onClick={() => void send('Give me a hint')}>Hint</Button>
        <Button disabled={busy} variant="outline" onClick={() => void send('Show answer')}>Show answer</Button>
        <Button disabled={busy} variant="outline" onClick={() => void send('Skip question')}>Skip</Button>
      </>}
      {['feedback', 'revealed', 'skipped'].includes(value.itemStatus) && <Button disabled={busy} onClick={() => { setDraft(''); void send('Next question'); }}>
        {value.position >= value.availableCount ? 'Complete set' : 'Next question'}
      </Button>}
      <Button disabled={busy} variant="outline" onClick={() => {
        if (window.confirm('Stop this set? Your saved answers and feedback will remain in your history.')) void send('Stop practice');
      }}>Stop set</Button>
    </div>}
    {value.status !== 'active' && <div><p>
      Indicative total for unassisted scored answers: {value.summary.indicativeMarks || 0}/{value.summary.maximumMarks || 0}.
      {' '}{value.summary.assistedOrSkipped || 0} assisted or skipped. These results are not certified mastery measurements.
    </p>
      {!!value.summary.strengths?.length && <div><h4>Strengths from this set</h4><ul>{value.summary.strengths.map((text, i) => <li key={i}>{text}</li>)}</ul></div>}
      {!!value.summary.revisionSuggestions?.length && <div><h4>What to revise next</h4><p>Revisit {value.topicTitles.join(' and ')} with these points in mind:</p><ul>{value.summary.revisionSuggestions.map((text, i) => <li key={i}>{text}</li>)}</ul></div>}
    </div>}
  </section>;
}
