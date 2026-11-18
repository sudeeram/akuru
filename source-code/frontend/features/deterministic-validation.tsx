import { useEffect, useState, useId } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { request } from '@/api/core/client';
import { toast } from '@/components/ui/toast';

type Run = {
  id: string;
  part: string;
  passed: boolean;
  current?: boolean;
  coverageComplete: boolean;
  noModelCalls: boolean;
  engineHash: string;
  cases: {
    answer: string;
    expectedMarks?: number;
    expectedPoints: string[];
    actualPoints: string[];
    holdout: boolean;
    actualMarks?: number;
    actualRequiresReview: boolean;
    passed: boolean;
    reason?: string;
  }[];
};
export function DeterministicValidation({
  paperId,
  number,
  part,
  revision,
  disabled,
  onSaved,
}: {
  paperId: string;
  number: string;
  part: string;
  revision: number;
  disabled: boolean;
  onSaved?: () => void;
}) {
  const controlId = useId();
  const [history, setHistory] = useState<Run[]>([]);
  const [fixtures, setFixtures] = useState('');
  const [notes, setNotes] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const notify = (title: string) => toast.add({ title, type: 'info' });
  const root = `admin/official-paper-reviews/${paperId}`;
  useEffect(() => {
    let active = true;
    void request<Run[]>(`${root}/questions/${number}/deterministic-validations`)
      .then((v) => {
        if (active) setHistory(v);
      })
      .catch(() => {
        if (active) setError('Could not load validation history.');
      });
    return () => {
      active = false;
    };
  }, [root, number, revision]);
  return (
    <details>
      <summary>
        Validate without model calls ·{' '}
        {history.some((r) => r.part === part && r.current && r.passed)
          ? 'Current certificate'
          : 'Validation required'}
      </summary>
      <div className="stack">
        <p>
          The backend runs the deployed recognizer and allocator on synthetic
          answers. A pass requires all criteria, zero/full/partial credit, a
          holdout and an ambiguous-answer review case. This makes no paid model
          calls. It does not approve source content or release a complete exam.
        </p>
        <label htmlFor={`${controlId}-notes`} className="stack">
          Reviewed source interpretation
          <Textarea
            id={`${controlId}-notes`}
            value={notes}
            onChange={(e) => {
              setNotes(e.target.value);
              setConfirmed(false);
            }}
          />
        </label>
        <label htmlFor={`${controlId}-cases`} className="stack">
          Synthetic fixture array (prepared packages may be pasted here)
          <Textarea
            id={`${controlId}-cases`}
            rows={10}
            value={fixtures}
            maxLength={600000}
            onChange={(e) => {
              setFixtures(e.target.value);
              setConfirmed(false);
            }}
            placeholder={
              '[{"answer":"0.057","expectedMarks":2,"expectedPoints":["P_FULL"],"holdout":true}]'
            }
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I checked the exact scheme, exclusions, expected outcomes and fixture
          coverage.
        </label>
        <Button
          disabled={disabled || busy || !confirmed || notes.trim().length < 20}
          onClick={async () => {
            setBusy(true);
            setError('');
            try {
              const cases = JSON.parse(fixtures);
              if (!Array.isArray(cases))
                throw new Error('Enter a JSON array of synthetic cases.');
              const caps = await request<{ engineHash: string }>(
                `${root}/deterministic-capabilities`,
              );
              const run = await request<Run>(
                `${root}/questions/${number}/validate-deterministic`,
                {
                  method: 'POST',
                  body: {
                    requestId: crypto.randomUUID(),
                    partLabel: part,
                    expectedRevision: revision,
                    expectedEngineHash: caps.engineHash,
                    confirmSourceReviewed: true,
                    sourceNotes: notes,
                    cases,
                  },
                },
              );
              setHistory((old) => [run, ...old]);
              notify(
                run.passed
                  ? 'Deterministic validation passed. Reload to see saved readiness.'
                  : 'Validation did not pass. Inspect cases and coverage.',
              );
              onSaved?.();
            } catch (cause) {
              setError(
                cause instanceof Error ? cause.message : 'Validation failed.',
              );
            } finally {
              setBusy(false);
            }
          }}
        >
          Validate without model calls
        </Button>
        {error && <p role="alert">{error}</p>}
        {history
          .filter((r) => r.part === part)
          .map((r) => (
            <details key={r.id}>
              <summary>
                {r.passed ? 'Passed' : 'Not passed'} ·{' '}
                {r.current
                  ? 'Current'
                  : r.current === false
                    ? 'Historical/stale'
                    : 'Reload for current status'}{' '}
                · no model calls
              </summary>
              <p>
                Engine fingerprint: {r.engineHash} · coverage:{' '}
                {r.coverageComplete ? 'complete' : 'incomplete'}
              </p>
              <table>
                <thead>
                  <tr>
                    <th>Answer</th>
                    <th>Expected</th>
                    <th>Actual</th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {r.cases.map((c, i) => (
                    <tr key={i}>
                      <td>{c.answer}</td>
                      <td>{c.expectedMarks ?? 'Review'} · {c.expectedPoints.join(', ') || 'no credited criteria'}</td>
                      <td>
                        {c.actualRequiresReview ? 'Review' : `${c.actualMarks} · ${c.actualPoints.join(', ') || 'no credited criteria'}`}
                      </td>
                      <td>
                        {c.passed ? 'Passed' : 'Failed'} {c.holdout ? '· holdout' : ''} {c.reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          ))}
      </div>
    </details>
  );
}
