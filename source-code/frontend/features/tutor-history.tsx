'use client';
import { StatusBadge } from '@/components/portal/badges';
import {
  AdvancedPanel,
  EditorDrawer,
  FilterToolbar,
  LoadingState,
  ErrorState,
} from '@/components/portal/workspace';
import { useWorkspaceSearch } from '@/lib/use-workspace-search';
/* eslint-disable react/react-compiler */
import { useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Empty, Heading } from './shared';
import {
  errorMessage,
  getTutorHistorySummaries,
  getTutorSafetyEvents,
  getTutorSupportTranscript,
  previewTutorTranscriptPurge,
  purgeTutorTranscripts,
  reviewTutorSafetyEvent,
  type TutorHistorySummary,
  type TutorSafetyEvent,
} from '@/api';

export function TutorHistory({
  admin = false,
  notify,
}: {
  admin?: boolean;
  notify: (message: string) => void;
}) {
  const [filters, setFilters] = useWorkspaceSearch({
    q: '',
    days: 'all',
    status: 'all',
  });
  const [loading, setLoading] = useState(true);
  const [summaries, setSummaries] = useState<TutorHistorySummary[]>([]),
    [events, setEvents] = useState<TutorSafetyEvent[]>([]);
  const [error, setError] = useState(''),
    [busy, setBusy] = useState(false),
    [reason, setReason] = useState(''),
    [days, setDays] = useState('365');
  const [preview, setPreview] = useState<{
    turnCount: number;
    sessionCount: number;
    cutoff: string;
  } | null>(null);
  const [transcript, setTranscript] = useState<{
    studentName: string;
    turns: {
      turnRef: string;
      role: string;
      content: string;
      purged: boolean;
    }[];
  } | null>(null);
  const load = useCallback(async () => {
    try {
      const [history, safety] = await Promise.all([
        getTutorHistorySummaries(),
        getTutorSafetyEvents(),
      ]);
      setSummaries(history.summaries);
      setEvents(safety.events);
      setError('');
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  const run = async (action: () => Promise<unknown>, message: string) => {
    setBusy(true);
    setError('');
    try {
      await action();
      await load();
      notify(message);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  };
  const recent = (createdAt: string) =>
    filters.days === 'all' ||
    Date.parse(createdAt) >= Date.now() - Number(filters.days) * 86400000;
  const filteredSummaries = summaries.filter(
    (item) =>
      recent(item.createdAt) &&
      (!filters.q ||
        `${item.studentName} ${item.subjectId} ${item.topicsCovered.map((topic) => topic.title).join(' ')}`
          .toLowerCase()
          .includes(filters.q.toLowerCase())),
  );
  const filteredEvents = events.filter(
    (item) =>
      recent(item.createdAt) &&
      (filters.status === 'all' || item.reviewStatus === filters.status) &&
      (!filters.q ||
        `${item.studentName} ${item.category}`
          .toLowerCase()
          .includes(filters.q.toLowerCase())),
  );
  if (loading)
    return (
      <LoadingState message="Loading Tutor summaries and safety notices…" />
    );
  if (error && !summaries.length && !events.length)
    return <ErrorState message={error} retry={() => void load()} />;
  return (
    <div className="stack">
      <Heading
        eyebrow={
          admin ? 'ADMIN · CONTROLLED SUPPORT' : 'PARENT · TUTOR HISTORY'
        }
        title={
          admin
            ? 'Tutor history and safety'
            : 'Learning summaries and safety notices'
        }
      >
        {admin
          ? 'Support access and transcript cleanup are always reason-required and audited.'
          : 'Educational summaries protect the child’s private conversation while keeping you informed.'}
      </Heading>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      <FilterToolbar
        search={filters.q}
        onSearch={(q) => setFilters({ q })}
        placeholder="Find a learner, subject or topic…"
        count={filteredSummaries.length}
        onClear={() => setFilters({ q: '', days: 'all', status: 'all' })}
      >
        <label>
          Period
          <select
            value={filters.days}
            onChange={(event) => setFilters({ days: event.target.value })}
          >
            <option value="all">All dates</option>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
          </select>
        </label>
        <label>
          Safety status
          <select
            value={filters.status}
            onChange={(event) => setFilters({ status: event.target.value })}
          >
            <option value="all">All statuses</option>
            {Array.from(new Set(events.map((item) => item.reviewStatus))).map(
              (value) => (
                <option key={value} value={value}>
                  {value.replaceAll('_', ' ')}
                </option>
              ),
            )}
          </select>
        </label>
      </FilterToolbar>
      <section className="panel stack">
        <h2>Session summaries</h2>
        {filteredSummaries.length ? (
          filteredSummaries.map((item) => (
            <article className="card stack" key={item.summaryRef}>
              <div className="spread">
                <h3>
                  {item.studentName} · {item.subjectId.toUpperCase()}
                </h3>
                <small>{new Date(item.createdAt).toLocaleString()}</small>
              </div>
              <p>
                <strong>Topics:</strong>{' '}
                {item.topicsCovered
                  .map((topic) => `${topic.code} · ${topic.title}`)
                  .join(', ')}
              </p>
              <p>
                <strong>Activities:</strong> {item.activities.join(', ')}
              </p>
              <p>
                <strong>Strengths:</strong>{' '}
                {item.strengths.join(' ') || 'More evidence is needed.'}
              </p>
              <p>
                <strong>Difficulties:</strong>{' '}
                {item.difficulties.join(' ') ||
                  'No verified difficulty was recorded.'}
              </p>
              <p>
                <strong>Next:</strong> {item.suggestedNextSteps.join(' ')}
              </p>
              <small>
                {item.usage.aiRequests || 0} AI requests ·{' '}
                {(item.usage.textTokens || 0).toLocaleString()} tokens ·{' '}
                {item.usage.voiceTurns || 0} voice turns
              </small>
              {admin && (
                <Button
                  variant="outline"
                  disabled={busy || reason.trim().length < 5}
                  onClick={async () => {
                    setBusy(true);
                    try {
                      setTranscript(
                        await getTutorSupportTranscript(
                          item.sessionRef,
                          reason,
                        ),
                      );
                      notify('Audited support transcript opened.');
                    } catch (cause) {
                      setError(errorMessage(cause));
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Open full transcript for support
                </Button>
              )}
            </article>
          ))
        ) : (
          <Empty title="No completed tutor sessions">
            A summary is created when a student ends a Tutor session.
          </Empty>
        )}
      </section>
      <section className="panel stack">
        <h2>Safety notifications</h2>
        <p>
          Notifications identify the concern and action without repeating the
          child’s message.
        </p>
        {filteredEvents.length ? (
          filteredEvents.map((item) => (
            <article className="card" key={item.eventRef}>
              <div className="spread">
                <strong>
                  {item.studentName} · {item.category.replace('_', ' ')}
                </strong>
                <StatusBadge status={item.severity} tone={item.severity === 'low' ? 'neutral' : undefined} />
              </div>
              <p>{item.action}</p>
              <small>
                {item.notificationStatus} · {item.reviewStatus} ·{' '}
                {new Date(item.createdAt).toLocaleString()}
              </small>
              {admin && item.reviewStatus !== 'resolved' && (
                <Button
                  variant="outline"
                  disabled={busy || reason.trim().length < 5}
                  onClick={() =>
                    void run(
                      () =>
                        reviewTutorSafetyEvent(
                          item.eventRef,
                          'resolved',
                          reason,
                        ),
                      'Safety event reviewed and resolved.',
                    )
                  }
                >
                  Resolve with audit note
                </Button>
              )}
            </article>
          ))
        ) : (
          <p>No safety notifications.</p>
        )}
      </section>
      {admin && (
        <>
          <section className="panel stack">
            <h2>Support reason</h2>
            <Input
              aria-label="Support and review reason"
              placeholder="Required for transcript access, review, or purge"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              maxLength={500}
            />
          </section>
          <AdvancedPanel title="Transcript retention cleanup">
            <section className="panel stack">
              <h2>Transcript retention cleanup</h2>
              <p>
                Transcripts remain forever unless an Admin explicitly performs
                this cleanup. Summaries, usage and audit records are preserved.
              </p>
              <label className="stack" htmlFor="purge-days">
                <span>Older than days</span>
                <Input
                  id="purge-days"
                  type="number"
                  min="1"
                  max="3650"
                  value={days}
                  onChange={(event) => {
                    setDays(event.target.value);
                    setPreview(null);
                  }}
                />
              </label>
              <div className="button-row">
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={async () => {
                    try {
                      setPreview(
                        await previewTutorTranscriptPurge(Number(days)),
                      );
                    } catch (cause) {
                      setError(errorMessage(cause));
                    }
                  }}
                >
                  Dry-run preview
                </Button>
                <Button
                  className="primary"
                  disabled={busy || !preview || reason.trim().length < 5}
                  onClick={() =>
                    void run(
                      () => purgeTutorTranscripts(Number(days), reason),
                      'Selected transcript content purged.',
                    )
                  }
                >
                  Confirm PURGE TRANSCRIPTS
                </Button>
              </div>
              {preview && (
                <p className="source-note">
                  {preview.turnCount} turns in {preview.sessionCount} sessions
                  before {new Date(preview.cutoff).toLocaleString()} will be
                  redacted.
                </p>
              )}
            </section>
          </AdvancedPanel>
          {transcript && (
            <EditorDrawer
              open={Boolean(transcript)}
              onOpenChange={(open) => {
                if (!open) setTranscript(null);
              }}
              title="Audited support transcript"
            >
              <section className="panel stack">
                <h2>Audited support transcript · {transcript.studentName}</h2>
                {transcript.turns.map((turn) => (
                  <article className="card" key={turn.turnRef}>
                    <strong>{turn.role}</strong>
                    <p>{turn.content}</p>
                    {turn.purged && <small>Content purged</small>}
                  </article>
                ))}
              </section>
            </EditorDrawer>
          )}
        </>
      )}
    </div>
  );
}
