'use client';
import { useState } from 'react';
import { request } from '@/api/core/client';
import { Button } from '@/components/ui/button';
import type { AnswerVisual } from '@/api/assessments/official-paper-review.api';
import { LearningImage } from './learning-media';

export function ModelAnswerVisuals({
  assessmentId,
  questionId,
  visuals,
}: {
  assessmentId?: string;
  questionId: string;
  visuals?: AnswerVisual[];
}) {
  if (!assessmentId || !visuals?.some((v) => v.status === 'approved'))
    return null;
  return (
    <section
      className="panel stack"
      aria-label="Approved model-answer diagrams"
    >
      <h3>Approved model-answer diagrams</h3>
      {visuals
        .filter((v) => v.status === 'approved')
        .map((visual) => (
          <details
            key={`${visual.partLabel}-${visual.assetId}`}
            open={visual.origin !== 'ai_generated'}
          >
            <summary>
              {visual.origin === 'ai_generated'
                ? `Show worked step for part ${visual.partLabel}`
                : `Model answer for part ${visual.partLabel}`}
            </summary>
            <figure
              key={`${visual.partLabel}-${visual.assetId}`}
              style={{ margin: 0, maxWidth: 600 }}
            >
              <LearningImage
                src={`/api/v1/assessments/${assessmentId}/questions/${questionId}/answer-visuals/${visual.assetId}`}
                description={visual.altText}
              />
              <figcaption>
                Part ({visual.partLabel})
                {visual.pointCodes.length
                  ? ` · ${visual.pointCodes.join(', ')}`
                  : ''}
                {visual.caption ? ` — ${visual.caption}` : ''}
                {visual.origin === 'ai_generated'
                  ? ' · AI-generated worked answer — not an official Pearson answer'
                  : ' · Reviewed marking scheme'}
              </figcaption>
              {visual.dataText && (
                <details>
                  <summary>Graph values (horizontal, vertical)</summary>
                  <p>{visual.dataText}</p>
                </details>
              )}
              {visual.explanation && <p>{visual.explanation}</p>}
              {visual.limitations && (
                <p className="small">{visual.limitations}</p>
              )}
            </figure>
          </details>
        ))}
    </section>
  );
}

export function PracticeWorkedAnswer({
  assessmentId,
  questionId,
}: {
  assessmentId: string;
  questionId: string;
}) {
  const [visuals, setVisuals] = useState<AnswerVisual[]>([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  return (
    <section className="panel stack">
      <p>
        Showing a worked answer makes this assisted practice; this question will
        not increase your independent mastery.
      </p>
      <Button
        disabled={busy}
        variant="outline"
        onClick={async () => {
          setBusy(true);
          try {
            const result = await request<{
              visuals: AnswerVisual[];
              message: string;
            }>(
              `assessments/${assessmentId}/questions/${questionId}/worked-answer`,
              { method: 'POST' },
            );
            setVisuals(result.visuals);
            setMessage(result.message);
          } catch (e) {
            setMessage(
              e instanceof Error ? e.message : 'Unable to show worked answer.',
            );
          } finally {
            setBusy(false);
          }
        }}
      >
        Show worked answer
      </Button>
      {message && <output>{message}</output>}
      <ModelAnswerVisuals
        assessmentId={assessmentId}
        questionId={questionId}
        visuals={visuals}
      />
    </section>
  );
}
