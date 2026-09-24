'use client';
import { useEffect, useMemo, useState } from 'react';
import { BookOpen, CheckCircle2, Layers3, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Heading, Empty, Status } from './shared';
import { errorMessage, generateFlashcardDeck, getAdminFlashcardDeck, getAdminFlashcardDecks,
  getStudentFlashcardDecks, getTextbookStructures, rateFlashcard, releaseFlashcardDeck,
  revealFlashcard, reviewFlashcard, startFlashcardSession, type FlashcardDeck,
  type FlashcardSession } from '@/api';

export function FlashcardAdmin({ notify }: { notify: (message: string) => void }) {
  const [decks, setDecks] = useState<FlashcardDeck[]>([]);
  const [deck, setDeck] = useState<FlashcardDeck | null>(null);
  const [topics, setTopics] = useState<{ value: string; label: string }[]>([]);
  const [topicRef, setTopicRef] = useState('');
  const [limit, setLimit] = useState('12');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function load() { setDecks(await getAdminFlashcardDecks()); }
  useEffect(() => {
    void Promise.all([getAdminFlashcardDecks(), getTextbookStructures()]).then(([rows, books]) => {
      setDecks(rows);
      const available = books.textbooks.flatMap(book => book.groups.flatMap(group => group.topics
        .filter(topic => topic.status === 'published' && topic.content.contentVersion > 0)
        .map(topic => ({ value: topic.topicRef, label: `${book.subjectId.toUpperCase()} · ${group.code} · ${topic.code} ${topic.title}` }))));
      setTopics(available); setTopicRef(available[0]?.value || '');
    }).catch(cause => setError(errorMessage(cause)));
  }, []);
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
      Create grounded drafts from one published topic, check every card, then release it to eligible Students.
    </Heading>
    {error && <div className="error" role="alert">{error}</div>}
    <section className="panel stack">
      <h2>Create a draft deck</h2>
      <p>AKURU uses the topic’s current published content version and exact textbook passages. A passing retrieval preflight is required.</p>
      <label htmlFor="flashcard-topic">Published topic</label>
        <select id="flashcard-topic" value={topicRef} onChange={event => setTopicRef(event.target.value)}>
          <option value="">Select a topic</option>
          {topics.map(topic => <option key={topic.value} value={topic.value}>{topic.label}</option>)}
        </select>
      <label htmlFor="flashcard-limit">Maximum cards</label><Input id="flashcard-limit" type="number" min="3" max="40" value={limit} onChange={event => setLimit(event.target.value)} />
      <Button className="primary" disabled={busy || !topicRef}
        onClick={() => void act(() => generateFlashcardDeck(topicRef, Number(limit), crypto.randomUUID()), 'Flashcard draft created for review.')}>
        Generate grounded draft
      </Button>
    </section>
    <section className="panel stack"><h2>Decks</h2>
      {decks.length ? decks.map(row => <button className="attempt-row" key={row.deckRef} onClick={() => void open(row.deckRef)}>
        <div><strong>{row.title}</strong><p>{row.groupCode} · {row.topicCode} · content version {row.contentVersion}</p></div>
        <Status status={row.status}/><span>{row.approvedCount}/{row.cardCount} approved</span>
      </button>) : <Empty title="No flashcard decks yet">Choose a published topic above to prepare the first draft.</Empty>}
    </section>
    {deck && <section className="panel stack" aria-live="polite">
      <div className="spread"><div><h2>{deck.title}</h2><p>{deck.groupTitle} · {deck.topicCode} {deck.topicTitle}</p></div><Status status={deck.status}/></div>
      <div className="flashcard-stats"><strong>{deck.cardCount} cards</strong><span>{deck.approvedCount} approved</span><span>{deck.reviewRequiredCount} need review</span><span>{deck.rejectedCount} rejected</span></div>
      {deck.cards.map(card => <FlashcardEditor key={card.cardRef} card={card} disabled={busy || deck.status === 'released'}
        save={(front, back, decision) => act(() => reviewFlashcard(deck.deckRef, card.cardRef, front, back, decision), decision === 'approved' ? 'Card approved.' : 'Card review saved.')} />)}
      {deck.status !== 'released' && <Button className="primary" disabled={busy || deck.cardCount < 3 || deck.approvedCount !== deck.cardCount}
        onClick={() => void act(() => releaseFlashcardDeck(deck.deckRef), 'Flashcards released to eligible Students.')}>Release approved deck</Button>}
    </section>}
  </>;
}

function FlashcardEditor({ card, save, disabled }: { card: FlashcardDeck['cards'][number]; save: (front: string, back: string, decision: 'review_required'|'approved'|'rejected') => Promise<void>; disabled: boolean }) {
  const [front, setFront] = useState(card.front), [back, setBack] = useState(card.back || '');
  return <article className="flashcard-editor">
    <div className="spread"><strong>Card {card.ordinal}</strong><Status status={card.status}/></div>
    <label htmlFor={`front-${card.cardRef}`}>Question</label><Textarea id={`front-${card.cardRef}`} value={front} onChange={event => setFront(event.target.value)} disabled={disabled}/>
    <label htmlFor={`back-${card.cardRef}`}>Best answer</label><Textarea id={`back-${card.cardRef}`} value={back} onChange={event => setBack(event.target.value)} disabled={disabled}/>
    <details><summary>Exact textbook evidence · page {card.source.printedPage || card.source.page}</summary><blockquote>{card.source.passage}</blockquote><small>{card.source.documentTitle}</small></details>
    {!!card.warnings.length && <div className="source-note">{card.warnings.join(' ')}</div>}
    {!disabled && <div className="button-row"><Button variant="outline" onClick={() => void save(front, back, 'review_required')}>Save for later</Button><Button variant="outline" onClick={() => void save(front, back, 'rejected')}>Reject</Button><Button className="primary" onClick={() => void save(front, back, 'approved')}><CheckCircle2 size={16}/>Approve card</Button></div>}
  </article>;
}

export function StudentFlashcards() {
  const [decks, setDecks] = useState<FlashcardDeck[]>([]);
  const [session, setSession] = useState<FlashcardSession | null>(null);
  const [error, setError] = useState(''), [busy, setBusy] = useState(false), [announcement, setAnnouncement] = useState('');
  useEffect(() => { void getStudentFlashcardDecks().then(setDecks).catch(cause => setError(errorMessage(cause))); }, []);
  const progress = useMemo(() => session ? Math.round(100 * session.reviewedCount / Math.max(1, session.totalCards)) : 0, [session]);
  async function run(action: () => Promise<FlashcardSession>) {
    setBusy(true); setError('');
    try { const next = await action(); setSession(next); setAnnouncement(next.message); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  }
  return <>
    <Heading eyebrow="STUDENT · ACTIVE RECALL" title="Flashcards">Remember ideas by trying the answer first, then compare it with the approved textbook answer.</Heading>
    {error && <div className="error" role="alert">{error}</div>}<p className="sr-only" aria-live="polite">{announcement}</p>
    {!session && <div className="topic-list">
      {decks.map(deck => <button className="panel topic-row" key={deck.deckRef} disabled={busy}
        onClick={() => void run(() => startFlashcardSession(deck.deckRef, crypto.randomUUID()))}>
        <span className="topic-number"><Layers3/></span><div><span className="eyebrow">{deck.subjectId} · {deck.groupCode}</span><h3>{deck.title}</h3><p>{deck.cardCount} approved cards · textbook content version {deck.contentVersion}</p></div><BookOpen/>
      </button>)}
      {!decks.length && <Empty title="No flashcards are ready yet">Your Admin must release a deck for a topic included in your grade and term coverage.</Empty>}
    </div>}
    {session && <section className="flashcard-study panel">
      <div className="spread"><span>Card {Math.min(session.reviewedCount + 1, session.totalCards)} of {session.totalCards}</span><strong>{progress}% complete</strong></div>
      <progress value={session.reviewedCount} max={session.totalCards} aria-label={`${progress}% complete`}/>
      {session.status === 'completed' ? <div className="flashcard-finished"><CheckCircle2 size={48}/><h2>Session complete</h2><p>{session.message}</p><Button onClick={() => setSession(null)}><RotateCcw size={16}/>Choose another deck</Button></div>
      : session.currentCard && <><fieldset className="flashcard-face"><legend className="sr-only">Current flashcard</legend><span className="eyebrow">QUESTION</span><h2>{session.currentCard.front}</h2>
        {session.answerRevealed && <div className="flashcard-answer"><span className="eyebrow">APPROVED ANSWER</span><p>{session.currentCard.back}</p><details><summary>Open exact textbook source</summary><blockquote>{session.currentCard.source.passage}</blockquote>{session.currentCard.source.sourceUrl && <a href={session.currentCard.source.sourceUrl} target="_blank" rel="noreferrer">View source details · page {session.currentCard.source.printedPage || session.currentCard.source.page}</a>}</details></div>}
      </fieldset>
      {!session.answerRevealed ? <Button className="primary" disabled={busy} onClick={() => void run(() => revealFlashcard(session.sessionRef))}>Show approved answer</Button>
      : <fieldset className="rating-buttons"><legend>How well did you remember it?</legend>{([['again','Again'],['difficult','Difficult'],['good','Good'],['easy','Easy']] as const).map(([value,label]) => <Button key={value} variant={value === 'good' ? 'default' : 'outline'} disabled={busy} onClick={() => void run(() => rateFlashcard(session.sessionRef, value, crypto.randomUUID()))}>{label}</Button>)}</fieldset>}</>}
    </section>}
  </>;
}
