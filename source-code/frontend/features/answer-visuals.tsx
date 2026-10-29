'use client';
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
              {visual.caption ? ` — ${visual.caption}` : ''} · Reviewed marking
              scheme
            </figcaption>
          </figure>
        ))}
    </section>
  );
}
