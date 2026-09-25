'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertTriangle, BarChart3, BookOpen, CheckCircle2, ChevronLeft, ChevronRight, Flag, Layers3, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Heading, Empty, Status } from './shared';
import { LearningImage } from './learning-media';
import { decideFlashcardReport, discardFlashcardSession, errorMessage, getAdminFlashcardDeck, getAdminFlashcardDecks, getFlashcardMastery, getFlashcardReports, getFlashcardSession, getFlashcardStudyOptions,
  getStudentFlashcardDecks, rateFlashcard, reportFlashcard, revealFlashcard, startFlashcardSession,
  withdrawFlashcardDeck, type FlashcardDeck, type FlashcardDifficulty, type FlashcardMode, type FlashcardRating, type FlashcardSession,
  type FlashcardStudyOption, type FlashcardReport } from '@/api';
import { queryKeys } from '@/lib/query-keys';
import { flashcardPaths, type FlashcardRoute } from '@/lib/routes';

const protectedAssetCache = new Map<string, Promise<string>>();
const protectedAssetUrls = new Map<string, string>();
const compactUnits = (value: string | null | undefined) => String(value ?? '').replace(/(\d(?:[\d.,]*))\s+(kg|mg|g|μg|µg|cm³|cm3|dm³|dm3|m³|m3|cm²|cm2|mm|cm|dm|km|mL|ml|L|mol|°C)\b/g, '$1$2');
function MasteryRing({ value, label }: { value: number; label: string }) { const colour = value >= 90 ? '#166534' : value >= 70 ? '#65a30d' : value >= 40 ? '#d97706' : '#dc2626'; return <div className="mastery-ring-item"><div className="mastery-ring" aria-label={`${label}: ${value}% mastery`} style={{background: `conic-gradient(${colour} ${value}%, #e5e7eb 0)`}}><span>{value}%</span></div><strong>{label}</strong></div>; }

function clearProtectedAssets(sessionRef?: string) {
  for (const [key, url] of protectedAssetUrls) {
    if (!sessionRef || key.startsWith(`${sessionRef}:`)) {
      URL.revokeObjectURL(url); protectedAssetUrls.delete(key); protectedAssetCache.delete(key);
    }
  }
}

async function protectedAsset(sessionRef: string, sourceUrl: string) {
  const key = `${sessionRef}:${sourceUrl}`;
  const cached = protectedAssetCache.get(key);
  if (cached) return cached;
  const pending = fetch(sourceUrl, { credentials: 'same-origin', cache: 'no-store' }).then(async response => {
    if (!response.ok) throw new Error('The textbook source could not be opened.');
    const objectUrl = URL.createObjectURL(await response.blob());
    protectedAssetUrls.set(key, objectUrl);
    return objectUrl;
  }).catch(error => { protectedAssetCache.delete(key); throw error; });
  protectedAssetCache.set(key, pending);
  return pending;
}

function ProtectedLearningImage({ sessionRef, src, description, title }: { sessionRef: string; src: string; description: string; title: string }) {
  const [localUrl, setLocalUrl] = useState(protectedAssetUrls.get(`${sessionRef}:${src}`) ?? '');
  const [loadError, setLoadError] = useState('');
  useEffect(() => {
    let live = true;
    void protectedAsset(sessionRef, src).then(url => { if (live) setLocalUrl(url); }).catch(error => { if (live) setLoadError(errorMessage(error)); });
    return () => { live = false; };
  }, [sessionRef, src]);
  if (loadError) return <p className="error" role="alert">{loadError}</p>;
  if (!localUrl) return <p className="small" aria-live="polite">Loading approved textbook figure…</p>;
  return <LearningImage src={localUrl} description={description} title={title}/>;
}

function ProtectedSourceLink({ sessionRef, src, label }: { sessionRef: string; src: string; label: string }) {
  const [busy, setBusy] = useState(false), [loadError, setLoadError] = useState('');
  async function open() {
    setBusy(true); setLoadError('');
    try { window.open(await protectedAsset(sessionRef, src), '_blank', 'noopener,noreferrer'); }
    catch (error) { setLoadError(errorMessage(error)); }
    finally { setBusy(false); }
  }
  return <div><Button type="button" variant="outline" disabled={busy} onClick={() => void open()}>{busy ? 'Opening textbook page…' : label}</Button>{loadError && <p className="error" role="alert">{loadError}</p>}</div>;
}

function pageLabel(value: string | number | undefined) {
  const text = String(value ?? '').trim();
  return /[,–-]/.test(text) ? `Page Numbers ${text.replace(/\s*,\s*/g, '–')}` : `Page Number ${text}`;
}

export function FlashcardAdmin({ notify }: { notify: (message: string) => void }) {
  const [decks, setDecks] = useState<FlashcardDeck[]>([]);
  const [deck, setDeck] = useState<FlashcardDeck | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [withdrawReason, setWithdrawReason] = useState('');
  const [reports, setReports] = useState<FlashcardReport[]>([]);
  async function load() { setDecks(await getAdminFlashcardDecks()); }
  useEffect(() => { void Promise.all([getAdminFlashcardDecks(), getFlashcardReports()]).then(([nextDecks,nextReports]) => { setDecks(nextDecks); setReports(nextReports); }).catch(cause => setError(errorMessage(cause))); }, []);
  async function decide(reportRef: string, decision: 'exclude'|'restore') { setBusy(true); setError(''); try { await decideFlashcardReport(reportRef, decision); setReports(await getFlashcardReports()); await load(); notify(decision === 'exclude' ? 'Flashcard excluded.' : 'Flashcard restored to Student decks.'); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }
  async function open(ref: string) {
    setError('');
    try { setDeck(await getAdminFlashcardDeck(ref)); } catch (cause) { setError(errorMessage(cause)); }
  }
  async function act(action: () => Promise<FlashcardDeck>, message: string) {
    setBusy(true); setError('');
    try { const next = await action(); setDeck(next); await load(); notify(message); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  }
  return <>
    <Heading eyebrow="ADMIN · REVIEWED LEARNING" title="Flashcard release desk">
      Inspect validated flashcard releases prepared from published textbook content and withdraw a release when necessary.
    </Heading>
    {error && <div className="error" role="alert">{error}</div>}
    <section className="panel stack">
      <h2>Curated releases</h2>
      <p>AKURU flashcards are prepared as reviewed, source-grounded release packages. Student study does not generate cards or consume AI tokens.</p>
    </section>
    <section className="panel stack"><h2>Reported flashcards</h2><p>Reported cards stop appearing for every Student immediately. Restore a suitable card or keep it excluded.</p>{reports.length ? reports.map(report => <article className="flashcard-editor" key={report.reportRef}><div className="spread"><Status status={report.status}/><span>{new Date(report.createdAt).toLocaleDateString()}</span></div><h3>{compactUnits(report.question)}</h3><p><strong>Student reason:</strong> {report.reason}</p><div className="button-row"><Button disabled={busy || report.availability === 'excluded'} onClick={() => void decide(report.reportRef, 'exclude')}>Exclude from deck</Button><Button variant="outline" disabled={busy || report.availability === 'active'} onClick={() => void decide(report.reportRef, 'restore')}>Add back to deck</Button></div></article>) : <Empty title="No reported flashcards">Student reports will appear here for review.</Empty>}</section>
    <section className="panel stack"><h2>Decks</h2>
      {decks.length ? decks.map(row => <button className="attempt-row" key={row.deckRef} onClick={() => void open(row.deckRef)}>
        <div><strong>{row.title}</strong><p>{row.groupCode} · {row.topicCode} · content version {row.contentVersion}</p></div>
        <Status status={row.status}/><span>{row.cardCount} validated cards</span>
      </button>) : <Empty title="No flashcard releases yet">A reviewed release package can be validated and imported by the AKURU release process.</Empty>}
    </section>
    {deck && <section className="panel stack" aria-live="polite">
      <div className="spread"><div><h2>{deck.title}</h2><p>{deck.groupTitle} · {deck.topicCode} {deck.topicTitle}</p></div><Status status={deck.status}/></div>
      <div className="flashcard-stats"><strong>{deck.cardCount} cards</strong><span>{deck.approvedCount} approved</span><span>Validation: {deck.validationStatus || 'legacy'}</span><span>Release: {deck.releaseId || 'legacy pilot'}</span></div>
      {!!Object.keys(deck.categoryDistribution || {}).length && <div className="flashcard-stats">{Object.entries(deck.categoryDistribution).map(([key, count]) => <span key={key}>{key.replaceAll('_', ' ')}: {count}</span>)}</div>}
      {!!Object.keys(deck.validationSummary || {}).length && <details><summary>Validation and coverage report</summary><pre>{JSON.stringify(deck.validationSummary, null, 2)}</pre></details>}
      {deck.cards.map(card => <article className="flashcard-editor" key={card.cardRef}>
        <div className="spread"><strong>Card {card.ordinal} · {card.category.replaceAll('_', ' ')}</strong><Status status={card.status}/></div>
        <h3>{compactUnits(card.front)}</h3><p>{compactUnits(card.back)}</p>
        <details><summary>Exact textbook evidence · page {card.source.printedPage || card.source.page}</summary><blockquote>{card.source.passage}</blockquote></details>
      </article>)}
      {deck.status === 'released' && <div className="stack"><label htmlFor="withdraw-reason">Reason for withdrawal</label><input id="withdraw-reason" value={withdrawReason} onChange={event => setWithdrawReason(event.target.value)} placeholder="Explain why Students should no longer see this release"/><Button variant="outline" disabled={busy || withdrawReason.trim().length < 5} onClick={() => void act(() => withdrawFlashcardDeck(deck.deckRef, withdrawReason), 'Flashcard release withdrawn.')}>Withdraw release</Button></div>}
    </section>}
  </>;
}

export function StudentFlashcards({ actorRef, route, navigate }: {
  actorRef: string;
  route: FlashcardRoute;
  navigate: (to: string) => void;
}) {
  const cache = useQueryClient();
  const [error, setError] = useState(''), [busy, setBusy] = useState(false), [announcement, setAnnouncement] = useState('');
  const [difficulty, setDifficulty] = useState<FlashcardDifficulty>('mixed');
  const [requestedCount, setRequestedCount] = useState<20 | 30>(20);
  const [explanationCardRef, setExplanationCardRef] = useState<string | null>(null);
  const [sourceOpenByCard, setSourceOpenByCard] = useState<Record<string, boolean>>({});
  const [reportOpen, setReportOpen] = useState(false), [reportReason, setReportReason] = useState('');
  const [pendingExit, setPendingExit] = useState<{to: string; proceed: () => void} | null>(null);
  const bypassExitGuard = useRef(false);
  const decksQuery = useQuery({ queryKey: queryKeys.flashcards.studentDecks(actorRef), queryFn: getStudentFlashcardDecks });
  const decks = decksQuery.data ?? [];
  const selectedDeck = route.deckRef ? decks.find(deck => deck.deckRef === route.deckRef) ?? null : null;
  const optionsQuery = useQuery({ queryKey: queryKeys.flashcards.studyOptions(actorRef, route.deckRef ?? ''), queryFn: () => getFlashcardStudyOptions(route.deckRef!), enabled: Boolean(route.deckRef) });
  const masteryQuery = useQuery({ queryKey: queryKeys.flashcards.mastery(actorRef, route.deckRef ?? ''), queryFn: () => getFlashcardMastery(route.deckRef!), enabled: Boolean(route.deckRef) });
  const options: FlashcardStudyOption[] = optionsQuery.data?.options ?? [];
  const sessionQuery = useQuery({ queryKey: queryKeys.flashcards.session(actorRef, route.sessionRef ?? '', route.position), queryFn: () => getFlashcardSession(route.sessionRef!, route.position), enabled: Boolean(route.sessionRef), staleTime: 0 });
  const session = sessionQuery.data ?? null;
  const queryError = decksQuery.error ?? optionsQuery.error ?? masteryQuery.error ?? sessionQuery.error;
  const visibleError = error || (queryError ? errorMessage(queryError) : '');
  const progress = useMemo(() => session ? Math.round(100 * session.reviewedCount / Math.max(1, session.totalCards)) : 0, [session]);
  const uncommitted = Boolean(session?.hasUncommittedResults && session.status === 'active');

  useEffect(() => {
    const ref = session?.sessionRef;
    if (!ref) return;
    if (session.status === 'completed') clearProtectedAssets(ref);
    return () => clearProtectedAssets(ref);
  }, [session?.sessionRef, session?.status]);
  useEffect(() => {
    if (!uncommitted) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [uncommitted]);
  useEffect(() => {
    const guard = (rawEvent: Event) => {
      const event = rawEvent as CustomEvent<{to: string; proceed: () => void}>;
      if (!uncommitted || bypassExitGuard.current || event.detail?.to.startsWith(`/flashcards/sessions/${session?.sessionRef}/`)) return;
      event.preventDefault(); setPendingExit(event.detail ?? {to: flashcardPaths.library, proceed: () => navigate(flashcardPaths.library)});
    };
    window.addEventListener('akuru:before-navigation', guard);
    return () => window.removeEventListener('akuru:before-navigation', guard);
  }, [uncommitted, session?.sessionRef, navigate]);

  async function run(action: () => Promise<FlashcardSession>) {
    setBusy(true); setError('');
    try {
      const next = await action();
      setExplanationCardRef(null);
      cache.setQueryData(queryKeys.flashcards.session(actorRef, next.sessionRef, next.viewedOrdinal), next);
      setAnnouncement(next.message); navigate(flashcardPaths.card(next.sessionRef, next.viewedOrdinal));
      if (next.status === 'completed') { clearProtectedAssets(next.sessionRef); await cache.invalidateQueries({ queryKey: queryKeys.flashcards.all(actorRef) }); }
    } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); }
  }
  function begin(mode: FlashcardMode) {
    if (!selectedDeck) return;
    const chosenDifficulty = mode === 'review' ? difficulty : null;
    navigate(flashcardPaths.start(selectedDeck.deckRef, mode, chosenDifficulty ?? undefined, requestedCount));
    void run(() => startFlashcardSession(selectedDeck.deckRef, mode, chosenDifficulty, requestedCount, crypto.randomUUID()));
  }
  function requestExit(to: string) { if (uncommitted) setPendingExit({to, proceed: () => navigate(to)}); else navigate(to); }
  async function confirmDiscard() {
    if (!session || !pendingExit) return;
    setBusy(true); setError('');
    try {
      const result = await discardFlashcardSession(session.sessionRef);
      clearProtectedAssets(session.sessionRef);
      cache.removeQueries({ queryKey: queryKeys.flashcards.session(actorRef, session.sessionRef) });
      const proceed = pendingExit.proceed; bypassExitGuard.current = true; setPendingExit(null); setAnnouncement(result.message); proceed();
    } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); }
  }
  async function confirmReport() { if (!session) return; setBusy(true); setError(''); try { await reportFlashcard(session.sessionRef, reportReason); setReportOpen(false); setReportReason(''); setAnnouncement('Flashcard reported and removed for all Students.'); await cache.invalidateQueries({ queryKey: queryKeys.flashcards.all(actorRef) }); if (session.totalCards <= 1) navigate(flashcardPaths.deck(session.deck.deckRef)); else navigate(flashcardPaths.card(session.sessionRef, Math.min(session.viewedOrdinal, session.totalCards - 1))); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }
  function openPosition(position: number) { if (session) { setExplanationCardRef(null); navigate(flashcardPaths.card(session.sessionRef, position)); } }
  const mastery = masteryQuery.data;
  const paragraphs = session?.currentCard?.source.paragraphs?.length ? session.currentCard.source.paragraphs : session?.currentCard?.source.passage ? [session.currentCard.source.passage] : [];
  const sourceOpen = Boolean(session?.currentCard && sourceOpenByCard[session.currentCard.cardRef]);
  const explanationOpen = Boolean(session?.currentCard && explanationCardRef === session.currentCard.cardRef);
  return <>
    <Heading eyebrow="STUDENT · ACTIVE RECALL" title="Flashcards">Complete a set to update your personal mastery. Incomplete attempts never change your ranking.</Heading>
    {visibleError && <div className="error" role="alert">{visibleError}</div>}<p className="sr-only" aria-live="polite">{announcement}</p>
    {!session && !route.deckRef && !route.sessionRef && <div className="topic-list">
      {decks.map(deck => <button className="panel topic-row" key={deck.deckRef} disabled={busy} onClick={() => navigate(flashcardPaths.deck(deck.deckRef))}><span className="topic-number"><Layers3/></span><div><span className="eyebrow">{deck.subjectId} · {deck.groupCode}</span><h3>{deck.title}</h3><p>{deck.cardCount} approved cards · textbook content version {deck.contentVersion}</p></div><BookOpen/></button>)}
      {!decksQuery.isPending && !decks.length && <Empty title="No flashcards are ready yet">Your Admin must release a deck for a topic included in your grade and term coverage.</Empty>}
    </div>}
    {!session && route.deckRef && !selectedDeck && !decksQuery.isPending && !visibleError && <Empty title="Flashcard deck unavailable">This deck may have been removed or is not available to this Student.</Empty>}
    {!session && selectedDeck && <section className="panel stack"><div className="spread"><div><span className="eyebrow">CHOOSE YOUR REVIEW</span><h2>{selectedDeck.title}</h2></div><Button variant="outline" onClick={() => navigate(flashcardPaths.library)}>Back to topics</Button></div>
      {mastery && <section className="flashcard-mastery" aria-labelledby="mastery-title"><div className="spread"><h3 id="mastery-title"><BarChart3 size={18}/> Your mastery</h3><MasteryRing value={mastery.masteryPercent} label="Overall"/></div><div className="flashcard-stats"><span>Mastered: {mastery.mastered}</span><span>Good: {mastery.good}</span><span>Needs review: {mastery.needsReview}</span><span>To evaluate: {mastery.toEvaluate}</span></div><p className="small">Coverage {mastery.coveragePercent}% · {mastery.completedSessions} completed set{mastery.completedSessions === 1 ? '' : 's'}</p><p><strong>Recommended next:</strong> {mastery.recommendedMode === 'difficult' ? 'Difficult Flashcards' : `${mastery.recommendedDifficulty ?? 'mixed'} Review Flashcards`} · {mastery.recommendedCount} cards</p><div className="mastery-categories">{mastery.categories.map(item => <MasteryRing key={item.category} value={item.masteryPercent} label={`${item.category.replaceAll('_',' ')} · ${item.coveragePercent}% evaluated`}/>)}</div>{mastery.recentSessions.length > 0 && <details><summary>Recent completed sets</summary><ul>{mastery.recentSessions.map(item => <li key={item.sessionRef}>{new Date(item.completedAt).toLocaleDateString()} · {item.mode === 'review' ? 'Review' : 'Difficult'} · {item.cardCount} cards</li>)}</ul></details>}</section>}
      <fieldset className="flashcard-choice"><legend>Number of flashcards</legend>{([20,30] as const).map(count => <Button key={count} type="button" variant={requestedCount === count ? 'default' : 'outline'} aria-pressed={requestedCount === count} onClick={() => setRequestedCount(count)}>{count} cards</Button>)}</fieldset>
      <div className="topic-list">{options.map(option => <article className="panel stack" key={option.mode}><div><h3>{option.title}</h3><p>{option.description}</p><small>{option.availableCount} available</small></div>{option.mode === 'review' && <fieldset className="flashcard-choice"><legend>Card difficulty</legend>{(['easy','difficult','mixed'] as const).map(value => <Button type="button" key={value} variant={difficulty === value ? 'default' : 'outline'} aria-pressed={difficulty === value} onClick={() => setDifficulty(value)}>{value[0].toUpperCase()+value.slice(1)}</Button>)}</fieldset>}<Button disabled={busy || !option.enabled} onClick={() => begin(option.mode)}>Start {option.title}</Button></article>)}</div>
    </section>}
    {!session && route.sessionRef && sessionQuery.isPending && <section className="panel stack" aria-live="polite"><h2>Opening your Flashcard session…</h2><p>AKURU is restoring your current card.</p></section>}
    {session && <section className="flashcard-study panel"><div className="spread"><span>{session.mode === 'review' ? 'Review Flashcards' : 'Difficult Flashcards'} · Card {session.viewedOrdinal} of {session.totalCards}</span><strong>{progress}% attempted</strong></div><progress value={session.reviewedCount} max={session.totalCards} aria-label={`${progress}% attempted`}/>
      {session.status === 'completed' ? <div className="flashcard-finished"><CheckCircle2 size={48}/><h2>Session complete</h2><p>{session.message}</p><Button onClick={() => navigate(flashcardPaths.deck(session.deck.deckRef))}><RotateCcw size={16}/>View mastery and start another set</Button></div> : session.currentCard && <><nav className="flashcard-card-navigation" aria-label="Cards in this set"><Button variant="outline" disabled={!session.canGoPrevious || busy} onClick={() => openPosition(session.viewedOrdinal - 1)}><ChevronLeft size={16}/>Previous attempted card</Button><span>First unattempted card: {session.firstUnattemptedOrdinal}</span><Button variant="outline" disabled={!session.canGoNext || busy} onClick={() => openPosition(session.viewedOrdinal + 1)}>Next attempted card<ChevronRight size={16}/></Button></nav>
        <fieldset className="flashcard-face"><legend className="sr-only">Current flashcard</legend><span className="eyebrow">QUESTION</span><h2>{compactUnits(session.currentCard.front)}</h2>{session.answerRevealed && <div className="flashcard-answer stack"><section className="approved-answer"><span className="eyebrow">APPROVED ANSWER</span><p>{compactUnits(session.currentCard.back)}</p></section>{session.currentCard.explanation && <section className="answer-explanation"><Button type="button" variant="outline" aria-expanded={explanationOpen} onClick={() => setExplanationCardRef(explanationOpen ? null : session.currentCard!.cardRef)}>{explanationOpen ? 'Hide explanation' : 'Show explanation'}</Button>{explanationOpen && <div><h3>Explanation</h3><p>{compactUnits(session.currentCard.explanation)}</p></div>}</section>}{session.currentCard.source.visual && <div className="stack"><p><strong>{session.currentCard.source.visual.caption || 'Textbook figure'}</strong></p><ProtectedLearningImage sessionRef={session.sessionRef} src={session.currentCard.source.visual.contentUrl} description={session.currentCard.source.visual.altText} title={session.currentCard.source.visual.caption || 'Textbook figure'}/></div>}<section className="textbook-source"><Button type="button" variant="outline" aria-expanded={sourceOpen} aria-controls={`source-${session.currentCard.cardRef}`} onClick={() => setSourceOpenByCard(current => ({...current, [session.currentCard!.cardRef]: !sourceOpen}))}>{sourceOpen ? 'Hide exact textbook source' : 'Open exact textbook source'}</Button>{sourceOpen && <div id={`source-${session.currentCard.cardRef}`}><div className="source-identity"><strong>{session.currentCard.source.documentTitle}</strong><span>{pageLabel(session.currentCard.source.printedPage || session.currentCard.source.page)}</span></div><blockquote>{paragraphs.map((paragraph,index) => <p key={index}>{compactUnits(paragraph)}</p>)}</blockquote>{session.currentCard.source.textbookPageUrl && <ProtectedSourceLink sessionRef={session.sessionRef} src={session.currentCard.source.textbookPageUrl} label={`View matching textbook ${pageLabel(session.currentCard.source.printedPage || session.currentCard.source.page).toLowerCase()}`}/>}</div>}</section></div>}</fieldset>
        {!session.answerRevealed ? <Button className="primary" disabled={busy || session.currentCard.attempted} onClick={() => void run(() => revealFlashcard(session.sessionRef))}>Show approved answer</Button> : session.currentCard.attempted ? <p className="saved-rating"><CheckCircle2 size={18}/> You selected <strong>{session.currentCard.selectedRating}</strong>. This rating cannot be changed.</p> : <fieldset className="rating-buttons"><legend>How well did you remember it? Choose one to continue.</legend>{([['again','Again'],['difficult','Difficult'],['good','Good'],['easy','Easy']] as const satisfies readonly (readonly [FlashcardRating,string])[]).map(([value,label]) => <Button key={value} variant="outline" disabled={busy} onClick={() => void run(() => rateFlashcard(session.sessionRef, value, crypto.randomUUID()))}>{label}</Button>)}</fieldset>}<Button variant="outline" disabled={busy} onClick={() => setReportOpen(true)}><Flag size={16}/>Report this flashcard</Button><Button variant="ghost" disabled={busy} onClick={() => requestExit(flashcardPaths.deck(session.deck.deckRef))}>Exit this set</Button></>}
    </section>}

    {reportOpen && session?.currentCard && <div className="modal-backdrop" role="presentation"><dialog className="confirm-dialog" open aria-labelledby="report-title"><Flag size={32}/><h2 id="report-title">Report this flashcard?</h2><p>Confirming will immediately remove this card from every Student deck while an Admin reviews it.</p><label className="stack"><strong>What is unclear or incorrect?</strong><textarea rows={4} value={reportReason} onChange={event => setReportReason(event.target.value)} placeholder="Describe the problem with this question, answer or explanation"/></label><div className="button-row"><Button variant="outline" onClick={() => { setReportOpen(false); setReportReason(''); }}>Cancel</Button><Button disabled={busy || reportReason.trim().length < 5} onClick={() => void confirmReport()}>Confirm report</Button></div></dialog></div>}
    {pendingExit && <div className="modal-backdrop" role="presentation"><dialog className="confirm-dialog" open aria-labelledby="discard-title"><AlertTriangle size={32}/><h2 id="discard-title">Discard this flashcard attempt?</h2><p>Mastery is recorded only after every card is completed. Leaving now will discard this incomplete attempt and its provisional ratings. Earlier completed learning will not be deleted.</p><div className="button-row"><Button variant="outline" autoFocus onClick={() => setPendingExit(null)}>Continue studying</Button><Button disabled={busy} onClick={() => void confirmDiscard()}>Exit and discard attempt</Button></div></dialog></div>}
  </>;
}
