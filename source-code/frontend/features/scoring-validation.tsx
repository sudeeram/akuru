'use client';

import { useEffect, useId, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { request } from '@/api/core/client';

type Result = {
  passed: boolean;
  cases: {
    expectedMarks: number;
    actualMarks: number;
    expectedPoints: string[];
    actualPoints: string[];
    passed: boolean;
  }[];
};

type Job = {
  id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  errorCode?: string;
  result?: Result & { failureReason?: string };
};

export function ScoringValidation({
  paperId,
  number,
  part,
  revision,
  disabled,
}: {
  paperId: string;
  number: string;
  part: string;
  revision: number;
  disabled: boolean;
}) {
  const examplesId = useId();
  const [examples, setExamples] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [job, setJob] = useState<Job | null>(null);
  const key = `akuru:scoring-validation:${paperId}:${number}:${part}`;
  const pending = job?.status === 'queued' || job?.status === 'processing';
  const result = job?.status === 'completed' ? job.result : undefined;
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const id = job?.id || sessionStorage.getItem(key);
    if (!id || (job && !pending)) return;
    async function refresh() {
      try {
        const value = await request<Job>(
          `admin/official-paper-reviews/${paperId}/scoring-validation/${id}`,
        );
        if (active) setJob(value);
      } catch (cause) {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : 'Could not load the validation result.',
          );
      }
      if (active) timer = setTimeout(refresh, 3000);
    }
    if (job) timer = setTimeout(refresh, 3000);
    else void refresh();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [job, key, paperId, pending]);
  const lines = examples.split('\n').filter((line) => line.trim());
  return (
    <details>
      <summary>Validate marking with sample answers</summary>
      <div className="stack">
        <p>
          Use reviewed, synthetic answers only. Enter up to 8 lines in the form{' '}
          <code>P1,P2 | sample answer</code>. Use <code>0 | sample answer</code>{' '}
          for zero credit. Include zero, full and partial credit where
          applicable, and cover every point. For score bands, enter only the credited band code (for example FULL or PARTIAL); its configured marks are used, not the number of codes.
        </p>
        <label htmlFor={examplesId}>
          Sample answers and expected point codes
          <Textarea
            id={examplesId}
            value={examples}
            rows={6}
            maxLength={16500}
            disabled={busy}
            onChange={(event) => {
              setExamples(event.target.value);
              setConfirmed(false);
            }}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={confirmed}
            disabled={busy}
            onChange={(event) => setConfirmed(event.target.checked)}
          />
          I verified these examples and the saved scheme, including any caps,
          dependencies and alternative answers.
        </label>
        <p>
          This uses two paid model calls per answer. A pass saves automatic
          marking readiness and may make the subpart eligible for Tutor
          practice.
        </p>
        <Button
          variant="outline"
          disabled={
            disabled ||
            busy ||
            pending ||
            !confirmed ||
            lines.length < 2 ||
            lines.length > 8
          }
          onClick={async () => {
            const samples = lines.map((line) => {
              const boundary = line.indexOf('|');
              const codes = line.slice(0, boundary).trim();
              return {
                answer: boundary > 0 ? line.slice(boundary + 1).trim() : '',
                expectedPoints:
                  codes === '0'
                    ? []
                    : codes.split(',').map((code) => code.trim()),
              };
            });
            if (
              samples.some(
                (sample) =>
                  !sample.answer || sample.expectedPoints.some((code) => !code),
              )
            ) {
              setError(
                'Use one line per sample with expected point codes or 0 before the | separator.',
              );
              return;
            }
            setBusy(true);
            setError('');
            try {
              const value = await request<Job>(
                `admin/official-paper-reviews/${paperId}/questions/${encodeURIComponent(number)}/validate-scoring`,
                {
                  method: 'POST',
                  body: {
                    requestId: crypto.randomUUID(),
                    partLabel: part,
                    expectedRevision: revision,
                    confirmReviewed: true,
                    samples,
                  },
                },
              );
              sessionStorage.setItem(key, value.id);
              setJob(value);
            } catch (cause) {
              setError(
                cause instanceof Error
                  ? cause.message
                  : 'Scoring validation failed.',
              );
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy || pending
            ? 'Checking sample answers…'
            : `Run scoring validation · ${lines.length * 2} model calls`}
        </Button>
        {error && <p role="alert">{error}</p>}
        {job?.status === 'failed' && (
          <p role="alert">
            Scoring validation failed (
            {job.errorCode === 'ai_schema_invalid'
              ? 'AKURU response schema rejected by the provider; contact your administrator before retrying'
              : job.errorCode}
            ).{' '}
            {job.result?.failureReason ||
              'No scoring pass was saved. Inspect the job error before retrying.'}
          </p>
        )}
        {result && (
          <output>
            {result.passed
              ? 'Passed · automatic marking readiness saved. Reload after saving or discarding any other edits to see the updated review.'
              : 'Needs review · marking readiness unchanged.'}
            <ul>
              {result.cases.map((item, index) => (
                <li key={index}>
                  Sample {index + 1}: {item.passed ? 'Passed' : 'Needs review'}{' '}
                  · expected {item.expectedMarks} (
                  {item.expectedPoints.join(', ') || 'none'}), awarded{' '}
                  {item.actualMarks} ({item.actualPoints.join(', ') || 'none'})
                </li>
              ))}
            </ul>
          </output>
        )}
      </div>
    </details>
  );
}
