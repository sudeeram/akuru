'use client';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { DeterministicAnswerInput } from './deterministic-answer-input';
import type { PastPaperChatState } from '@/api/tutoring/tutor.types';
import { DrawingSubmissions } from './drawing-submissions';
import { ModelAnswerVisuals } from './answer-visuals';
import { Equation, LearningImage } from './learning-media';
import { TutorMessageContent } from './tutor-chat-elements';

export function TutorPastPaperCard({
  value,
  busy,
  refresh,
  submitAnswer,
}: {
  value: PastPaperChatState;
  busy: boolean;
  refresh: () => void;
  submitAnswer: (answer: string) => Promise<void>;
}) {
  const [answer, setAnswer] = useState('');
  const p = value.practice;
  const q = p.question;
  return (
    <section
      className="panel stack tutor-past-paper-card"
      aria-label="Past-paper practice question"
    >
      <div>
        <small>
          REVIEWED PAST-PAPER PRACTICE · {value.state.replaceAll('_', ' ')}
        </small>
        <h3>
          {value.paperTitle} · Q{value.questionLabel}
        </h3>
        <p>
          {q.marks} marks · {p.topicTitle}
        </p>
      </div>
      {q.sharedStem && (
        <TutorMessageContent content={q.sharedStem} formatted={false} />
      )}
      <TutorMessageContent content={q.prompt} formatted={false} />
      {q.equations.map((equation, i) => (
        <Equation key={i} value={equation} />
      ))}
      {p.assetUrls.map((src, i) => (
        <figure key={src} style={{ margin: 0, maxWidth: 560 }}>
          <LearningImage
            src={src}
            description={
              q.assetDescriptions?.[q.assetIds[i]] ||
              'Reviewed question diagram'
            }
          />
        </figure>
      ))}
      {value.state === 'awaiting_answer' && (
        <>
          <p>
            Type your response in the chat. Start with “My answer:” to submit
            it. Hints and answer reveals count as assisted practice.
          </p>
          {q.answerFormat && <form className="stack" onSubmit={async event => {
            event.preventDefault();
            if (!busy && answer.trim()) await submitAnswer(answer);
          }}>
            <DeterministicAnswerInput format={q.answerFormat} value={answer} onChange={setAnswer} disabled={busy} />
            <Button type="submit" disabled={busy || !answer.trim()}>Submit final answer</Button>
          </form>}
          <DrawingSubmissions
            assessmentId={p.assessmentId}
            questionId={q.id}
            parts={q.drawingParts}
            files={q.drawingFiles}
            disabled={busy}
            onSaved={async () => refresh()}
          />
        </>
      )}
      {(value.answerRevealed || value.state === 'answered') && (
        <>
          <details>
            <summary>Approved marking guidance</summary>
            <div className="stack">
              {value.markingGuidance.map((point, i) => (
                <p key={i}>{point.text}</p>
              ))}
              {value.alternatives.map((text, i) => (
                <p key={i}>{text}</p>
              ))}
            </div>
          </details>
          {!!value.examinerAdvice.length && (
            <details>
              <summary>Reviewed examiner guidance</summary>
              {value.examinerAdvice.map((text, i) => (
                <TutorMessageContent key={i} content={text} formatted={false} />
              ))}
            </details>
          )}
          <ModelAnswerVisuals
            assessmentId={p.assessmentId}
            questionId={q.id}
            visuals={q.rubric?.answerVisuals}
          />
        </>
      )}
      {!!value.sources.length && (
        <details>
          <summary>Exam source evidence ({value.sources.length})</summary>
          <div className="stack">
            {value.sources.map((source) => (
              <a
                key={source.url}
                href={source.url}
                target="_blank"
                rel="noreferrer"
              >
                {source.label}
              </a>
            ))}
          </div>
        </details>
      )}
      {value.answerRevealed && (
        <p className="muted">
          Answer revealed · assisted practice · no independent mastery credit.
        </p>
      )}
    </section>
  );
}
