'use client';
/* State effects synchronise API-loaded defaults with the session form. */
/* eslint-disable react/react-compiler */
import Image from 'next/image';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowRightLeft, BookMarked, Compass, ExternalLink, MessageCircle, Send, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Empty, Heading } from '@/features/shared';
import { TutorSignals } from '@/features/tutor-signals';
import {
  addTutorAgentTurn, endTutorSession, errorMessage, getTutorOptions, getTutorSessionOptions,
  getTutorCitationContext, getTutorPractice, getTutorPracticeHint, getTutorSessions, getNextTutorUnit,
  saveTutorPracticeAnswer, searchTutorSources, startTutorPractice, startTutorSession, submitTutorPractice,
  switchTutorProfile, switchTutorUnit, type NextUnitResult, type TutorCitationContext,
  type TutorAgentReply, type TutorOptions, type TutorPractice, type TutorSession, type TutorSessionOptions, type TutorSourceSearch,
} from '@/lib/api';

const key = () => crypto.randomUUID();

export function TutorSessions({ notify }: { notify: (message: string) => void }) {
  const [options, setOptions] = useState<TutorSessionOptions | null>(null);
  const [profileOptions, setProfileOptions] = useState<TutorOptions | null>(null);
  const [session, setSession] = useState<TutorSession | null>(null);
  const [subject, setSubject] = useState(''), [unit, setUnit] = useState(''), [profile, setProfile] = useState('');
  const [message, setMessage] = useState(''), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const [teachingMode, setTeachingMode] = useState<TutorAgentReply['teachingMode']>('explanation');
  const [agentReply, setAgentReply] = useState<TutorAgentReply | null>(null);
  const [practice, setPractice] = useState<TutorPractice | null>(null), [practiceAnswer, setPracticeAnswer] = useState('');
  const [nextUnit, setNextUnit] = useState<NextUnitResult | null>(null);
  const [sourceQuery, setSourceQuery] = useState(''), [sources, setSources] = useState<TutorSourceSearch | null>(null);
  const [expandedSource, setExpandedSource] = useState<TutorCitationContext | null>(null);
  const load = useCallback(async () => {
    try {
      const [choices, profiles, sessions] = await Promise.all([getTutorSessionOptions(), getTutorOptions(), getTutorSessions()]);
      setOptions(choices); setProfileOptions(profiles);
      const active = sessions.sessions.find((item) => item.status === 'active') || null;
      setSession(active);
      const retained = active ? [...active.turns].reverse().find((item) => item.role === 'assistant' && item.structured?.operationRef) : undefined;
      setAgentReply(retained?.structured as TutorAgentReply || null);
      if (active) { const retainedPractice = await getTutorPractice(active.sessionRef); setPractice(retainedPractice); setPracticeAnswer(retainedPractice?.question.answer || ''); }
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
    try { const result = await operation(); setSession(result.status === 'active' ? result : null); setNextUnit(null); setSources(null); setExpandedSource(null); setAgentReply(null); if (confirmation) notify(confirmation); }
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
    <section className="panel stack tutor-guided-practice">
      <div className="panel-heading"><div><span className="pill">GUIDED PRACTICE</span><h2>Practise one eligible question</h2></div>{!practice || practice.status === 'submitted' ? <Button className="primary" disabled={busy} onClick={async () => { setBusy(true); setError(''); try { const value = await startTutorPractice(session.sessionRef, key()); setPractice(value); setPracticeAnswer(value.question.answer); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>Start practice</Button> : null}</div>
      {practice && <article className="card stack"><div><span className="eyebrow">{practice.unitCode} · QUESTION {practice.question.number} · {practice.question.marks} MARKS</span><h3>{practice.question.prompt}</h3>{practice.question.sharedStem && <p>{practice.question.sharedStem}</p>}</div>{practice.assetUrls.map((url, index) => <Image unoptimized width={640} height={400} src={url} alt={`Question diagram ${index + 1}`} key={url} />)}{practice.status === 'active' ? <><label className="stack"><span>Your answer</span><textarea rows={5} value={practiceAnswer} onChange={(event) => setPracticeAnswer(event.target.value)} /></label>{practice.latestHint && <p className="source-note"><strong>Hint {practice.hintCount}:</strong> {practice.latestHint}</p>}<div className="button-row"><Button variant="outline" disabled={busy} onClick={async () => { setBusy(true); try { setPractice(await getTutorPracticeHint(session.sessionRef, key())); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>Get next hint</Button><Button variant="outline" disabled={busy} onClick={async () => { setBusy(true); try { setPractice(await saveTutorPracticeAnswer(session.sessionRef, practiceAnswer, key())); notify('Practice answer saved.'); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>Save answer</Button><Button className="primary" disabled={busy} onClick={async () => { setBusy(true); setError(''); try { await saveTutorPracticeAnswer(session.sessionRef, practiceAnswer, key()); setPractice(await submitTutorPractice(session.sessionRef, key())); notify('Practice submitted and assessed.'); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>Submit for assessment</Button></div><small>You can switch tutors without losing this question. Submit it before moving to another unit.</small></> : practice.question.result ? <div className="practice-feedback stack"><div className="spread"><h3>Authoritative AKURU assessment</h3><strong>{practice.question.result.awardedMarks}/{practice.question.result.maxMarks}</strong></div><h4>How each mark was decided</h4>{practice.question.result.markingDecisions.map((decision) => <p className="source-note" key={decision.pointId}><strong>{decision.awarded ? 'Awarded' : 'Not awarded'}:</strong> {decision.rationale}<br /><small>Your evidence: {decision.studentEvidence}</small></p>)}{!!practice.question.result.smallMistakes.length && <p><strong>Small improvements:</strong> {practice.question.result.smallMistakes.join(' ')}</p>}<p><strong>Improved answer:</strong> {practice.question.result.improvedAnswer}</p><p><strong>Explanation:</strong> {practice.question.result.teachingExplanation}</p></div> : <p>Assessment feedback is awaiting the permitted review workflow.</p>}</article>}
      {!practice && <p>Start a question selected deterministically from this covered unit.</p>}
    </section>
    <section className="panel stack tutor-transcript" aria-label="Tutor transcript">
      <div className="panel-heading"><div><span className="pill"><ArrowRightLeft size={13} /> CONTINUOUS HANDOVER</span><h2>Conversation</h2></div></div>
      {!session.turns.length ? <Empty title="Ask your first question">AKURU will retain this message with the tutor version that received it.</Empty> : <div className="tutor-turn-list">{session.turns.map((turn) => <article key={turn.turnRef} className={`tutor-turn ${turn.role}`}><strong>{turn.role === 'student' ? 'You' : session.currentTutor.name}</strong><p>{turn.content}</p><small>{turn.modality === 'voice' ? 'Voice transcript' : 'Text'} · tutor version {turn.profileVersion}</small></article>)}</div>}
      {agentReply && <aside className="agent-evidence stack" aria-label="Evidence used by tutor">{agentReply.citations.map((citation) => <a className="citation-link" key={citation.citationRef} href={citation.assetUrl} target="_blank" rel="noreferrer"><BookMarked size={14} />{citation.textbookTitle} · {citation.pageReference}</a>)}{agentReply.visuals.map((visual) => <figure key={visual.contentUrl}><Image unoptimized width={640} height={400} src={visual.contentUrl} alt={visual.altText} /><figcaption>{visual.title}</figcaption></figure>)}{!!agentReply.followUpChoices.length && <div className="follow-up-choices"><strong>Continue with:</strong>{agentReply.followUpChoices.map((choice) => <button type="button" key={choice} onClick={() => setMessage(choice)}>{choice}</button>)}</div>}</aside>}
      <label className="tutor-mode"><span>Teaching approach</span><select value={teachingMode} disabled={busy} onChange={(event) => setTeachingMode(event.target.value as TutorAgentReply['teachingMode'])}><option value="explanation">Explanation</option><option value="questions">Questions</option><option value="guided_practice">Guided practice</option><option value="socratic_practice">Socratic practice</option><option value="revision">Revision</option><option value="exam_technique">Exam technique</option><option value="french_conversation">French conversation</option></select></label>
      <form className="tutor-composer" onSubmit={async (event) => { event.preventDefault(); const content = message.trim(); if (!content) return; setBusy(true); setError(''); try { const reply = await addTutorAgentTurn(session.sessionRef, content, teachingMode, key()); setAgentReply(reply); setMessage(''); const refreshed = await getTutorSessions(); setSession(refreshed.sessions.find((item) => item.sessionRef === session.sessionRef) || session); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>
        <Input aria-label="Message your tutor" placeholder="Ask about this unit…" value={message} onChange={(event) => setMessage(event.target.value)} maxLength={8000} />
        <Button className="primary" type="submit" disabled={busy || !message.trim()}><Send size={16} />Send</Button>
      </form>
      <small>AKURU uses only your eligible unit, verified learner context and approved sources. Proposed tutor observations do not change mastery or your study plan.</small>
    </section>
    <TutorSignals refreshKey={agentReply?.turnRef} />
  </div>;
}
