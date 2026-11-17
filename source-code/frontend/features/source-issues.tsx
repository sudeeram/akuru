'use client';
import { useEffect, useState } from 'react';
import { request } from '@/api/core/client';
import { Button } from '@/components/ui/button';

type Issue = {
  id: string;
  kind: string;
  role: string;
  pages: number[];
  description: string;
  partLabel: string | null;
  resolved: boolean;
  resolutionNotes: string[];
};
type Issues = { analysisId: string | null; issues: Issue[] };

export function SourceIssues({
  paperId,
  number,
  partLabel,
  disabled,
}: {
  paperId: string;
  number: string;
  partLabel?: string;
  disabled?: boolean;
}) {
  const [value, setValue] = useState<Issues | null>(null);
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const base = `admin/official-paper-reviews/${paperId}/questions/${encodeURIComponent(number)}/source-issues`;
  useEffect(() => {
    let active = true;
    void request<Issues>(base)
      .then((v) => {
        if (active) setValue(v);
      })
      .catch((e) => {
        if (active)
          setError(
            e instanceof Error ? e.message : 'Could not load source issues.',
          );
      });
    return () => {
      active = false;
    };
  }, [base]);
  const issues = value?.issues.filter(
    (i) => i.partLabel === null || i.partLabel === partLabel,
  );
  return (
    <section className="panel stack" aria-label="Source discrepancies">
      <strong>
        Source discrepancies · separate from extraction confidence
      </strong>
      <p>
        Record how an actual publisher conflict is handled. This does not change
        confidence or approve content. Unresolved answer/credit conflicts block
        Tutor release. Unreliable report guidance is withheld from students.
      </p>
      {issues?.map((i) => (
        <div className="stack" key={`${i.partLabel}:${i.id}`}>
          <strong>
            {i.resolved ? 'Resolved' : 'Needs review'} ·{' '}
            {i.kind.replaceAll('_', ' ')} · {i.role} · PDF pages{' '}
            {i.pages.join(', ')}
          </strong>
          <p>{i.description}</p>
          {i.resolutionNotes.map((text, index) => (
            <p key={index}>{text}</p>
          ))}
          {!i.resolved && (
            <Button
              variant="outline"
              disabled={disabled || busy || note.trim().length < 10}
              onClick={async () => {
                setBusy(true);
                setError('');
                try {
                  await request(`${base}/resolve`, {
                    method: 'POST',
                    body: {
                      analysisId: value?.analysisId,
                      issueId: i.id,
                      partLabel: i.partLabel,
                      note,
                    },
                  });
                  setValue(await request<Issues>(base));
                  setNote('');
                } catch (e) {
                  setError(
                    e instanceof Error
                      ? e.message
                      : 'Could not save the decision.',
                  );
                } finally {
                  setBusy(false);
                }
              }}
            >
              Record reviewed resolution
            </Button>
          )}
        </div>
      ))}
      {!!issues?.some((i) => !i.resolved) && (
        <label>
          Source-based resolution and authoritative marking decision
          <textarea
            value={note}
            maxLength={2000}
            disabled={busy}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>
      )}
      {issues && !issues.length && (
        <p>
          No structured source issues in the current assessment. Older
          assessment warnings remain in history.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
