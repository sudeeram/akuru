'use client';
import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { toast } from '@/components/ui/toast';
import { getPaperReview, type PaperReview } from '@/api';
import { request } from '@/api/core/client';
import {
  getAccuracyJobs,
  getAccuracyReadiness,
  queueAccuracyJobs,
  type AccuracyJob,
  type AccuracyReadiness,
} from '@/api/assessments/accuracy-jobs.api';

const errors: Record<string, string> = {
  evidence_conflict:
    'Saved content changed. Refresh and queue a new assessment.',
  analysis_conflict: 'Another assessment was saved. Refresh before retrying.',
  accuracy_visual_review_required:
    'Finish the image review before reassessment.',
  accuracy_job_interrupted:
    'Processing was interrupted. Check history before explicitly retrying; no automatic paid retry was made.',
  accuracy_page_limit:
    'Too many source pages/crops for one model request. Assisted source review is required.',
  accuracy_invalid_output:
    'The model response could not be validated. No assessment was saved.',
  accuracy_unseen_page:
    'The model cited an unprovided source page. No assessment was saved.',
};

export function AccuracyReassessment({
  paperId,
  review,
  number,
  disabled = false,
  onUpdated,
}: {
  paperId: string;
  review: PaperReview;
  number?: string;
  disabled?: boolean;
  onUpdated: (value: PaperReview) => void;
}) {
  const [ready, setReady] = useState<AccuracyReadiness | null>(null);
  const [jobs, setJobs] = useState<AccuracyJob[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [tick, setTick] = useState(0);
  const hadPending = useRef(false);
  const updated = useRef(onUpdated);
  useEffect(() => {
    updated.current = onUpdated;
  }, [onUpdated]);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    void Promise.all([getAccuracyReadiness(paperId), getAccuracyJobs(paperId)])
      .then(async ([value, work]) => {
        if (!active) return;
        setReady(value);
        setJobs(work);
        const pending = work.some((j) =>
          ['queued', 'processing'].includes(j.status),
        );
        if (pending) {
          hadPending.current = true;
          timer = setTimeout(() => setTick((v) => v + 1), 4000);
        } else if (hadPending.current) {
          hadPending.current = false;
          const current = await getPaperReview(paperId);
          if (active) {
            updated.current(current);
            toast.add({
              title:
                'Reassessment finished. Check results and remaining review gates.',
              type: 'success',
            });
          }
        }
      })
      .catch((cause) => {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : 'Unable to load reassessment status.',
          );
      });
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [paperId, review, tick]);
  const items = (ready?.questions || []).filter(
    (q) => !number || q.number === number,
  );
  const eligible = items.filter((q) => q.canReassess && q.reassessmentRequired);
  const pending = jobs.some((j) => ['queued', 'processing'].includes(j.status));
  const visual = items.filter((q) => q.visualBlockers.length);
  const manual = items.filter((q) => q.manualContentParts.length);
  const reviewUrl = (n: string, part?: string) =>
    `/admin/exam-documents/review/${paperId}?record=${encodeURIComponent(n)}${part !== undefined ? `&section=${encodeURIComponent(part)}` : ''}`;
  return (
    <section className="stack" aria-label="Final content reassessment">
      <h2>Final content reassessment</h2>
      <p>
        Review image crops, labels and associations first. AI then checks the
        final saved wording, marking points, sources and published curriculum
        evidence. You only need to inspect content at 75% or lower, or with an
        explicit unresolved blocker. Human decisions and explicit withdrawals
        are preserved. Eligible subparts are automatically released for Tutor
        practice; formal-exam publication stays separate.
      </p>
      <div className="form-grid">
        <div>
          <h3>Images needing review · {visual.length} questions</h3>
          {visual.length ? (
            visual.map((q) => (
              <p key={q.number}>
                <a href={reviewUrl(q.number)}>Q{q.number}</a>:{' '}
                {q.visualBlockers.join(' ')}
              </p>
            ))
          ) : (
            <p>No outstanding image-review gates in this selection.</p>
          )}
        </div>
        <div>
          <h3>
            Content needing manual review ·{' '}
            {manual.reduce((n, q) => n + q.manualContentParts.length, 0)}{' '}
            subparts
          </h3>
          {manual.map((q) => (
            <p key={q.number}>
              Q{q.number}:{' '}
              {q.manualContentParts.map((p) => (
                <a
                  key={p}
                  href={reviewUrl(q.number, p)}
                  style={{ marginRight: '0.75rem' }}
                >
                  {p || 'whole question'}
                </a>
              ))}
            </p>
          ))}
          {!manual.length && (
            <p>
              No current low-confidence content flagged. Outdated assessments
              must be rerun before this result can be relied on.
            </p>
          )}
        </div>
      </div>
      <output aria-live="polite">
        {items.filter((q) => q.reassessmentRequired).length} questions need a
        fresh assessment · {eligible.length} ready after image review.
      </output>
      {disabled && (
        <p>
          Save or discard your current question edits before queueing
          reassessment.
        </p>
      )}
      <Button
        disabled={disabled || busy || pending || !eligible.length}
        onClick={() => setConfirm(true)}
      >
        Reassess reviewed content{number ? ` · Q${number}` : ''}
      </Button>
      <Button
        variant="outline"
        disabled={disabled || busy || pending}
        onClick={async () => {
          setBusy(true);
          try {
            await request(
              `admin/official-paper-reviews/${paperId}/auto-tutor-release`,
              { method: 'POST', body: {} },
            );
            updated.current(await getPaperReview(paperId));
            setTick((v) => v + 1);
            toast.add({
              title:
                'Eligible Tutor releases checked. No AI call was made; unresolved gates and withdrawals remain protected.',
              type: 'success',
            });
          } catch (cause) {
            setError(
              cause instanceof Error
                ? cause.message
                : 'Unable to check Tutor releases.',
            );
          } finally {
            setBusy(false);
          }
        }}
      >
        Retry eligible Tutor releases · no AI call
      </Button>
      {confirm && (
        <fieldset className="stack">
          <legend>Confirm paid reassessment</legend>
          <p>
            Queue {eligible.length} question assessments using the configured
            AKURU backend AI account? Model usage can incur charges. Results are
            checked against the current saved source version. Eligible content
            can become AI approved and automatically available for Tutor
            practice. This does not publish a formal exam.
          </p>
          <div className="form-grid">
            <Button
              variant="outline"
              disabled={busy}
              onClick={() => setConfirm(false)}
            >
              Cancel
            </Button>
            <Button
              disabled={busy || disabled || pending || !eligible.length}
              onClick={async () => {
                setBusy(true);
                setError('');
                try {
                  const questions = eligible.map((item) => {
                    const q = review.questions.find(
                      (v) => v.number === item.number,
                    )!;
                    return {
                      requestId: crypto.randomUUID(),
                      number: q.number,
                      expectedRevision: q.revision,
                      expectedContentHash: q.analysisContentHash,
                      expectedAnalysisVersion: q.analysisVersion || 0,
                    };
                  });
                  setJobs(await queueAccuracyJobs(paperId, questions));
                  hadPending.current = true;
                  setConfirm(false);
                  setTick((v) => v + 1);
                  toast.add({
                    title:
                      'Reassessment queued. You can leave this page and return.',
                    type: 'success',
                  });
                } catch (cause) {
                  setError(
                    cause instanceof Error
                      ? cause.message
                      : 'Unable to queue reassessment. Refresh job status before retrying.',
                  );
                } finally {
                  setBusy(false);
                }
              }}
            >
              Queue reassessment
            </Button>
          </div>
        </fieldset>
      )}
      {error && <p role="alert">{error}</p>}
      {!!jobs.length && (
        <details>
          <summary>
            Reassessment jobs ·{' '}
            {jobs.filter((j) => j.status === 'completed').length} completed ·{' '}
            {jobs.filter((j) => j.status === 'failed').length} failed ·{' '}
            {
              jobs.filter((j) => ['queued', 'processing'].includes(j.status))
                .length
            }{' '}
            pending
          </summary>
          <ul>
            {jobs
              .filter((j) => !number || j.number === number)
              .map((j) => (
                <li key={j.id}>
                  Q{j.number}: {j.status}
                  {j.result.confidence !== undefined
                    ? ` · ${j.result.confidence}%`
                    : ''}
                  {j.result.model ? ` · ${j.result.model}` : ''}
                  {j.errorCode
                    ? ` · ${errors[j.errorCode] || 'Processing failed safely. Check source/AI configuration and job history before an explicit retry.'}`
                    : ''}
                </li>
              ))}
          </ul>
        </details>
      )}
      {!!review.assessmentBlockers?.length && (
        <details>
          <summary>Remaining release / scoring blockers</summary>
          <ul>
            {review.assessmentBlockers.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
