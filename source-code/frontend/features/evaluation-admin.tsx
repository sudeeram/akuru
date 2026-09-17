'use client';
/* eslint-disable react/react-compiler */
import { useCallback, useEffect, useState } from 'react';
import { api, errorMessage, getTutorAdminPresets, type State, type TutorAdminPresets } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Empty, Picker } from './shared';

type Corpus = { id: string; subjectId: string; workflow: 'assessment'|'tutor'; versionNumber: number; name: string; cases: Record<string, unknown>[]; status: string; contentHash: string; approvedAt?: string | null };
type Run = { id: string; corpusId: string; subjectId: string; workflow: string; modality: 'assessment'|'text'|'voice'|'tools'; environment: 'ci'|'staging'; candidateModel: string; promptVersion: string; metrics: Record<string, number>; thresholds: Record<string, number>; passed: boolean; failureReasons: string[]; createdAt: string };
type Release = { subjectId: string; workflow: string; mode: string; audience: string; runId?: string | null; confidenceThreshold: number };
type Dashboard = { corpora: Corpus[]; runs: Run[]; releases: Release[]; missingApprovedSubjects: string[]; missingApprovedTutorSubjects: string[] };

const CASE_TEMPLATE = JSON.stringify([
  { caseId: 'inventory-1', category: 'inventory', input: {}, expected: { questionIds: ['Q1'] } },
  { caseId: 'ocr-1', category: 'ocr', input: {}, expected: { text: 'Reviewed source text' } },
  { caseId: 'equation-1', category: 'equation', input: {}, expected: { equation: 'x^2+2x+1' } },
  { caseId: 'diagram-1', category: 'diagram', input: {}, expected: { preserved: true } },
  { caseId: 'mapping-1', category: 'mapping', input: {}, expected: { topicRefs: ['reviewed-topic-ref'], crossSubjectRejected: true, unmappedTopicRejected: true } },
  { caseId: 'topic-citation-1', category: 'topic_citation', input: {}, expected: { topicIsolation: true, requiredCitationFields: ['topicRef','groupTitle','documentTitle','pdfPage','printedPage','boundingBox'], inventedCitationRejected: true } },
  { caseId: 'marking-1', category: 'marking', input: {}, expected: { marks: 2, methodPoints: ['M1'] } },
  { caseId: 'feedback-1', category: 'feedback', input: {}, expected: { smallErrors: ['reviewed-error'], improvedAnswerRequired: true, sourceIds: ['reviewed-source-id'] } },
  { caseId: 'repeatability-1', category: 'repeatability', input: {}, expected: { stableDecisions: ['reviewed-decision'] } },
], null, 2);

function tutorTemplate(presets: TutorAdminPresets | null) { return JSON.stringify([
  { caseId:'tutor-factual-low', category:'tutor_factual', input:{masteryLevel:'low'}, expected:{requiredChecks:['factually-correct','age-suitable']} },
  { caseId:'tutor-maths-medium', category:'tutor_mathematical', input:{masteryLevel:'medium'}, expected:{requiredChecks:['exact-equation','correct-working','correct-answer']} },
  { caseId:'tutor-grounding-high', category:'tutor_grounding', input:{masteryLevel:'high'}, expected:{requiredChecks:['exact-edition','exact-topic','exact-group','exact-page','reject-invented-reference']} },
  { caseId:'tutor-personalisation', category:'tutor_personalisation', input:{masteryLevel:'low'}, expected:{requiredChecks:['evidence-backed-claim','recurring-count-exact','confidence-language']} },
  { caseId:'tutor-next-topic', category:'tutor_recommendation', input:{masteryLevel:'medium'}, expected:{requiredChecks:['deterministic-ranking','eligible-topic-only','no-automatic-plan-change']} },
  { caseId:'tutor-persona-matrix', category:'tutor_persona', input:{masteryLevel:'high'}, expected:{personaMatrixComplete:true,personaCombinationCount:11664,requiredChecks:['all-combinations-reviewed','age-suitable','academic-consistency']} },
  { caseId:'tutor-security', category:'tutor_security', input:{masteryLevel:'low'}, expected:{requiredChecks:['prompt-injection-rejected','cross-subject-rejected','sibling-isolated','unsupported-unit-rejected','formal-assessment-blocked']} },
  { caseId:'tutor-handover', category:'tutor_handover', input:{masteryLevel:'medium'}, expected:{requiredChecks:['profile-version-retained','handover-accurate','no-cross-student-context']} },
  { caseId:'tutor-voice', category:'tutor_voice', input:{masteryLevel:'high'}, expected:{requiredChecks:['french-voice','captions','interruption','latency-budget','reconnect','quota-settlement']} },
  { caseId:'tutor-presets', category:'tutor_preset_safety', input:{masteryLevel:'medium'}, expected:{reviewedAvatarCodes:presets?.avatars.filter(x=>x.enabled).map(x=>x.code)||[],reviewedVoiceCodes:presets?.voices.filter(x=>x.enabled).map(x=>x.code)||[],requiredChecks:['all-enabled-avatars-reviewed','all-enabled-voices-reviewed','akuru-brand-suitable']} },
  { caseId:'tutor-operations', category:'tutor_operations', input:{masteryLevel:'low'}, expected:{requiredChecks:['security','privacy','accessibility','cost','retention','rollback-demonstrated']} },
],null,2); }

export function EvaluationAdmin({ data, notify }: { data: State; notify: (message: string) => void }) {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [subjectId, setSubjectId] = useState(data.subjects[0]?.id || 'maths');
  const [name, setName] = useState('Reviewed evaluation corpus');
  const [workflow, setWorkflow] = useState<'assessment'|'tutor'>('assessment');
  const [cases, setCases] = useState(CASE_TEMPLATE);
  const [observations, setObservations] = useState('[]');
  const [model, setModel] = useState('configured-model');
  const [prompt, setPrompt] = useState('assessment-v1');
  const [modality, setModality] = useState<Run['modality']>('assessment');
  const [environment, setEnvironment] = useState<Run['environment']>('ci');
  const [releaseFeature, setReleaseFeature] = useState('tutor_text');
  const [presets, setPresets] = useState<TutorAdminPresets | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async () => { try { const [view, availablePresets] = await Promise.all([api('evaluations/admin') as Promise<Dashboard>, getTutorAdminPresets()]); setDashboard(view); setPresets(availablePresets); setError(''); } catch (e) { setError(errorMessage(e)); } }, []);
  useEffect(() => { void load(); }, [load]);
  async function act(work: () => Promise<unknown>, message: string) { setBusy(true); setError(''); try { await work(); await load(); notify(message); } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); } }
  const approved = dashboard?.corpora.find((row) => row.subjectId === subjectId && row.workflow === workflow && row.status === 'approved');
  return <div className="stack">
    <section className="panel stack"><h2>Evaluation release gates</h2><p>Automatic feedback stays review-only until a reviewed corpus passes every required threshold for the selected subject, model and prompt version.</p>
      {error && <div className="error" role="alert">{error}</div>}
      {dashboard?.missingApprovedSubjects.length ? <div className="notice">Missing approved corpus: {dashboard.missingApprovedSubjects.join(', ')}</div> : <div className="success">Every Phase 1 subject has an approved corpus.</div>}
      {dashboard?.missingApprovedTutorSubjects.length ? <div className="notice">Tutor subjects awaiting approval: {dashboard.missingApprovedTutorSubjects.join(', ')}</div> : <div className="success">Every enabled iGCSE subject has an approved Tutor corpus.</div>}
    </section>
    <section className="panel stack"><h2>Create a reviewed corpus version</h2>
      <Picker label="Subject" value={subjectId} onChange={setSubjectId} options={data.subjects.map((s) => ({ value: s.id, label: s.name }))} />
      <Picker label="Workflow" value={workflow} onChange={(value) => { const next=value as 'assessment'|'tutor'; setWorkflow(next); setModality(next==='tutor'?'text':'assessment'); setPrompt(next==='tutor'?'tutor-v1':'assessment-v1'); setCases(next==='tutor'?tutorTemplate(presets):CASE_TEMPLATE); }} options={[{value:'assessment',label:'Assessment'},{value:'tutor',label:'Tutor'}]} />
      <label className="stack" htmlFor="evaluation-name">Corpus name</label><Input id="evaluation-name" value={name} onChange={(e) => setName(e.target.value)} />
      <label className="stack" htmlFor="evaluation-cases">Reviewed cases (JSON)</label><Textarea id="evaluation-cases" rows={18} value={cases} onChange={(e) => setCases(e.target.value)} />
      <Button disabled={busy} onClick={() => act(() => api('evaluations/admin/corpora', { subjectId, workflow, name, cases: JSON.parse(cases) }), 'Evaluation corpus draft saved.')}>Save draft</Button>
      <div className="stack">{dashboard?.corpora.filter((c) => c.subjectId === subjectId && c.workflow === workflow).map((c) => <article className="card" key={c.id}><strong>{c.name} · {c.workflow} v{c.versionNumber}</strong><p>{c.cases.length} cases · {c.status} · hash {c.contentHash.slice(0, 12)}…</p>{c.status === 'draft' && <Button disabled={busy} onClick={() => act(() => api(`evaluations/admin/corpora/${c.id}/review`, { decision: 'approved' }), 'Corpus approved.')}>Approve reviewed corpus</Button>}</article>)}</div>
    </section>
    <section className="panel stack"><h2>Run a candidate regression</h2>{!approved ? <Empty title="Approve a corpus first">A regression can only run against the active Admin-approved subject corpus.</Empty> : <>
      <label className="stack" htmlFor="evaluation-model">Candidate model</label><Input id="evaluation-model" value={model} onChange={(e) => setModel(e.target.value)} />
      <label className="stack" htmlFor="evaluation-prompt">Prompt version</label><Input id="evaluation-prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      {workflow==='tutor' && <><Picker label="Modality" value={modality} onChange={(value)=>setModality(value as Run['modality'])} options={['text','voice','tools'].map(value=>({value,label:value}))}/><Picker label="Environment" value={environment} onChange={(value)=>setEnvironment(value as Run['environment'])} options={[{value:'ci',label:'CI'},{value:'staging',label:'Production-like staging'}]}/></>}
      <label className="stack" htmlFor="evaluation-observations">Observed outputs (JSON)</label><Textarea id="evaluation-observations" rows={14} value={observations} onChange={(e) => setObservations(e.target.value)} />
      <Button disabled={busy} onClick={() => act(() => api('evaluations/admin/runs', { corpusId: approved.id, candidateModel: model, promptVersion: prompt, modality, environment, observations: JSON.parse(observations) }), 'Regression completed.')}>Run evaluation</Button></>}
      {workflow==='tutor' && <Picker label="Tutor feature gate" value={releaseFeature} onChange={setReleaseFeature} options={['tutor_text','tutor_voice','tutor_tools','tutor_learner_context','tutor_next_unit','tutor_sources','tutor_practice','tutor_visuals'].map(value=>({value,label:value.replaceAll('_',' ')}))}/>}
      {dashboard?.runs.filter((r) => r.subjectId === subjectId && r.workflow === workflow).map((r) => <article className="card" key={r.id}><strong>{r.passed ? 'PASS' : 'BLOCKED'} · {r.modality} · {r.environment} · {r.candidateModel} · {r.promptVersion}</strong><p>{Object.entries(r.metrics).map(([key, value]) => `${key}: ${(value * 100).toFixed(1)}%`).join(' · ')}</p>{r.failureReasons.map((reason) => <p className="error" key={reason}>{reason}</p>)}{r.passed && (workflow==='assessment'?<Button disabled={busy} onClick={() => act(() => api('evaluations/admin/releases', { subjectId, workflow: 'assessment_feedback', mode: 'automatic', runId: r.id, confidenceThreshold: .85 }), 'Passing assessment release activated.')}>Activate automatic feedback</Button>:<div className="button-row"><Button disabled={busy} onClick={()=>act(()=>api('evaluations/admin/releases',{subjectId,workflow:releaseFeature,mode:'automatic',runId:r.id,audience:'admin_testing'}),'Admin testing gate activated.')}>Admin testing</Button><Button disabled={busy} onClick={()=>act(()=>api('evaluations/admin/releases',{subjectId,workflow:releaseFeature,mode:'automatic',runId:r.id,audience:'parent_pilot'}),'Parent pilot gate activated.')}>Parent pilot</Button><Button disabled={busy || r.environment!=='staging'} onClick={()=>act(()=>api('evaluations/admin/releases',{subjectId,workflow:releaseFeature,mode:'automatic',runId:r.id,audience:'students'}),'Student release activated.')}>Eligible students</Button><Button variant="outline" disabled={busy} onClick={()=>act(()=>api('evaluations/admin/releases',{subjectId,workflow:releaseFeature,mode:'review_required',audience:'admin_testing'}),'Tutor feature kill switch applied.')}>Disable feature</Button></div>)}</article>)}
    </section>
  </div>;
}
