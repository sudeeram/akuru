'use client';
/* eslint-disable react/react-compiler */
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import Image from 'next/image';
import { Bot, Pencil, Plus, Save, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  deleteTutorProfile,
  errorMessage,
  getTutorAdminPresets,
  getTutorOptions,
  getTutorProfiles,
  saveTutorProfile,
  updateTutorPreset,
  type State,
  type TutorAdminPresets,
  type TutorOptions,
  type TutorProfile,
  type TutorProfileDraft,
} from '@/api';
import { Empty, Heading } from './shared';

const initialDraft: TutorProfileDraft = {
  name: 'My AKURU Tutor', presentation: 'neutral', avatarCode: 'akuru-spark', voiceCode: 'bright-companion',
  tone: 'encouraging', friendliness: 'medium', enthusiasm: 'medium', speed: 'medium',
  communicationCharacter: 'balanced', explanationDepth: 'standard', teachingStyle: 'guided',
};

const title = (value: string) => value.replaceAll('_', ' ').replace(/^./, (character) => character.toUpperCase());

function Choice({ label, value, values, change }: { label: string; value: string; values: string[]; change: (value: string) => void }) {
  const name = `tutor-${label.toLowerCase().replaceAll(' ', '-')}`;
  return <fieldset className="tutor-choice"><legend>{label}</legend><div>{values.map((item) => <label key={item} data-selected={value === item}><input type="radio" name={name} value={item} checked={value === item} onChange={() => change(item)} /><span>{title(item)}</span></label>)}</div></fieldset>;
}

function ProfileCard({ profile, options, actions }: { profile: TutorProfile; options: TutorOptions; actions?: ReactNode }) {
  const avatar = options.avatars.find((item) => item.code === profile.avatarCode);
  const voice = options.voices.find((item) => item.code === profile.voiceCode);
  return <article className="panel tutor-profile-card">
    <div className="tutor-avatar-wrap"><Image unoptimized width={145} height={165} src={avatar?.imagePath || '/akuru-bots/akuru-bot-say.png'} alt={`${profile.name}, ${avatar?.name || 'AKURU BOT'} avatar`} /></div>
    <div className="stack tutor-profile-copy"><div><span className="pill">AI TUTOR · VERSION {profile.version}</span><h3>{profile.name}</h3><p>{avatar?.description}</p></div>
      <div className="tutor-tags"><span>{title(profile.presentation)}</span><span>{title(profile.communicationCharacter)}</span><span>{title(profile.tone)}</span><span>{title(profile.teachingStyle)}</span></div>
      <p><strong>Voice:</strong> {voice?.name || profile.voiceCode} · <strong>Speed:</strong> {title(profile.speed)} · <strong>Detail:</strong> {title(profile.explanationDepth)}</p>
      {actions && <div className="button-row">{actions}</div>}
    </div>
  </article>;
}

export function TutorProfiles({ data, notify }: { data: State; notify: (message: string) => void }) {
  const studentMode = data.user.role === 'student';
  const [studentId, setStudentId] = useState(data.students[0]?.id || '');
  const [options, setOptions] = useState<TutorOptions | null>(null);
  const [profiles, setProfiles] = useState<TutorProfile[]>([]);
  const [draft, setDraft] = useState<TutorProfileDraft>(initialDraft);
  const [editing, setEditing] = useState('');
  const [busy, setBusy] = useState(false), [loading, setLoading] = useState(true), [error, setError] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [available, saved] = await Promise.all([getTutorOptions(), getTutorProfiles(studentMode ? undefined : studentId)]);
      setOptions(available); setProfiles(saved.profiles);
      setDraft((current) => {
        if (editing || (available.avatars.some((item) => item.code === current.avatarCode && item.enabled !== false)
          && available.voices.some((item) => item.code === current.voiceCode && item.enabled !== false))) return current;
        const presentation = current.presentation;
        const avatar = available.avatars.find((item) => item.enabled !== false && (item.presentation === presentation || item.presentation === 'neutral'));
        const voice = available.voices.find((item) => item.enabled !== false && (item.presentation === presentation || item.presentation === 'neutral'));
        return { ...current, avatarCode: avatar?.code || '', voiceCode: voice?.code || '' };
      });
    } catch (cause) { setError(errorMessage(cause)); }
    finally { setLoading(false); }
  }, [editing, studentId, studentMode]);
  useEffect(() => { if (studentMode || studentId) void load(); }, [load, studentId, studentMode]);
  const matchingAvatars = useMemo(() => options?.avatars.filter((item) => item.enabled !== false && (item.presentation === draft.presentation || item.presentation === 'neutral')) || [], [options, draft.presentation]);
  const matchingVoices = useMemo(() => options?.voices.filter((item) => item.enabled !== false && (item.presentation === draft.presentation || item.presentation === 'neutral')) || [], [options, draft.presentation]);
  const set = <K extends keyof TutorProfileDraft>(key: K, value: TutorProfileDraft[K]) => setDraft((current) => ({ ...current, [key]: value }));
  const changePresentation = (value: string) => {
    const presentation = value as TutorProfileDraft['presentation'];
    const avatar = options?.avatars.find((item) => item.enabled !== false && item.presentation === presentation) || options?.avatars.find((item) => item.enabled !== false && item.presentation === 'neutral');
    const voice = options?.voices.find((item) => item.enabled !== false && item.presentation === presentation) || options?.voices.find((item) => item.enabled !== false && item.presentation === 'neutral');
    setDraft((current) => ({ ...current, presentation, avatarCode: avatar?.code || '', voiceCode: voice?.code || '' }));
  };
  if (!studentMode) return <div className="stack"><Heading eyebrow="PARENT · TUTORS" title="Your child's AKURU tutors">Tutor profiles use child-safe choices prepared by AKURU.</Heading>
    {data.students.length > 1 && <label className="stack tutor-student-choice"><span>Student</span><select value={studentId} onChange={(event) => setStudentId(event.target.value)}>{data.students.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>}
    {loading ? <section className="panel">Loading tutor profiles…</section> : error ? <section className="panel stack"><div className="error" role="alert">{error}</div><Button onClick={() => void load()}>Retry</Button></section> : options && profiles.length ? <div className="tutor-profile-grid">{profiles.map((profile) => <ProfileCard key={profile.profileRef} profile={profile} options={options} />)}</div> : <Empty title="No tutor profiles yet">Your child can create tutors from the My tutors page.</Empty>}
  </div>;
  return <div className="stack"><Heading eyebrow="STUDENT · MY TUTORS" title="Build your tutor team">Choose a child-safe AKURU hero and teaching style. You can create more than one tutor and rename them whenever you like.</Heading>
    {error && <div className="error" role="alert">{error}</div>}
    {loading ? <section className="panel">Loading your tutors…</section> : <>
      {options && <form className="panel stack tutor-builder" onSubmit={async (event) => { event.preventDefault(); setBusy(true); setError(''); try { await saveTutorProfile(draft, editing || undefined); notify(editing ? 'Tutor updated.' : 'Tutor created.'); setEditing(''); setDraft(initialDraft); await load(); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>
        <div className="panel-heading"><div><span className="pill"><Bot size={14} /> CURATED AKURU BOT</span><h2>{editing ? 'Update your tutor' : 'Create a tutor'}</h2></div></div>
        <label className="stack" htmlFor="tutor-name"><span>Tutor name</span><Input id="tutor-name" value={draft.name} minLength={2} maxLength={60} required onChange={(event) => set('name', event.target.value)} /></label>
        <Choice label="Presentation" value={draft.presentation} values={options.presentations} change={changePresentation} />
        <fieldset className="tutor-avatar-picker"><legend>Choose an avatar</legend>{matchingAvatars.map((avatar) => <label key={avatar.code} data-selected={draft.avatarCode === avatar.code}><input type="radio" name="avatar" value={avatar.code} checked={draft.avatarCode === avatar.code} onChange={() => set('avatarCode', avatar.code)} /><Image unoptimized width={145} height={120} src={avatar.imagePath} alt="" /><strong>{avatar.name}</strong><small>{avatar.description}</small></label>)}</fieldset>
        <div className="three-cols">
          <Choice label="Voice" value={draft.voiceCode} values={matchingVoices.map((item) => item.code)} change={(value) => set('voiceCode', value)} />
          <Choice label="Tone" value={draft.tone} values={options.tones} change={(value) => set('tone', value as TutorProfileDraft['tone'])} />
          <Choice label="Character" value={draft.communicationCharacter} values={options.communicationCharacters} change={(value) => set('communicationCharacter', value as TutorProfileDraft['communicationCharacter'])} />
        </div>
        <div className="three-cols">
          <Choice label="Friendliness" value={draft.friendliness} values={options.levels} change={(value) => set('friendliness', value as TutorProfileDraft['friendliness'])} />
          <Choice label="Enthusiasm" value={draft.enthusiasm} values={options.levels} change={(value) => set('enthusiasm', value as TutorProfileDraft['enthusiasm'])} />
          <Choice label="Speed" value={draft.speed} values={options.levels} change={(value) => set('speed', value as TutorProfileDraft['speed'])} />
        </div>
        <div className="two-cols">
          <Choice label="Explanation detail" value={draft.explanationDepth} values={options.explanationDepths} change={(value) => set('explanationDepth', value as TutorProfileDraft['explanationDepth'])} />
          <Choice label="Teaching style" value={draft.teachingStyle} values={options.teachingStyles} change={(value) => set('teachingStyle', value as TutorProfileDraft['teachingStyle'])} />
        </div>
        <div className="button-row"><Button type="submit" className="primary" disabled={busy}><Save size={16} />{busy ? 'Saving…' : editing ? 'Save new version' : 'Create tutor'}</Button>{editing && <Button type="button" variant="outline" onClick={() => { setEditing(''); setDraft(initialDraft); }}>Cancel</Button>}</div>
      </form>}
      {options && profiles.length ? <div className="tutor-profile-grid">{profiles.map((profile) => <ProfileCard key={profile.profileRef} profile={profile} options={options} actions={<><Button variant="outline" onClick={() => { setEditing(profile.profileRef); setDraft(profile); window.scrollTo({ top: 0, behavior: 'smooth' }); }}><Pencil size={15} />Edit</Button><Button variant="outline" onClick={async () => { setBusy(true); try { await deleteTutorProfile(profile.profileRef); notify('Tutor removed.'); await load(); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }} disabled={busy}><Trash2 size={15} />Remove</Button></>} />)}</div> : <Empty title="Create your first tutor"><Plus size={20} /> Choose a hero and the way you want to learn.</Empty>}
    </>}
  </div>;
}

export function TutorPresetAdmin({ notify }: { notify: (message: string) => void }) {
  const [presets, setPresets] = useState<TutorAdminPresets | null>(null), [error, setError] = useState(''), [busy, setBusy] = useState('');
  const load = useCallback(async () => { try { setPresets(await getTutorAdminPresets()); setError(''); } catch (cause) { setError(errorMessage(cause)); } }, []);
  useEffect(() => { void load(); }, [load]);
  const change = async (kind: 'avatars' | 'voices', code: string, enabled: boolean, sortOrder: number) => { setBusy(`${kind}:${code}`); try { setPresets(await updateTutorPreset(kind, code, enabled, sortOrder)); notify('Tutor preset updated.'); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(''); } };
  return <div className="stack"><section className="panel stack"><h2>Curated tutor presets</h2><p>Students can use only these child-safe AKURU hero avatars and approved voice styles. Disabling a preset prevents new profile selections while preserving historical profile versions.</p>{error && <div className="error" role="alert">{error}</div>}</section>
    {!presets ? <section className="panel">Loading tutor presets…</section> : <><section className="panel stack"><h2>Avatar heroes</h2><div className="tutor-admin-list">{presets.avatars.map((item) => <article className="card" key={item.code}><Image unoptimized width={85} height={95} src={item.imagePath} alt={`${item.name} AKURU tutor avatar`} /><div><h3>{item.name}</h3><p>{item.description}</p><small>{title(item.presentation)} · Order {item.sortOrder}</small></div><div className="button-row"><Button disabled={busy === `avatars:${item.code}` || (item.sortOrder || 0) === 0} variant="outline" onClick={() => void change('avatars', item.code, Boolean(item.enabled), Math.max(0, (item.sortOrder || 0) - 10))}>Earlier</Button><Button disabled={busy === `avatars:${item.code}`} variant="outline" onClick={() => void change('avatars', item.code, Boolean(item.enabled), Math.min(1000, (item.sortOrder || 0) + 10))}>Later</Button><Button disabled={busy === `avatars:${item.code}`} variant="outline" onClick={() => void change('avatars', item.code, !item.enabled, item.sortOrder || 0)}>{item.enabled ? 'Disable' : 'Enable'}</Button></div></article>)}</div></section>
      <section className="panel stack"><h2>Voice styles</h2><div className="tutor-admin-list">{presets.voices.map((item) => <article className="card" key={item.code}><div><h3>{item.name}</h3><p>{item.description}</p><small>{title(item.presentation)} · Order {item.sortOrder}</small></div><div className="button-row"><Button disabled={busy === `voices:${item.code}` || (item.sortOrder || 0) === 0} variant="outline" onClick={() => void change('voices', item.code, Boolean(item.enabled), Math.max(0, (item.sortOrder || 0) - 10))}>Earlier</Button><Button disabled={busy === `voices:${item.code}`} variant="outline" onClick={() => void change('voices', item.code, Boolean(item.enabled), Math.min(1000, (item.sortOrder || 0) + 10))}>Later</Button><Button disabled={busy === `voices:${item.code}`} variant="outline" onClick={() => void change('voices', item.code, !item.enabled, item.sortOrder || 0)}>{item.enabled ? 'Disable' : 'Enable'}</Button></div></article>)}</div></section></>}
  </div>;
}
