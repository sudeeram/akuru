'use client';

import { tutorLearningContextChanged } from '@/lib/tutor-session-context';
import { request } from '@/api/core/client';
import { TutorPastPaperCard } from './tutor-past-paper-card';
import type { PastPaperChatState } from '@/api/tutoring/tutor.types';
import { ModelAnswerVisuals, PracticeWorkedAnswer } from './answer-visuals';
import { DrawingSubmissions } from './drawing-submissions';
import { MetadataBadge, StatusBadge } from '@/components/portal/badges';
import { useFocusMode, AdvancedPanel } from '@/components/portal/workspace';
import { useWorkspaceSearch } from '@/lib/use-workspace-search';
import { scrollTutorTurnIntoView } from '@/lib/tutor-chat-scroll';
/* State effects synchronise API-loaded defaults with the session form. */
/* eslint-disable react/react-compiler */
import Image from 'next/image';
import {
  TutorChatAvatar,
  TutorAnswerBasis,
  TutorMessageContent,
  TutorTextbookEvidence,
  TutorTopicMatches,
} from './tutor-chat-elements';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowRightLeft,
  BookMarked,
  Compass,
  ExternalLink,
  MessageCircle,
  Send,
  Square,
  UserRound,
  Sparkles,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Empty, Heading } from '@/features/shared';
import { TutorSignals } from '@/features/tutor-signals';
import { TutorVoice } from '@/features/tutor-voice';
import { Equation, LearningImage } from '@/features/learning-media';
import {
  addTutorAgentTurn,
  endTutorSession,
  errorMessage,
  getTutorOptions,
  getTutorQuota,
  getTutorSessionOptions,
  getTutorCitationContext,
  getTutorPractice,
  getTutorPracticeHint,
  getTutorSessions,
  getNextTutorTopic,
  saveTutorPracticeAnswer,
  searchTutorSources,
  startTutorPractice,
  startTutorSession,
  submitTutorPractice,
  switchTutorProfile,
  switchTutorTopic,
  type NextTopicResult,
  type TutorCitationContext,
  type TutorAgentReply,
  type TutorOptions,
  type TutorPractice,
  type TutorQuota,
  type TutorSession,
  type TutorSessionOptions,
  type TutorSourceSearch,
} from '@/api';

const key = () => crypto.randomUUID();

export function TutorSessions({
  notify,
}: {
  notify: (message: string) => void;
}) {
  const [routeFilters] = useWorkspaceSearch({ record: '' });
  const [options, setOptions] = useState<TutorSessionOptions | null>(null);
  const [profileOptions, setProfileOptions] = useState<TutorOptions | null>(
    null,
  );
  const [session, setSession] = useState<TutorSession | null>(null);
  useFocusMode(Boolean(session));
  const [chatScope, setChatScope] = useState<'topic' | 'subject'>('topic');
  const [historySessions, setHistorySessions] = useState<TutorSession[]>([]);
  const [historyScope, setHistoryScope] = useState('all');
  const [subject, setSubject] = useState(''),
    [topic, setTopic] = useState(''),
    [profile, setProfile] = useState('');
  const [message, setMessage] = useState(''),
    [error, setError] = useState(''),
    [busy, setBusy] = useState(false);
  const [pendingMessage, setPendingMessage] = useState('');
  const [agentReply, setAgentReply] = useState<TutorAgentReply | null>(null);
  const [pastPaper, setPastPaper] = useState<PastPaperChatState | null>(null);
  const [practice, setPractice] = useState<TutorPractice | null>(null),
    [practiceAnswer, setPracticeAnswer] = useState('');
  const [nextTopic, setNextTopic] = useState<NextTopicResult | null>(null);
  const [sourceQuery, setSourceQuery] = useState(''),
    [sources, setSources] = useState<TutorSourceSearch | null>(null);
  const [quota, setQuota] = useState<TutorQuota | null>(null);
  const [expandedSource, setExpandedSource] =
    useState<TutorCitationContext | null>(null);
  const textInput = useRef<HTMLInputElement | null>(null);
  const latestTurnElement = useRef<HTMLElement | null>(null);
  const pendingTurnElement = useRef<HTMLDivElement | null>(null);
  const [toolAvailability, setToolAvailability] = useState({
    guidedPractice: false,
    voice: false,
    recommendations: false,
  });
  useEffect(() => {
    let cancelled = false;
    setToolAvailability({
      guidedPractice: false,
      voice: false,
      recommendations: false,
    });
    if (session?.status === 'active')
      void request<typeof toolAvailability>(
        `tutoring/sessions/${session.sessionRef}/tools`,
      )
        .then((value) => {
          if (!cancelled) setToolAvailability(value);
        })
        .catch(() => {
          /* Fail closed; ordinary text chat remains usable. */
        });
    return () => {
      cancelled = true;
    };
  }, [session?.sessionRef, session?.activeTopic.topicRef, session?.status]);
  const latestTurnRef = session?.turns.at(-1)?.turnRef;
  useEffect(() => {
    if (!latestTurnRef) return;
    // Wait for focus-mode layout to settle, then position each scroll container.
    // Typing, quota updates and other rerenders must not move the reader.
    let layoutFrame: number | undefined;
    const frame = window.requestAnimationFrame(() => {
      layoutFrame = window.requestAnimationFrame(() => {
        if (latestTurnElement.current)
          scrollTutorTurnIntoView(
            latestTurnElement.current,
            window.matchMedia('(prefers-reduced-motion: reduce)').matches,
          );
      });
    });
    return () => {
      window.cancelAnimationFrame(frame);
      if (layoutFrame !== undefined) window.cancelAnimationFrame(layoutFrame);
    };
  }, [latestTurnRef]);
  useEffect(() => {
    if (pendingMessage && pendingTurnElement.current)
      scrollTutorTurnIntoView(pendingTurnElement.current, true);
  }, [pendingMessage]);
  const load = useCallback(async () => {
    try {
      const [choices, profiles, sessions, allowance] = await Promise.all([
        getTutorSessionOptions(),
        getTutorOptions(),
        getTutorSessions(),
        getTutorQuota(),
      ]);
      setQuota(allowance);
      setOptions(choices);
      setProfileOptions(profiles);
      setHistorySessions(sessions.sessions);
      const active =
        sessions.sessions.find((item) => item.status === 'active') || null;
      setSession(active);
      const retained = active
        ? [...active.turns]
            .reverse()
            .find(
              (item) =>
                item.role === 'assistant' && item.structured?.operationRef,
            )
        : undefined;
      setAgentReply((retained?.structured as TutorAgentReply) || null);
      setPastPaper(null);
      if (active) {
        await request<PastPaperChatState | null>(
          `tutoring/sessions/${active.sessionRef}/past-paper`,
        )
          .then(setPastPaper)
          .catch(() => setPastPaper(null));
      }
      if (active) {
        const retainedPractice = await getTutorPractice(active.sessionRef);
        setPractice(retainedPractice);
        setPracticeAnswer(retainedPractice?.question.answer || '');
      }
      setSubject((current) => current || choices.subjects[0]?.id || '');
      setProfile(
        (current) =>
          choices.profiles.find(
            (item) => item.profileRef === routeFilters.record,
          )?.profileRef ||
          current ||
          choices.profiles[0]?.profileRef ||
          '',
      );
      setError('');
    } catch (cause) {
      setError(errorMessage(cause));
    }
  }, [routeFilters.record]);
  useEffect(() => {
    void load();
  }, [load]);
  const subjectChoice = useMemo(
    () => options?.subjects.find((item) => item.id === subject),
    [options, subject],
  );
  useEffect(() => {
    if (
      subjectChoice &&
      !subjectChoice.topics.some((item) => item.topicRef === topic)
    )
      setTopic(subjectChoice.topics[0]?.topicRef || '');
  }, [subjectChoice, topic]);
  const avatar = profileOptions?.avatars.find(
    (item) => item.code === session?.currentTutor.avatarCode,
  );
  const act = async (
    operation: () => Promise<TutorSession>,
    confirmation?: string,
  ) => {
    setBusy(true);
    setError('');
    try {
      const result = await operation();
      if (tutorLearningContextChanged(session, result)) {
        setPastPaper(null);
        setPractice(null);
        setPracticeAnswer('');
        setMessage('');
        setPendingMessage('');
        setSourceQuery('');
      }
      setSession(result.status === 'active' ? result : null);
      setHistorySessions((items) => [
        result,
        ...items.filter((s) => s.sessionRef !== result.sessionRef),
      ]);
      setNextTopic(null);
      setSources(null);
      setExpandedSource(null);
      setAgentReply(null);
      if (confirmation) notify(confirmation);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  };
  const refreshVoiceTranscript = useCallback(async () => {
    const [sessions, allowance] = await Promise.all([
      getTutorSessions(),
      getTutorQuota(),
    ]);
    setSession(
      (current) =>
        sessions.sessions.find(
          (item) => item.sessionRef === current?.sessionRef,
        ) || current,
    );
    setQuota(allowance);
  }, []);
  if (!options)
    return (
      <section className="panel stack">
        {error ? (
          <>
            <p className="error" role="alert">
              {error}
            </p>
            <Button onClick={() => void load()}>Try again</Button>
          </>
        ) : (
          <p>Loading AKURU Tutor…</p>
        )}
      </section>
    );
  if (!session)
    return (
      <div className="stack">
        <Heading eyebrow="STUDENT · PRACTICE" title="Start a tutor session">
          Choose Subject chat to explore across your available topics, or Topic
          chat for focused learning. Tutor help is available during practice
          only.{' '}
          {options.pilotMode &&
            'This text tutoring pilot includes the covered topics listed below.'}
        </Heading>
        {error && (
          <div className="error" role="alert">
            {error}
          </div>
        )}
        {quota && <QuotaSummary quota={quota} />}
        {!options.profiles.length ? (
          <Empty title="Create a tutor first">
            Go to My tutors and build an AKURU tutor profile.
          </Empty>
        ) : !options.subjects.length ? (
          <Empty title="No covered topics available">
            Ask your parent or administrator to check your enrolment and
            curriculum coverage.
          </Empty>
        ) : (
          <form
            className="panel stack tutor-session-start"
            onSubmit={(event) => {
              event.preventDefault();
              void act(
                () =>
                  startTutorSession(subject, topic, profile, key(), chatScope),
                'Tutor session started.',
              );
            }}
          >
            <fieldset className="tutor-choice stack">
              <legend>Chat scope</legend>
              <div className="button-row">
                {(['topic', 'subject'] as const).map((scope) => (
                  <label key={scope} data-selected={chatScope === scope}>
                    <input
                      type="radio"
                      name="chat-scope"
                      value={scope}
                      checked={chatScope === scope}
                      onChange={() => setChatScope(scope)}
                    />
                    <span>
                      {scope === 'topic' ? 'Topic chat' : 'Subject chat'}
                    </span>
                  </label>
                ))}
              </div>
              <small>
                {chatScope === 'subject'
                  ? 'Ask across the published, covered topics released for you in this subject. AKURU retrieves relevant passages; it does not send the whole textbook.'
                  : 'Focus on one selected topic. You can move topics during this conversation.'}
              </small>
            </fieldset>
            <label className="stack">
              <span>Subject</span>
              <select
                value={subject}
                onChange={(event) => setSubject(event.target.value)}
              >
                {options.subjects.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            {chatScope === 'topic' && (
              <label className="stack">
                <span>Covered topic</span>
                <select
                  value={topic}
                  onChange={(event) => setTopic(event.target.value)}
                >
                  {subjectChoice?.topics.map((item) => (
                    <option key={item.topicRef} value={item.topicRef}>
                      {item.groupCode} · {item.code} · {item.title}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <label className="stack">
              <span>Tutor</span>
              <select
                value={profile}
                onChange={(event) => setProfile(event.target.value)}
              >
                {options.profiles.map((item) => (
                  <option key={item.profileRef} value={item.profileRef}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <Button
              className="primary"
              type="submit"
              disabled={
                busy ||
                (chatScope === 'topic' && !topic) ||
                !subject ||
                !profile
              }
            >
              <MessageCircle size={16} />
              {busy ? 'Starting…' : 'Enter tutor room'}
            </Button>
          </form>
        )}
        {!!historySessions.length && (
          <section className="panel stack">
            <h2>Your previous conversations</h2>
            <label>
              Session type{' '}
              <select
                value={historyScope}
                onChange={(e) => setHistoryScope(e.target.value)}
              >
                <option value="all">All chats</option>
                <option value="subject">Subject chat</option>
                <option value="topic">Topic chat</option>
              </select>
            </label>
            {historySessions
              .filter(
                (s) =>
                  historyScope === 'all' ||
                  (s.chatScope || 'topic') === historyScope,
              )
              .slice(0, 30)
              .map((s) => (
                <details key={s.sessionRef} className="card">
                  <summary>
                    {s.subjectId.toUpperCase()} ·{' '}
                    {s.chatScope === 'subject'
                      ? 'Subject chat'
                      : `Topic chat · ${s.activeTopic.title}`}{' '}
                    · {new Date(s.startedAt).toLocaleDateString()} · {s.status}
                  </summary>
                  {s.turns.map((turn) => (
                    <article key={turn.turnRef} className="stack">
                      <strong>
                        {turn.role === 'student' ? 'You' : 'AKURU'}
                      </strong>
                      <TutorMessageContent content={turn.content} />
                    </article>
                  ))}
                  {!s.turns.length && <p>No messages in this session.</p>}
                </details>
              ))}
          </section>
        )}
      </div>
    );
  const topics =
    options.subjects.find((item) => item.id === session.subjectId)?.topics ||
    [];
  const activeLabel =
    session.chatScope === 'subject'
      ? `${session.subjectId.toUpperCase()} · Subject chat`
      : `${session.activeTopic.groupCode} · ${session.activeTopic.code} · ${session.activeTopic.title}`;
  const tutorName = session.currentTutor.name;
  return (
    <div className="stack tutor-room-page">
      <Heading
        eyebrow="STUDENT · TUTOR ROOM"
        title={`${session.currentTutor.name} is helping you`}
        action={
          <Button
            variant="outline"
            disabled={busy}
            onClick={() =>
              void act(
                () => endTutorSession(session.sessionRef, key()),
                'Tutor session ended.',
              )
            }
          >
            <Square size={14} />
            End session
          </Button>
        }
      >
        Your transcript stays together when you change tutors or move to another
        covered topic.
      </Heading>
      {error && (
        <div className="error" role="alert">
          {error}
        </div>
      )}
      {quota && <QuotaSummary quota={quota} />}
      <section className="panel tutor-room-header">
        <TutorChatAvatar
          key={avatar?.code || 'default'}
          src={avatar?.imagePath}
          name={tutorName}
          size={64}
        />
        <div>
          <MetadataBadge>{session.subjectId.toUpperCase()}</MetadataBadge>
          <h2>{activeLabel}</h2>
          <p>
            {session.chatScope === 'subject'
              ? 'Subject chat across your released topics'
              : 'Topic chat'}{' '}
            · Practice only · Tutor profile version{' '}
            {session.currentTutor.version}
          </p>
        </div>
        <div className="tutor-room-controls">
          <label>
            <span>Switch tutor</span>
            <select
              value={session.currentTutor.profileRef}
              disabled={busy}
              onChange={(event) =>
                void act(
                  () =>
                    switchTutorProfile(
                      session.sessionRef,
                      event.target.value,
                      key(),
                    ),
                  'Tutor switched. Your conversation was retained.',
                )
              }
            >
              {options.profiles.map((item) => (
                <option key={item.profileRef} value={item.profileRef}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          {session.chatScope !== 'subject' && (
            <label>
              <span>Move topic</span>
              <select
                value={session.activeTopic.topicRef}
                disabled={busy}
                onChange={(event) =>
                  void act(
                    () =>
                      switchTutorTopic(
                        session.sessionRef,
                        event.target.value,
                        key(),
                      ),
                    'Active topic changed.',
                  )
                }
              >
                {topics.map((item) => (
                  <option key={item.topicRef} value={item.topicRef}>
                    {item.groupCode} · {item.code} · {item.title}
                  </option>
                ))}
              </select>
            </label>
          )}
        </div>
      </section>
      <section
        className="panel tutor-transcript tutor-chat-shell"
        aria-label="Tutor transcript"
      >
        <header className="tutor-chat-header">
          <TutorChatAvatar
            key={avatar?.code || 'default'}
            src={avatar?.imagePath}
            name={tutorName}
            size={44}
          />
          <div className="tutor-chat-heading">
            <h2>{tutorName}</h2>
            <p>
              AI study companion ·{' '}
              {session.chatScope === 'subject'
                ? 'Subject chat'
                : session.activeTopic.title}
            </p>
          </div>
          <span className="tutor-chat-status">
            <span aria-hidden="true" />
            {pendingMessage ? 'Thinking…' : 'Ready to help'}
          </span>
        </header>
        {!session.turns.length && !pendingMessage ? (
          <Empty title="Ask your first question">
            AKURU will retain this message with the tutor version that received
            it.
          </Empty>
        ) : (
          <div
            className="tutor-turn-list"
            aria-label="Conversation messages"
            // Keyboard users must be able to scroll the bounded conversation.
            // oxlint-disable-next-line jsx-a11y/no-noninteractive-tabindex
            tabIndex={0}
          >
            <div className="tutor-chat-session-label">
              <span>Learning together</span>
            </div>
            {session.turns.map((turn) => {
              const turnProfile = options.profiles.find(
                (item) => item.profileRef === turn.profileRef,
              );
              const turnName = turnProfile?.name || 'AKURU Tutor';
              const turnAvatar = profileOptions?.avatars.find(
                (item) => item.code === turnProfile?.avatarCode,
              );
              const date = new Date(turn.createdAt);
              const hasTime = !Number.isNaN(date.getTime());
              return (
                <article
                  key={turn.turnRef}
                  className={`tutor-turn ${turn.role}`}
                  ref={
                    turn.turnRef === latestTurnRef
                      ? latestTurnElement
                      : undefined
                  }
                  style={{ scrollMarginBlockStart: '6rem' }}
                >
                  {turn.role === 'student' ? (
                    <span className="tutor-student-avatar" aria-hidden="true">
                      <UserRound size={19} />
                    </span>
                  ) : (
                    <TutorChatAvatar
                      key={turnAvatar?.code || 'default'}
                      src={turnAvatar?.imagePath}
                      name={turnName}
                      size={34}
                    />
                  )}
                  <div className="tutor-message-body">
                    <div className="tutor-message-meta">
                      <strong>
                        {turn.role === 'student' ? 'You' : turnName}
                      </strong>
                      {hasTime && (
                        <time dateTime={turn.createdAt}>
                          {date.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </time>
                      )}
                    </div>
                    <div className="tutor-message-bubble">
                      {turn.role === 'assistant' && (
                        <TutorAnswerBasis
                          basis={
                            turn.structured?.answerBasis as string | undefined
                          }
                        />
                      )}
                      <TutorMessageContent
                        content={turn.content}
                        formatted={turn.role === 'assistant'}
                      />
                    </div>
                    <small className="tutor-message-provenance">
                      {turn.modality === 'voice'
                        ? 'Voice transcript'
                        : turn.role === 'assistant'
                          ? turn.structured?.model === 'approved-exam-tools-v1'
                            ? 'Reviewed exam tools'
                            : 'AI tutor'
                          : 'You'}{' '}
                      · tutor version {turn.profileVersion}
                    </small>
                  </div>
                </article>
              );
            })}
            {pendingMessage && (
              <div ref={pendingTurnElement} className="tutor-pending-turn">
                <article className="tutor-turn student">
                  <span className="tutor-student-avatar" aria-hidden="true">
                    <UserRound size={19} />
                  </span>
                  <div className="tutor-message-body">
                    <div className="tutor-message-meta">
                      <strong>You</strong>
                    </div>
                    <div className="tutor-message-bubble">
                      <TutorMessageContent
                        content={pendingMessage}
                        formatted={false}
                      />
                    </div>
                    <small className="tutor-message-provenance">
                      Sending to your tutor…
                    </small>
                  </div>
                </article>
                <output className="tutor-typing" aria-live="polite">
                  <Sparkles size={16} aria-hidden="true" />
                  {tutorName} is preparing a reply
                  <span className="tutor-typing-dots" aria-hidden="true">
                    <i />
                    <i />
                    <i />
                  </span>
                </output>
              </div>
            )}
          </div>
        )}
        {agentReply && (
          <div className="tutor-chat-extras">
            <TutorTopicMatches
              matches={agentReply.topicMatches || []}
              activeTopicRef={session.activeTopic.topicRef}
              busy={busy}
              onOpen={(topicRef) =>
                void act(
                  () => switchTutorTopic(session.sessionRef, topicRef, key()),
                  'Active topic changed.',
                )
              }
            />
            <TutorTextbookEvidence
              key={agentReply.turnRef}
              sourceCount={agentReply.citations.length}
              visualCount={agentReply.visuals.length}
            >
              {agentReply.citations.map((citation) => (
                <a
                  className="citation-link"
                  key={citation.citationRef}
                  href={citation.assetUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  <BookMarked size={14} />
                  {citation.textbookTitle} · {citation.pageReference}
                </a>
              ))}
              {agentReply.visuals.map((visual) => (
                <TutorVisualAid
                  visual={visual}
                  key={`${visual.visualType}:${visual.contentUrl || visual.title}`}
                />
              ))}
            </TutorTextbookEvidence>
            {!!agentReply.followUpChoices.length && (
              <div className="follow-up-choices">
                <span className="tutor-follow-up-label">Try a follow-up</span>
                {agentReply.followUpChoices.map((choice) => (
                  <button
                    type="button"
                    key={choice}
                    disabled={busy}
                    onClick={() => {
                      setMessage(choice);
                      textInput.current?.focus();
                    }}
                  >
                    {choice}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        {pastPaper && (
          <TutorPastPaperCard
            value={pastPaper}
            busy={busy}
            refresh={() => {
              void request<PastPaperChatState | null>(
                `tutoring/sessions/${session.sessionRef}/past-paper`,
              )
                .then(setPastPaper)
                .catch((cause) => setError(errorMessage(cause)));
            }}
          />
        )}
        <div className="tutor-chat-compose-area">
          <small>
            Ask naturally: “Explain this”, “Quiz me”, or “Help me revise”. AKURU
            adapts the approach to your request.
          </small>
          <form
            className="tutor-composer tutor-chat-composer"
            onSubmit={async (event) => {
              event.preventDefault();
              const content = message.trim();
              if (!content || busy) return;
              setPendingMessage(content);
              setBusy(true);
              setError('');
              try {
                const reply = await addTutorAgentTurn(
                  session.sessionRef,
                  content,
                  'auto',
                  key(),
                );
                setAgentReply(reply);
                if (reply.pastPaper) setPastPaper(reply.pastPaper);
                setMessage('');
                const [refreshed, allowance] = await Promise.all([
                  getTutorSessions(),
                  getTutorQuota(),
                ]);
                setSession(
                  refreshed.sessions.find(
                    (item) => item.sessionRef === session.sessionRef,
                  ) || session,
                );
                setQuota(allowance);
              } catch (cause) {
                setError(errorMessage(cause));
              } finally {
                setPendingMessage('');
                setBusy(false);
              }
            }}
          >
            <Input
              ref={textInput}
              aria-label="Message your tutor"
              placeholder="Ask your tutor a question…"
              disabled={busy}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              maxLength={8000}
            />
            <Button
              className="primary"
              type="submit"
              disabled={busy || !message.trim()}
            >
              <Send size={16} />
              Send
            </Button>
          </form>
          <small className="tutor-chat-privacy">
            Textbook references support the textbook-labelled sections.
            Additional explanations, when enabled, are labelled separately.
            Proposed tutor observations do not change mastery or your study
            plan.
          </small>
        </div>
      </section>
      <TutorSignals refreshKey={agentReply?.turnRef} />
      {options.pilotMode && (
        <output className="panel">
          Text tutoring pilot: explanations, revision and approved textbook
          figures are available. Other tools appear only when released and usable
          for your account. Ask “How can you help me?” to see your available
          learning activities.
        </output>
      )}
      <AdvancedPanel title="Sources, guided practice and session tools">
        {session.chatScope === 'subject' &&
          (toolAvailability.guidedPractice || toolAvailability.voice) && (
            <section className="panel stack">
              <label>
                <span>
                  {toolAvailability.guidedPractice && toolAvailability.voice
                    ? 'Topic for practice and voice'
                    : toolAvailability.voice
                      ? 'Topic for voice'
                      : 'Topic for guided practice'}
                </span>
                <select
                  value={session.activeTopic.topicRef}
                  disabled={busy}
                  onChange={(event) =>
                    void act(
                      () =>
                        switchTutorTopic(
                          session.sessionRef,
                          event.target.value,
                          key(),
                        ),
                      'Tool focus changed. Your text chat remains subject-wide.',
                    )
                  }
                >
                  {topics.map((item) => (
                    <option key={item.topicRef} value={item.topicRef}>
                      {item.groupCode} · {item.code} · {item.title}
                    </option>
                  ))}
                </select>
              </label>
              <small>
                This selects the topic for these tools only. Your text
                conversation stays subject-wide.
              </small>
            </section>
          )}{' '}
        <section className="panel stack tutor-next-topic">
          <div className="panel-heading">
            <div>
              <MetadataBadge>
                <Compass size={13} /> EVIDENCE-BASED
              </MetadataBadge>
              <h2>What should I improve next?</h2>
            </div>
            <Button
              variant="outline"
              disabled={busy || !toolAvailability.recommendations}
              onClick={async () => {
                setBusy(true);
                setError('');
                try {
                  setNextTopic(
                    await getNextTutorTopic(
                      session.sessionRef,
                      session.subjectId,
                      key(),
                    ),
                  );
                } catch (cause) {
                  setError(errorMessage(cause));
                } finally {
                  setBusy(false);
                }
              }}
            >
              <Compass size={15} />
              Find next topic
            </Button>
          </div>
          {nextTopic &&
            (nextTopic.status !== 'ready' || !nextTopic.recommendation ? (
              <p>{nextTopic.message}</p>
            ) : (
              <article className="card stack">
                <div>
                  <MetadataBadge>PRIORITY TOPIC</MetadataBadge>
                  <h3>{`${nextTopic.recommendation.topic.groupCode} · ${nextTopic.recommendation.topic.code} · ${nextTopic.recommendation.topic.title}`}</h3>
                </div>
                <p>{nextTopic.recommendation.reason}</p>
                <div>
                  <strong>{nextTopic.recommendation.activity.title}</strong>
                  <p>{nextTopic.recommendation.activity.instruction}</p>
                  <small>
                    Success:{' '}
                    {nextTopic.recommendation.activity.successCondition}
                  </small>
                </div>
                <Button
                  className="primary"
                  disabled={
                    busy ||
                    nextTopic.recommendation.topic.topicRef ===
                      session.activeTopic.topicRef
                  }
                  onClick={() =>
                    void act(
                      () =>
                        switchTutorTopic(
                          session.sessionRef,
                          nextTopic.recommendation!.topic.topicRef,
                          key(),
                        ),
                      'Moved to the recommended topic.',
                    )
                  }
                >
                  <ArrowRightLeft size={15} />
                  Move to this topic
                </Button>
              </article>
            ))}
        </section>
        <section className="panel stack tutor-sources">
          <div className="panel-heading">
            <div>
              <MetadataBadge>
                <BookMarked size={13} /> APPROVED TEXTBOOK
              </MetadataBadge>
              <h2>Find an exact explanation</h2>
            </div>
          </div>
          <form
            className="tutor-composer"
            onSubmit={async (event) => {
              event.preventDefault();
              if (!sourceQuery.trim()) return;
              setBusy(true);
              setError('');
              setExpandedSource(null);
              try {
                setSources(
                  await searchTutorSources(
                    session.sessionRef,
                    sourceQuery.trim(),
                  ),
                );
              } catch (cause) {
                setError(errorMessage(cause));
              } finally {
                setBusy(false);
              }
            }}
          >
            <Input
              aria-label="Search the approved textbook"
              placeholder="What would you like explained?"
              value={sourceQuery}
              onChange={(event) => setSourceQuery(event.target.value)}
              maxLength={2000}
            />
            <Button
              className="primary"
              type="submit"
              disabled={busy || sourceQuery.trim().length < 2}
            >
              <BookMarked size={15} />
              Find source
            </Button>
          </form>
          {sources && sources.status !== 'exact' && <p>{sources.message}</p>}
          {sources?.citations.map((citation) => (
            <article
              className="card stack tutor-citation"
              key={citation.citationRef}
            >
              <div className="panel-heading">
                <div>
                  <MetadataBadge>
                    {citation.contentKind.toUpperCase()}
                  </MetadataBadge>
                  <h3>
                    {citation.textbookTitle} · {citation.pageReference}
                  </h3>
                  <small>
                    {citation.textbookEdition} · document version{' '}
                    {citation.documentVersion} · confidence{' '}
                    {Math.round(citation.confidence * 100)}%
                  </small>
                </div>
              </div>
              <blockquote>{citation.passage}</blockquote>
              <div className="button-row">
                <a
                  className="citation-link"
                  href={citation.assetUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  <ExternalLink size={14} />
                  Open cited page or crop
                </a>
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    try {
                      setExpandedSource(
                        await getTutorCitationContext(
                          session.sessionRef,
                          citation.citationRef,
                        ),
                      );
                    } catch (cause) {
                      setError(errorMessage(cause));
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  Show nearby context
                </Button>
              </div>
              {expandedSource?.citation.citationRef ===
                citation.citationRef && (
                <div className="source-nearby">
                  <strong>Nearby approved passages</strong>
                  {expandedSource.nearbyPassages.map((item) => (
                    <p key={item.citationRef}>
                      <span>{item.pageReference}:</span> {item.passage}
                    </p>
                  ))}
                </div>
              )}
            </article>
          ))}
          <small>
            AKURU names a page only when it finds an authorized passage in your
            {session.chatScope === 'subject'
              ? 'authorised subject topics'
              : 'current topic'}{' '}
            and published textbook edition.
          </small>
        </section>
        <section className="panel stack tutor-guided-practice">
          <div className="panel-heading">
            <div>
              <MetadataBadge>GUIDED PRACTICE</MetadataBadge>
              <h2>Practise one eligible question</h2>
            </div>
            {!practice || practice.status === 'submitted' ? (
              <Button
                className="primary"
                disabled={busy || !toolAvailability.guidedPractice}
                onClick={async () => {
                  setBusy(true);
                  setError('');
                  try {
                    const value = await startTutorPractice(
                      session.sessionRef,
                      key(),
                    );
                    setPractice(value);
                    setPracticeAnswer(value.question.answer);
                  } catch (cause) {
                    setError(errorMessage(cause));
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Start practice
              </Button>
            ) : null}
          </div>
          {practice && (
            <article className="card stack">
              <div>
                <span className="eyebrow">
                  {practice.groupCode} · {practice.topicCode} · QUESTION{' '}
                  {practice.question.number} · {practice.question.marks} MARKS
                </span>
                <h3>{practice.question.prompt}</h3>
                {practice.question.sharedStem && (
                  <p>{practice.question.sharedStem}</p>
                )}
              </div>
              {practice.assetUrls.map((url, index) => (
                <Image
                  unoptimized
                  width={640}
                  height={400}
                  src={url}
                  alt={`Question diagram ${index + 1}`}
                  key={url}
                />
              ))}
              <DrawingSubmissions
                assessmentId={practice.assessmentId}
                questionId={practice.question.id}
                parts={practice.question.drawingParts}
                files={practice.question.drawingFiles}
                disabled={busy || practice.status !== 'active'}
                onSaved={async () =>
                  setPractice(await getTutorPractice(session.sessionRef))
                }
              />
              {practice.status === 'active' &&
                practice.question.generatedWorkedAnswerAvailable && (
                  <PracticeWorkedAnswer
                    key={practice.question.id}
                    assessmentId={practice.assessmentId}
                    questionId={practice.question.id}
                  />
                )}
              {practice.status === 'submitted' && (
                <ModelAnswerVisuals
                  assessmentId={practice.assessmentId}
                  questionId={practice.question.id}
                  visuals={practice.question.rubric?.answerVisuals}
                />
              )}
              {practice.status === 'active' ? (
                <>
                  <label className="stack">
                    <span>Your answer</span>
                    <textarea
                      rows={5}
                      value={practiceAnswer}
                      onChange={(event) =>
                        setPracticeAnswer(event.target.value)
                      }
                    />
                  </label>
                  {practice.latestHint && (
                    <p className="source-note">
                      <strong>Hint {practice.hintCount}:</strong>{' '}
                      {practice.latestHint}
                    </p>
                  )}
                  <div className="button-row">
                    <Button
                      variant="outline"
                      disabled={busy}
                      onClick={async () => {
                        setBusy(true);
                        try {
                          setPractice(
                            await getTutorPracticeHint(
                              session.sessionRef,
                              key(),
                            ),
                          );
                        } catch (cause) {
                          setError(errorMessage(cause));
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      Get next hint
                    </Button>
                    <Button
                      variant="outline"
                      disabled={busy}
                      onClick={async () => {
                        setBusy(true);
                        try {
                          setPractice(
                            await saveTutorPracticeAnswer(
                              session.sessionRef,
                              practiceAnswer,
                              key(),
                            ),
                          );
                          notify('Practice answer saved.');
                        } catch (cause) {
                          setError(errorMessage(cause));
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      Save answer
                    </Button>
                    <Button
                      className="primary"
                      disabled={busy}
                      onClick={async () => {
                        setBusy(true);
                        setError('');
                        try {
                          await saveTutorPracticeAnswer(
                            session.sessionRef,
                            practiceAnswer,
                            key(),
                          );
                          setPractice(
                            await submitTutorPractice(
                              session.sessionRef,
                              key(),
                            ),
                          );
                          notify('Practice submitted and assessed.');
                        } catch (cause) {
                          setError(errorMessage(cause));
                        } finally {
                          setBusy(false);
                        }
                      }}
                    >
                      Submit for assessment
                    </Button>
                  </div>
                  <small>
                    You can switch tutors without losing this question. Submit
                    it before moving to another topic.
                  </small>
                </>
              ) : practice.question.result ? (
                <div className="practice-feedback stack">
                  <div className="spread">
                    <h3>Authoritative AKURU assessment</h3>
                    <strong>
                      {practice.question.result.awardedMarks}/
                      {practice.question.result.maxMarks}
                    </strong>
                  </div>
                  <h4>How each mark was decided</h4>
                  {practice.question.result.markingDecisions.map((decision) => (
                    <p className="source-note" key={decision.pointId}>
                      <strong>
                        {decision.creditState === 'matched_capped'
                          ? 'Correct · mark limit reached'
                          : decision.creditState === 'not_required'
                            ? 'Optional · not required'
                            : decision.awarded
                              ? 'Awarded'
                              : 'Not awarded'}
                        :
                      </strong>{' '}
                      {decision.rationale}
                      <br />
                      <small>Your evidence: {decision.studentEvidence}</small>
                    </p>
                  ))}
                  {!!practice.question.result.smallMistakes.length && (
                    <p>
                      <strong>Small improvements:</strong>{' '}
                      {practice.question.result.smallMistakes.join(' ')}
                    </p>
                  )}
                  <p>
                    <strong>Improved answer:</strong>{' '}
                    {practice.question.result.improvedAnswer}
                  </p>
                  <p>
                    <strong>Explanation:</strong>{' '}
                    {practice.question.result.teachingExplanation}
                  </p>
                </div>
              ) : (
                <p>
                  Assessment feedback is awaiting the permitted review workflow.
                </p>
              )}
            </article>
          )}
          {!practice && (
            <p>
              Start a question selected deterministically from this covered
              topic.
            </p>
          )}
        </section>
        {toolAvailability.voice && (
          <TutorVoice
            sessionRef={session.sessionRef}
            subjectId={session.subjectId}
            profileIdentity={`${session.currentTutor.profileRef}:${session.currentTutor.version}`}
            disabled={
              options.pilotMode ||
              !quota ||
              !quota.enabled ||
              quota.voiceMinutes.remaining <= 0
            }
            notify={notify}
            onTranscript={refreshVoiceTranscript}
            focusText={() => textInput.current?.focus()}
          />
        )}
      </AdvancedPanel>
    </div>
  );
}

function QuotaSummary({ quota }: { quota: TutorQuota }) {
  return (
    <section
      className={`panel quota-summary quota-${quota.state}`}
      aria-label="Tutor allowance"
    >
      <div>
        <StatusBadge
          status={quota.state}
          label={quota.state[0].toUpperCase() + quota.state.slice(1)}
        />
        <strong>{quota.requests.remaining} tutor requests remaining</strong>
      </div>
      <p>
        {quota.textTokens.remaining.toLocaleString()} text tokens ·{' '}
        {quota.voiceMinutes.remaining} voice minutes remaining
      </p>
      <small>
        {quota.fallbackMessage} Renews{' '}
        {new Date(quota.renewsAt).toLocaleDateString()}.
      </small>
    </section>
  );
}

function TutorVisualAid({
  visual,
}: {
  visual: TutorAgentReply['visuals'][number];
}) {
  const official = visual.visualType === 'official_source';
  // Only protected, reauthorised stored-asset endpoints can become chat images.
  if (
    visual.contentUrl &&
    !/^\/api\/v1\/tutoring\/sessions\/[a-zA-Z0-9_-]+\/(?:approved-visuals|media)\/[a-f0-9-]+$/.test(
      visual.contentUrl,
    )
  )
    return null;
  return (
    <article
      className={`tutor-visual tutor-visual-${visual.visualType}`}
      aria-label={`${official ? 'Official source visual' : 'Explanatory visual'}: ${visual.title}`}
    >
      <header>
        <MetadataBadge>
          {official ? 'OFFICIAL SOURCE' : 'EXPLANATORY AID'}
        </MetadataBadge>
        <h3>{visual.title}</h3>
      </header>
      {visual.equation ? (
        <Equation value={visual.equation} />
      ) : visual.contentUrl ? (
        <LearningImage
          src={visual.contentUrl}
          description={visual.altText}
          title={visual.title}
        />
      ) : null}
      <p className="visual-fallback">
        <strong>Text alternative:</strong> {visual.readableFallback}
      </p>
      <small>
        {visual.sourceLabel}.{' '}
        {official
          ? 'Use this as source evidence.'
          : 'This supports understanding and does not replace the official source.'}
      </small>
      <details>
        <summary>Asset provenance</summary>
        <dl>
          {Object.entries(visual.provenance)
            .filter(([, value]) => value !== null && value !== '')
            .map(([name, value]) => (
              <div key={name}>
                <dt>{name}</dt>
                <dd>{formatProvenance(value)}</dd>
              </div>
            ))}
        </dl>
      </details>
    </article>
  );
}

function formatProvenance(value: unknown) {
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean')
    return value.toString();
  return JSON.stringify(value);
}
