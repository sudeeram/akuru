'use client';
import { useEffect, useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from '@/components/ui/toast';
import type { PaperReview } from '@/api';
import {
  getEvidenceRuns,
  getEvidenceJobs,
  proposeEvidence,
  queueEvidence,
  queueEvidenceBatch,
  reviewEvidence,
  type EvidenceRun,
  type EvidenceJob,
  type EvidenceProposal,
} from '@/api/assessments/evidence-links.api';

const notify = (title: string) => toast.add({ title, type: 'success' });

export function ExactEvidenceLinks({
  paperId,
  review,
  onUpdated,
  number,
  disabled = false,
}: {
  paperId: string;
  review: PaperReview;
  onUpdated: (value: PaperReview) => void;
  number?: string;
  disabled?: boolean;
}) {
  const [runs, setRuns] = useState<EvidenceRun[]>([]),
    [jobs, setJobs] = useState<EvidenceJob[]>([]),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(''),
    [progress, setProgress] = useState('');
  const [selected, setSelected] = useState<Record<string, boolean>>({}),
    [confirmed, setConfirmed] = useState(false);
  const [adjust, setAdjust] = useState<{
    part: string;
    role: 'paper' | 'scheme';
    page: number;
    bounds: Record<'x0' | 'y0' | 'x1' | 'y1', number>;
    reason: string;
    confidence: number;
    question: string;
  } | null>(null);
  const pending = jobs.some((j) => ['queued', 'processing'].includes(j.status));
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const [a, b] = await Promise.all([
          getEvidenceRuns(paperId),
          getEvidenceJobs(paperId),
        ]);
        if (active) {
          setRuns(a);
          setJobs(b);
        }
      } catch (e) {
        if (active)
          setError(e instanceof Error ? e.message : 'Unable to load evidence.');
      }
    }
    void load();
    const timer = pending
      ? setInterval(() => {
          void load();
        }, 5000)
      : undefined;
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [paperId, pending]);
  const questions = review.questions.filter(
    (q) => !number || q.number === number,
  );
  const chosenRuns = runs
    .filter((r) => !number || r.number === number)
    .filter(
      (r, i, all) =>
        !all.slice(i + 1).some((other) => other.number === r.number),
    );
  const snapshot = (q: PaperReview['questions'][number]) => ({
    requestId: crypto.randomUUID(),
    number: q.number,
    expectedRevision: q.revision,
    expectedContentHash: q.analysisContentHash,
  });
  async function analyse(ai: boolean) {
    setBusy(true);
    setError('');
    try {
      if (ai && !number) {
        await queueEvidenceBatch(paperId, questions.map(snapshot));
      } else
        for (let i = 0; i < questions.length; i++) {
          const q = questions[i];
          setProgress(
            `${ai ? 'Queueing AI' : 'Matching source blocks'}: question ${q.number} (${i + 1}/${questions.length})`,
          );
          if (ai) {
            await queueEvidence(paperId, snapshot(q));
            break;
          } // One durable job per paper at a time; no hidden batch charges.
          await proposeEvidence(paperId, snapshot(q));
        }
      setRuns(await getEvidenceRuns(paperId));
      setJobs(await getEvidenceJobs(paperId));
      notify(
        ai
          ? 'AI evidence analysis queued. It creates proposals only.'
          : 'Source matching complete. Review the results.',
      );
      setProgress('');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Evidence analysis failed.');
    } finally {
      setBusy(false);
    }
  }
  async function decide(
    run: EvidenceRun,
    decision: 'apply' | 'reject',
    autoOnly = false,
  ) {
    setBusy(true);
    setError('');
    try {
      const ids = run.proposals
        .filter((p) =>
          autoOnly ? p.autoEligible && p.status === 'matched' : selected[p.id],
        )
        .map((p) => p.id);
      if (!ids.length)
        throw new Error('Select at least one evidence proposal.');
      const q = review.questions.find((q) => q.number === run.number)!;
      const result = await reviewEvidence(paperId, run.id, {
        proposalIds: ids,
        expectedRevision: q.revision,
        expectedContentHash: q.analysisContentHash,
        decision,
        confirmSourceReview: confirmed,
        autoOnly,
      });
      onUpdated(result.review);
      setRuns(await getEvidenceRuns(paperId));
      setSelected({});
      setConfirmed(false);
      notify(
        decision === 'reject'
          ? 'Selected evidence proposals rejected.'
          : 'Exact evidence linked. A fresh accuracy assessment is required before AI approval.',
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Evidence review failed.');
    } finally {
      setBusy(false);
    }
  }
  function edit(p: EvidenceProposal, q: string) {
    setAdjust({
      part: p.part,
      role: p.role,
      page: p.page || 1,
      bounds: p.normalizedBounds || { x0: 0.05, y0: 0.1, x1: 0.95, y1: 0.9 },
      reason: p.reason,
      confidence: p.confidence,
      question: q,
    });
  }
  return (
    <section className="panel stack" aria-label="Exact source evidence linking">
      <h2>Exact question &amp; marking-scheme evidence</h2>
      <p>
        Match existing blocks without a model call, or queue one AI question
        analysis using the configured backend account. AI proposals are not
        content approval. Check every required region and continuation before
        linking.
      </p>
      <div className="button-row">
        <Button
          disabled={busy || disabled || pending}
          onClick={() => void analyse(false)}
        >
          Find existing exact blocks{number ? '' : ' · paper'}
        </Button>
        <Button
          disabled={busy || disabled || pending || !questions.length}
          onClick={() => void analyse(true)}
        >
          AI analyse{' '}
          {number ? `Q${number}` : `paper · ${questions.length} questions`}
        </Button>
      </div>
      {!number && (
        <p className="small">
          Paper analysis queues each question durably. Text matching is free;
          model jobs can incur usage and run one at a time.
        </p>
      )}
      {disabled && (
        <p>
          Save or discard your current question edits before changing evidence.
        </p>
      )}
      {(busy || pending) && (
        <output aria-live="polite">
          {progress ||
            'AI source analysis queued or processing. You can leave and return; its progress is saved.'}
        </output>
      )}
      {jobs
        .filter((j) => !number || j.number === number)
        .slice(0, 3)
        .map((j) => (
          <p key={j.id} role={j.status === 'failed' ? 'alert' : undefined}>
            Q{j.number}: {j.status.replaceAll('_', ' ')}
            {j.result.model ? ` · ${j.result.model}` : ''}
            {j.errorCode
              ? ` · ${j.errorCode.replaceAll('_', ' ')}. Review sources or retry with a new analysis.`
              : ''}
          </p>
        ))}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      <label>
        <input
          type="checkbox"
          checked={confirmed}
          onChange={(e) => setConfirmed(e.target.checked)}
        />{' '}
        I have checked the selected original source regions, their subpart
        labels and all required continuations.
      </label>
      {chosenRuns.map((run) => {
        const q = review.questions.find((q) => q.number === run.number);
        const stale =
          !q ||
          q.revision !== run.revision ||
          q.analysisContentHash !== run.contentHash;
        return (
          <details key={run.id} open={!!number}>
            <summary>
              Q{run.number} ·{' '}
              {run.proposals.filter((p) => p.status === 'linked').length} linked
              ·{' '}
              {
                run.proposals.filter((p) =>
                  ['ambiguous', 'missing'].includes(p.status),
                ).length
              }{' '}
              need attention{stale ? ' · superseded source snapshot' : ''}
            </summary>
            <p className="small">
              {run.provenance
                .map(
                  (p) => `${p.role}: ${p.modelName || p.modelId || p.method}`,
                )
                .join('; ')}
              . Matching percentages are estimates, not extraction accuracy.
            </p>
            <div className="button-row">
              <Button
                disabled={busy || disabled || stale || !confirmed}
                onClick={() => void decide(run, 'apply')}
              >
                Verify and link selected regions
              </Button>
              <Button
                variant="outline"
                disabled={busy || disabled || stale}
                onClick={() => void decide(run, 'reject')}
              >
                Reject selected proposals
              </Button>
              <Button
                variant="outline"
                disabled={
                  busy ||
                  disabled ||
                  stale ||
                  !run.proposals.some(
                    (p) => p.autoEligible && p.status === 'matched',
                  )
                }
                onClick={() => void decide(run, 'apply', true)}
              >
                Link exact reviewed matches
              </Button>
            </div>
            {run.proposals.map((p) => (
              <article className="panel stack" key={p.id}>
                <label>
                  <input
                    type="checkbox"
                    checked={!!selected[p.id]}
                    disabled={
                      busy ||
                      stale ||
                      ['linked', 'rejected', 'missing'].includes(p.status)
                    }
                    onChange={(e) =>
                      setSelected((s) => ({ ...s, [p.id]: e.target.checked }))
                    }
                  />{' '}
                  Part {p.part || '(whole question)'} ·{' '}
                  {p.role === 'paper' ? 'Question paper' : 'Marking scheme'}
                  {p.page ? ` · PDF page ${p.page}` : ''} ·{' '}
                  <strong>{p.status}</strong> · {p.confidence}% match
                </label>
                <p>{p.reason}</p>
                {(p.text || p.normalizedBounds) && (
                  <details>
                    <summary>Original source excerpt and region</summary>
                    <p style={{ whiteSpace: 'pre-wrap' }}>{p.text}</p>
                    <Image
                      src={`/api/v1/admin/official-paper-reviews/${paperId}/evidence-links/${run.id}/${p.id}/preview`}
                      alt={`Original ${p.role} evidence for Q${run.number} part ${p.part}`}
                      width={700}
                      height={500}
                      unoptimized
                      style={{
                        width: '100%',
                        height: 'auto',
                        maxHeight: 500,
                        objectFit: 'contain',
                      }}
                    />
                  </details>
                )}
                <Button
                  variant="outline"
                  disabled={busy || disabled || !q || q.status === 'approved'}
                  onClick={() => edit(p, run.number)}
                >
                  Adjust or select original PDF region
                </Button>
              </article>
            ))}
          </details>
        );
      })}
      {adjust && (
        <form
          className="panel stack"
          onSubmit={async (e) => {
            e.preventDefault();
            setBusy(true);
            setError('');
            try {
              const q = review.questions.find(
                (q) => q.number === adjust.question,
              )!;
              const { question: _question, ...selection } = adjust;
              await proposeEvidence(paperId, {
                ...snapshot(q),
                selections: [{ ...selection, sourceVerified: false }],
                provenance: [
                  {
                    role: adjust.role,
                    method: 'manual',
                    processedAt: new Date().toISOString(),
                    notes:
                      'Admin-selected original PDF region; verify before linking.',
                  },
                ],
              });
              setRuns(await getEvidenceRuns(paperId));
              setAdjust(null);
              notify(
                'Adjusted source region prepared. Preview it and confirm before linking.',
              );
            } catch (cause) {
              setError(
                cause instanceof Error
                  ? cause.message
                  : 'Unable to prepare region.',
              );
            } finally {
              setBusy(false);
            }
          }}
        >
          <h3>
            Original PDF region · Q{adjust.question} part {adjust.part}
          </h3>
          <p>
            Coordinates are fractions from 0 to 1: left, top, right, bottom.
            This extracts original text; it does not generate or rewrite an
            answer.
          </p>
          <label htmlFor="evidence-region-page">
            PDF page
            <Input
              id="evidence-region-page"
              type="number"
              min={1}
              value={adjust.page}
              onChange={(e) =>
                setAdjust({ ...adjust, page: Number(e.target.value) })
              }
            />
          </label>
          {(['x0', 'y0', 'x1', 'y1'] as const).map((k) => (
            <label key={k} htmlFor={`evidence-region-${k}`}>
              {k}
              <Input
                id={`evidence-region-${k}`}
                type="number"
                min={0}
                max={1}
                step={0.001}
                required
                value={adjust.bounds[k]}
                onChange={(e) =>
                  setAdjust({
                    ...adjust,
                    bounds: { ...adjust.bounds, [k]: Number(e.target.value) },
                  })
                }
              />
            </label>
          ))}
          <label htmlFor="evidence-region-reason">
            Reason
            <Input
              id="evidence-region-reason"
              required
              minLength={10}
              value={adjust.reason}
              onChange={(e) => setAdjust({ ...adjust, reason: e.target.value })}
            />
          </label>
          <label htmlFor="evidence-region-confidence">
            Estimated matching confidence
            <Input
              id="evidence-region-confidence"
              type="number"
              min={0}
              max={100}
              required
              value={adjust.confidence}
              onChange={(e) =>
                setAdjust({ ...adjust, confidence: Number(e.target.value) })
              }
            />
          </label>
          <div className="button-row">
            <Button type="submit" disabled={busy}>
              Preview adjusted region
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setAdjust(null)}
            >
              Cancel
            </Button>
          </div>
        </form>
      )}
    </section>
  );
}
