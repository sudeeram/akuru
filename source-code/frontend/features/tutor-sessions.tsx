'use client';
/* State effects synchronise API-loaded defaults with the session form. */
/* eslint-disable react/react-compiler */
import Image from 'next/image';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowRightLeft, BookMarked, Compass, ExternalLink, MessageCircle, Send, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Empty, Heading } from '@/features/shared';
import {
  addTutorTurn, endTutorSession, errorMessage, getTutorOptions, getTutorSessionOptions,
  getTutorCitationContext, getTutorSessions, getNextTutorUnit, searchTutorSources, startTutorSession,
  switchTutorProfile, switchTutorUnit, type NextUnitResult, type TutorCitationContext,
  type TutorOptions, type TutorSession, type TutorSessionOptions, type TutorSourceSearch,
} from '@/lib/api';

const key = () => crypto.randomUUID();

export function TutorSessions({ notify }: { notify: (message: string) => void }) {
  const [options, setOptions] = useState<TutorSessionOptions | null>(null);
  const [profileOptions, setProfileOptions] = useState<TutorOptions | null>(null);
  const [session, setSession] = useState<TutorSession | null>(null);
  const [subject, setSubject] = useState(''), [unit, setUnit] = useState(''), [profile, setProfile] = useState('');
  const [message, setMessage] = useState(''), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const [nextUnit, setNextUnit] = useState<NextUnitResult | null>(null);
  const [sourceQuery, setSourceQuery] = useState(''), [sources, setSources] = useState<TutorSourceSearch | null>(null);
  const [expandedSource, setExpandedSource] = useState<TutorCitationContext | null>(null);
  const load = useCallback(async () => {
    try {
      const [choices, profiles, sessions] = await Promise.all([getTutorSessionOptions(), getTutorOptions(), getTutorSessions()]);
      setOptions(choices); setProfileOptions(profiles);
      const active = sessions.sessions.find((item) => item.status === 'active') || null;
      setSession(active);
      setSubject((current) => current || choices.subjects[0]?.id || '');
      setProfile((current) => current || choices.profiles[0]?.profileRef || '');
      setError('');
    } catch (cause) { setError(errorMessage(cause)); }
  }, []);
  useEffect(() => { void load(); }, [load]);
  const subjectChoice = useMemo(() => options?.subjects.find((item) => item.id === subject), [options, subject]);
  useEffect(() => { if (subjectChoice && !subjectChoice.units.some((item) => item.id === unit)) setUnit(subjectChoice.units[0]?.id || ''); }, [subjectChoice, unit]);
  const avatar = profileOptions?.avatars.find((item) => item.code === session?.currentTutor.avatarCode);
  const act = async (operation: () => Promise<TutorSession>, confirmation?: string) => {
    setBusy(true); setError('');
    try { const result = await operation(); setSession(result.status === 'active' ? result : null); setNextUnit(null); setSources(null); setExpandedSource(null); if (confirmation) notify(confirmation); }
    catch (cause) { setError(errorMessage(cause)); }
    finally { setBusy(false); }
  };
  if (!options) return <section className="panel">Loading AKURU Tutor…</section>;
  if (!session) return <div className="stack"><Heading eyebrow="STUDENT · PRACTICE" title="Start a tutor session">Choose one covered unit and one of your tutors. Tutor help is available during practice only.</Heading>
    {error && <div className="error" role="alert">{error}</div>}
    {!options.profiles.length ? <Empty title="Create a tutor first">Go to My tutors and build an AKURU tutor profile.</Empty> : !options.subjects.length ? <Empty title="No covered units available">Ask your parent or administrator to check your enrolment and curriculum coverage.</Empty> : <form className="panel stack tutor-session-start" onSubmit={(event) => { event.preventDefault(); void act(() => startTutorSession(subject, unit, profile, key()), 'Tutor session started.'); }}>
      <label className="stack"><span>Subject</span><select value={subject} onChange={(event) => setSubject(event.target.value)}>{options.subjects.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label className="stack"><span>Covered unit</span><select value={unit} onChange={(event) => setUnit(event.target.value)}>{subjectChoice?.units.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.title}</option>)}</select></label>
      <label className="stack"><span>Tutor</span><select value={profile} onChange={(event) => setProfile(event.target.value)}>{options.profiles.map((item) => <option key={item.profileRef} value={item.profileRef}>{item.name}</option>)}</select></label>
      <Button className="primary" type="submit" disabled={busy || !unit || !profile}><MessageCircle size={16} />{busy ? 'Starting…' : 'Enter tutor room'}</Button>
    </form>}
  </div>;
  const units = options.subjects.find((item) => item.id === session.subjectId)?.units || [];
  return <div className="stack"><Heading eyebrow="STUDENT · TUTOR ROOM" title={`${session.currentTutor.name} is helping you`} action={<Button variant="outline" disabled={busy} onClick={() => void act(() => endTutorSession(session.sessionRef, key()), 'Tutor session ended.')}><Square size={14} />End session</Button>}>Your transcript stays together when you change tutors or move to another covered unit.</Heading>
    {error && <div className="error" role="alert">{error}</div>}
    <section className="panel tutor-room-header">
      {avatar && <Image width={105} height={105} src={avatar.imagePath} alt={`${session.currentTutor.name} avatar`} />}
      <div><span className="pill">{session.subjectId.toUpperCase()}</span><h2>{session.activeUnit.code} · {session.activeUnit.title}</h2><p>Practice session · Tutor profile version {session.currentTutor.version}</p></div>
      <div className="tutor-room-controls">
        <label><span>Switch tutor</span><select value={session.currentTutor.profileRef} disabled={busy} onChange={(event) => void act(() => switchTutorProfile(session.sessionRef, event.target.value, key()), 'Tutor switched. Your conversation was retained.')}>{options.profiles.map((item) => <option key={item.profileRef} value={item.profileRef}>{item.name}</option>)}</select></label>
        <label><span>Move unit</span><select value={session.activeUnit.id} disabled={busy} onChange={(event) => void act(() => switchTutorUnit(session.sessionRef, event.target.value, key()), 'Active unit changed.')}>{units.map((item) => <option key={item.id} value={item.id}>{item.code} · {item.title}</option>)}</select></label>
      </div>
    </section>
    <section className="panel stack tutor-next-unit">
      <div className="panel-heading"><div><span className="pill"><Compass size={13} /> EVIDENCE-BASED</span><h2>What should I improve next?</h2></div><Button variant="outline" disabled={busy} onClick={async () => { setBusy(true); setError(''); try { setNextUnit(await getNextTutorUnit(session.sessionRef, session.subjectId, key())); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}><Compass size={15} />Find next unit</Button></div>
      {nextUnit && (nextUnit.status !== 'ready' || !nextUnit.recommendation ? <p>{nextUnit.message}</p> : <article className="card stack"><div><span className="pill">PRIORITY UNIT</span><h3>{nextUnit.recommendation.unit.code} · {nextUnit.recommendation.unit.title}</h3></div><p>{nextUnit.recommendation.reason}</p><div><strong>{nextUnit.recommendation.activity.title}</strong><p>{nextUnit.recommendation.activity.instruction}</p><small>Success: {nextUnit.recommendation.activity.successCondition}</small></div><Button className="primary" disabled={busy || nextUnit.recommendation.unit.id === session.activeUnit.id} onClick={() => void act(() => switchTutorUnit(session.sessionRef, nextUnit.recommendation!.unit.id, key()), 'Moved to the recommended unit.')}><ArrowRightLeft size={15} />{nextUnit.recommendation.unit.id === session.activeUnit.id ? 'Already studying this unit' : 'Move to this unit'}</Button></article>)}
    </section>
    <section className="panel stack tutor-sources">
      <div className="panel-heading"><div><span className="pill"><BookMarked size={13} /> APPROVED TEXTBOOK</span><h2>Find an exact explanation</h2></div></div>
      <form className="tutor-composer" onSubmit={async (event) => { event.preventDefault(); if (!sourceQuery.trim()) return; setBusy(true); setError(''); setExpandedSource(null); try { setSources(await searchTutorSources(session.sessionRef, sourceQuery.trim())); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>
        <Input aria-label="Search the approved textbook" placeholder="What would you like explained?" value={sourceQuery} onChange={(event) => setSourceQuery(event.target.value)} maxLength={2000} />
        <Button className="primary" type="submit" disabled={busy || sourceQuery.trim().length < 2}><BookMarked size={15} />Find source</Button>
      </form>
      {sources && sources.status !== 'exact' && <p>{sources.message}</p>}
      {sources?.citations.map((citation) => <article className="card stack tutor-citation" key={citation.citationRef}><div className="panel-heading"><div><span className="pill">{citation.contentKind.toUpperCase()}</span><h3>{citation.textbookTitle} · {citation.pageReference}</h3><small>{citation.textbookEdition} · document version {citation.documentVersion} · confidence {Math.round(citation.confidence * 100)}%</small></div></div><blockquote>{citation.passage}</blockquote><div className="button-row"><a className="citation-link" href={citation.assetUrl} target="_blank" rel="noreferrer"><ExternalLink size={14} />Open cited page or crop</a><Button variant="outline" disabled={busy} onClick={async () => { setBusy(true); try { setExpandedSource(await getTutorCitationContext(session.sessionRef, citation.citationRef)); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>Show nearby context</Button></div>{expandedSource?.citation.citationRef === citation.citationRef && <div className="source-nearby"><strong>Nearby approved passages</strong>{expandedSource.nearbyPassages.map((item) => <p key={item.citationRef}><span>{item.pageReference}:</span> {item.passage}</p>)}</div>}</article>)}
      <small>AKURU names a page only when it finds an authorized passage in your current unit and published textbook edition.</small>
    </section>
    <section className="panel stack tutor-transcript" aria-label="Tutor transcript">
      <div className="panel-heading"><div><span className="pill"><ArrowRightLeft size={13} /> CONTINUOUS HANDOVER</span><h2>Conversation</h2></div></div>
      {!session.turns.length ? <Empty title="Ask your first question">AKURU will retain this message with the tutor version that received it.</Empty> : <div className="tutor-turn-list">{session.turns.map((turn) => <article key={turn.turnRef} className={`tutor-turn ${turn.role}`}><strong>{turn.role === 'student' ? 'You' : session.currentTutor.name}</strong><p>{turn.content}</p><small>{turn.modality === 'voice' ? 'Voice transcript' : 'Text'} · tutor version {turn.profileVersion}</small></article>)}</div>}
      <form className="tutor-composer" onSubmit={(event) => { event.preventDefault(); const content = message.trim(); if (!content) return; void act(async () => { const result = await addTutorTurn(session.sessionRef, content, 'text', key()); setMessage(''); return result; }); }}>
        <Input aria-label="Message your tutor" placeholder="Ask about this unit…" value={message} onChange={(event) => setMessage(event.target.value)} maxLength={8000} />
        <Button className="primary" type="submit" disabled={busy || !message.trim()}><Send size={16} />Send</Button>
      </form>
      <small>Step 2 securely stores your conversation. AKURU-generated teaching replies are connected in Tutor Step 6.</small>
    </section>
  </div>;
}
