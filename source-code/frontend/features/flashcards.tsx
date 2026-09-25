'use client';
import { useEffect, useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { BookOpen, CheckCircle2, Layers3, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Heading, Empty, Status } from './shared';
import { LearningImage } from './learning-media';
import { errorMessage, getAdminFlashcardDeck, getAdminFlashcardDecks, getFlashcardSession, getFlashcardStudyOptions,
  getStudentFlashcardDecks, rateFlashcard, revealFlashcard, startFlashcardSession,
  withdrawFlashcardDeck, type FlashcardDeck, type FlashcardMode, type FlashcardSession,
  type FlashcardStudyOption } from '@/api';
import { queryKeys } from '@/lib/query-keys';
import { flashcardPaths, type FlashcardRoute } from '@/lib/routes';

export function FlashcardAdmin({ notify }: { notify: (message: string) => void }) {
  const [decks, setDecks] = useState<FlashcardDeck[]>([]);
  const [deck, setDeck] = useState<FlashcardDeck | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [withdrawReason, setWithdrawReason] = useState('');
  async function load() { setDecks(await getAdminFlashcardDecks()); }
  useEffect(() => { void getAdminFlashcardDecks().then(setDecks).catch(cause => setError(errorMessage(cause))); }, []);
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
        <h3>{card.front}</h3><p>{card.back}</p>
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
  const decksQuery = useQuery({
    queryKey: queryKeys.flashcards.studentDecks(actorRef),
    queryFn: getStudentFlashcardDecks,
  });
  const decks = decksQuery.data ?? [];
  const selectedDeck = route.deckRef ? decks.find(deck => deck.deckRef === route.deckRef) ?? null : null;
  const optionsQuery = useQuery({
    queryKey: queryKeys.flashcards.studyOptions(actorRef, route.deckRef ?? ''),
    queryFn: () => getFlashcardStudyOptions(route.deckRef!),
    enabled: Boolean(route.deckRef),
  });
  const options: FlashcardStudyOption[] = optionsQuery.data?.options ?? [];
  const studySummary = optionsQuery.data?.summary ?? {};
  const sessionQuery = useQuery({
    queryKey: queryKeys.flashcards.session(actorRef, route.sessionRef ?? ''),
    queryFn: () => getFlashcardSession(route.sessionRef!),
    enabled: Boolean(route.sessionRef),
    staleTime: 0,
  });
  const session = sessionQuery.data ?? null;
  const queryError = decksQuery.error ?? optionsQuery.error ?? sessionQuery.error;
  const visibleError = error || (queryError ? errorMessage(queryError) : '');
  useEffect(() => {
    if (session && route.position !== session.currentOrdinal)
      navigate(flashcardPaths.card(session.sessionRef, session.currentOrdinal));
  }, [session, route.position, navigate]);
  const progress = useMemo(() => session ? Math.round(100 * session.reviewedCount / Math.max(1, session.totalCards)) : 0, [session]);
  async function run(action: () => Promise<FlashcardSession>) {
    setBusy(true); setError('');
    try {
      const next = await action();
      cache.setQueryData(queryKeys.flashcards.session(actorRef, next.sessionRef), next);
      setAnnouncement(next.message);
      navigate(flashcardPaths.card(next.sessionRef, next.currentOrdinal));
    }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  }
  function begin(mode: FlashcardMode) {
    if (selectedDeck) {
      navigate(flashcardPaths.start(selectedDeck.deckRef, mode));
      void run(() => startFlashcardSession(selectedDeck.deckRef, mode, crypto.randomUUID()));
    }
  }
  return <>
    <Heading eyebrow="STUDENT · ACTIVE RECALL" title="Flashcards">Remember ideas by trying the answer first, then compare it with the approved textbook answer.</Heading>
    {visibleError && <div className="error" role="alert">{visibleError}</div>}<p className="sr-only" aria-live="polite">{announcement}</p>
    {!session && !route.deckRef && !route.sessionRef && <div className="topic-list">
      {decks.map(deck => <button className="panel topic-row" key={deck.deckRef} disabled={busy}
        onClick={() => navigate(flashcardPaths.deck(deck.deckRef))}>
        <span className="topic-number"><Layers3/></span><div><span className="eyebrow">{deck.subjectId} · {deck.groupCode}</span><h3>{deck.title}</h3><p>{deck.cardCount} approved cards · textbook content version {deck.contentVersion}</p></div><BookOpen/>
      </button>)}
      {!decksQuery.isPending && !decks.length && <Empty title="No flashcards are ready yet">Your Admin must release a deck for a topic included in your grade and term coverage.</Empty>}
    </div>}
    {!session && route.deckRef && !selectedDeck && !decksQuery.isPending && !visibleError && <Empty title="Flashcard deck unavailable">This deck may have been removed or is not available to this Student.</Empty>}
    {!session && selectedDeck && <section className="panel stack"><div className="spread"><div><span className="eyebrow">CHOOSE A STUDY MODE</span><h2>{selectedDeck.title}</h2></div><Button variant="outline" onClick={() => navigate(flashcardPaths.library)}>Back to topics</Button></div>
      {route.mode && <output>Ready to start {options.find(option => option.mode === route.mode)?.title ?? route.mode.replaceAll('_', ' ')}.</output>}
      <div className="flashcard-stats">{Object.entries(studySummary).map(([label, count]) => <span key={label}>{label}: {count}</span>)}</div>
      <div className="topic-list">{options.map(option => <button className="panel topic-row" key={option.mode} disabled={busy || !option.enabled} onClick={() => begin(option.mode)}><span className="topic-number"><Layers3/></span><div><h3>{option.title}</h3><p>{option.description}</p><small>{option.availableCount} available · {option.sessionSize} in this session</small></div><BookOpen/></button>)}</div>
    </section>}
    {!session && route.sessionRef && sessionQuery.isPending && <section className="panel stack" aria-live="polite"><h2>Opening your Flashcard session…</h2><p>AKURU is restoring your current card.</p></section>}
    {session && <section className="flashcard-study panel">
      <div className="spread"><span>{session.mode.replaceAll('_', ' ')} · Card {Math.min(session.reviewedCount + 1, session.totalCards)} of {session.totalCards}</span><strong>{progress}% complete</strong></div>
      <progress value={session.reviewedCount} max={session.totalCards} aria-label={`${progress}% complete`}/>
      {session.status === 'completed' ? <div className="flashcard-finished"><CheckCircle2 size={48}/><h2>Session complete</h2><p>{session.message}</p><Button onClick={() => navigate(flashcardPaths.library)}><RotateCcw size={16}/>Choose another deck</Button></div>
      : session.currentCard && <><fieldset className="flashcard-face"><legend className="sr-only">Current flashcard</legend><span className="eyebrow">QUESTION</span><h2>{session.currentCard.front}</h2>
        {session.answerRevealed && <div className="flashcard-answer"><span className="eyebrow">APPROVED ANSWER</span><p>{session.currentCard.back}</p>
          {session.currentCard.source.visual && <div className="stack"><p><strong>{session.currentCard.source.visual.caption || 'Textbook figure'}</strong></p><LearningImage src={session.currentCard.source.visual.contentUrl} description={session.currentCard.source.visual.altText} title={session.currentCard.source.visual.caption || 'Textbook figure'}/></div>}
          <details><summary>Open exact textbook source</summary><p className="small"><strong>{session.currentCard.source.documentTitle}</strong> · printed page {session.currentCard.source.printedPage || session.currentCard.source.page}</p><blockquote>{session.currentCard.source.passage}</blockquote>
            {session.currentCard.source.textbookPageUrl && <a href={session.currentCard.source.textbookPageUrl} target="_blank" rel="noreferrer">View matching textbook page {session.currentCard.source.printedPage || session.currentCard.source.page}</a>}
          </details>
        </div>}
      </fieldset>
      {!session.answerRevealed ? <Button className="primary" disabled={busy} onClick={() => void run(() => revealFlashcard(session.sessionRef))}>Show approved answer</Button>
      : <fieldset className="rating-buttons"><legend>How well did you remember it?</legend>{([['again','Again'],['difficult','Difficult'],['good','Good'],['easy','Easy']] as const).map(([value,label]) => <Button key={value} variant={value === 'good' ? 'default' : 'outline'} disabled={busy} onClick={() => void run(() => rateFlashcard(session.sessionRef, value, crypto.randomUUID()))}>{label}</Button>)}</fieldset>}</>}
    </section>}
  </>;
}
