'use client';
import { useEffect, useState } from 'react';
import { request } from '@/api/core/client';
import { errorMessage, type PaperReview } from '@/api';
import { Button } from '@/components/ui/button';

type Release = {
  number: string;
  partLabel: string;
  enabled: boolean;
  current: boolean;
};
export function TutorPastPaperReleases({
  paperId,
  review,
}: {
  paperId: string;
  review: PaperReview;
}) {
  const [releases, setReleases] = useState<Release[]>([]);
  const [readiness, setReadiness] = useState<
    {
      number: string;
      partLabel: string;
      ready: boolean;
      blocker: string | null;
    }[]
  >([]);
  const [loadedPaperId, setLoadedPaperId] = useState('');
  const [busy, setBusy] = useState(false),
    [notice, setNotice] = useState('');
  const load = () =>
    request<Release[]>(
      `admin/official-paper-reviews/${paperId}/chat-releases`,
    ).then(setReleases);
  useEffect(() => {
    let active = true;
    void Promise.all([
      request<typeof readiness>(
        `admin/official-paper-reviews/${paperId}/chat-release-readiness`,
      ),
      request<Release[]>(
        `admin/official-paper-reviews/${paperId}/chat-releases`,
      ),
    ])
      .then(([gates, rows]) => {
        if (active) {
          setLoadedPaperId(paperId);
          setReadiness(gates);
          setReleases(rows);
        }
      })
      .catch((cause) => {
        if (active) setNotice(errorMessage(cause));
      });
    return () => {
      active = false;
    };
  }, [paperId, review]);
  return (
    <details className="panel">
      <summary>Release approved subparts for Tutor chat</summary>
      <div className="stack">
        <p>
          This releases individual self-contained practice items, not a complete
          paper. A subpart must be human approved or AI approved, mapped to
          published topics and have confirmed marking readiness. Independent
          subparts can pass while siblings remain blocked; shared context must
          still be complete. Changing the reviewed source invalidates its
          release.
        </p>
        {notice && <output>{notice}</output>}
        {review.questions.flatMap((question) =>
          question.data.parts
            .filter((part) => part.coverage === 'supported')
            .map((part) => {
              const released =
                loadedPaperId === paperId &&
                releases.some(
                  (r) =>
                    r.number === question.number &&
                    r.partLabel === part.label &&
                    r.enabled &&
                    r.current,
                );
              const gate = readiness.find(
                (r) =>
                  r.number === question.number && r.partLabel === part.label,
              );
              const ready = loadedPaperId === paperId && gate?.ready === true;
              return (
                <div
                  className="panel row"
                  key={`${question.number}:${part.label}`}
                  style={{ justifyContent: 'space-between' }}
                >
                  <span>
                    <strong>
                      Q{question.number}({part.label})
                    </strong>{' '}
                    ·{' '}
                    {!ready && gate?.blocker && <small>{gate.blocker} </small>}
                    {released
                      ? 'Released for practice'
                      : ready
                        ? 'Ready for release review'
                        : 'Approval or marking readiness required'}
                  </span>
                  <Button
                    disabled={busy || (!ready && !released)}
                    variant="outline"
                    onClick={async () => {
                      if (
                        !window.confirm(
                          released
                            ? 'Withdraw this practice item? Existing access will be blocked.'
                            : 'Confirm this subpart is self-contained with its shared stem and approved visuals, and can be released for Student practice?',
                        )
                      )
                        return;
                      setBusy(true);
                      setNotice('');
                      try {
                        await request(
                          `admin/official-paper-reviews/${paperId}/questions/${question.number}/chat-release`,
                          {
                            method: 'POST',
                            body: {
                              partLabel: part.label,
                              revision: question.revision,
                              confirmSelfContained: true,
                              enabled: !released,
                            },
                          },
                        );
                        await load();
                        setNotice(
                          released
                            ? 'Practice item withdrawn.'
                            : 'Practice item released. Student coverage and account release controls still apply.',
                        );
                      } catch (cause) {
                        setNotice(errorMessage(cause));
                      } finally {
                        setBusy(false);
                      }
                    }}
                  >
                    {released
                      ? 'Withdraw practice item'
                      : 'Release for Tutor practice'}
                  </Button>
                </div>
              );
            }),
        )}
      </div>
    </details>
  );
}
