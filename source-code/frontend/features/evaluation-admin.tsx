'use client';
/* eslint-disable react/react-compiler */
import { useCallback, useEffect, useState } from 'react';
import { api, errorMessage, type State } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Empty, Picker } from './shared';

type Corpus = { id: string; subjectId: string; versionNumber: number; name: string; cases: Record<string, unknown>[]; status: string; contentHash: string; approvedAt?: string | null };
type Run = { id: string; corpusId: string; subjectId: string; candidateModel: string; promptVersion: string; metrics: Record<string, number>; thresholds: Record<string, number>; passed: boolean; failureReasons: string[]; createdAt: string };
type Release = { subjectId: string; workflow: string; mode: string; runId?: string | null; confidenceThreshold: number };
type Dashboard = { corpora: Corpus[]; runs: Run[]; releases: Release[]; missingApprovedSubjects: string[] };

const CASE_TEMPLATE = JSON.stringify([
  { caseId: 'inventory-1', category: 'inventory', input: {}, expected: { questionIds: ['Q1'] } },
  { caseId: 'ocr-1', category: 'ocr', input: {}, expected: { text: 'Reviewed source text' } },
  { caseId: 'equation-1', category: 'equation', input: {}, expected: { equation: 'x^2+2x+1' } },
  { caseId: 'diagram-1', category: 'diagram', input: {}, expected: { preserved: true } },
  { caseId: 'mapping-1', category: 'mapping', input: {}, expected: { unitIds: ['reviewed-unit-id'], crossSubjectRejected: true } },
  { caseId: 'marking-1', category: 'marking', input: {}, expected: { marks: 2, methodPoints: ['M1'] } },
  { caseId: 'feedback-1', category: 'feedback', input: {}, expected: { smallErrors: ['reviewed-error'], improvedAnswerRequired: true, sourceIds: ['reviewed-source-id'] } },
  { caseId: 'repeatability-1', category: 'repeatability', input: {}, expected: { stableDecisions: ['reviewed-decision'] } },
], null, 2);

export function EvaluationAdmin({ data, notify }: { data: State; notify: (message: string) => void }) {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [subjectId, setSubjectId] = useState(data.subjects[0]?.id || 'maths');
  const [name, setName] = useState('Reviewed evaluation corpus');
  const [cases, setCases] = useState(CASE_TEMPLATE);
  const [observations, setObservations] = useState('[]');
  const [model, setModel] = useState('configured-model');
  const [prompt, setPrompt] = useState('assessment-v1');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(async () => { try { setDashboard(await api('evaluations/admin') as Dashboard); setError(''); } catch (e) { setError(errorMessage(e)); } }, []);
  useEffect(() => { void load(); }, [load]);
  async function act(work: () => Promise<unknown>, message: string) { setBusy(true); setError(''); try { await work(); await load(); notify(message); } catch (e) { setError(errorMessage(e)); } finally { setBusy(false); } }
  const approved = dashboard?.corpora.find((row) => row.subjectId === subjectId && row.status === 'approved');
  return <div className="stack">
    <section className="panel stack"><h2>Evaluation release gates</h2><p>Automatic feedback stays review-only until a reviewed corpus passes every required threshold for the selected subject, model and prompt version.</p>
      {error && <div className="error" role="alert">{error}</div>}
      {dashboard?.missingApprovedSubjects.length ? <div className="notice">Missing approved corpus: {dashboard.missingApprovedSubjects.join(', ')}</div> : <div className="success">Every Phase 1 subject has an approved corpus.</div>}
    </section>
    <section className="panel stack"><h2>Create a reviewed corpus version</h2>
      <Picker label="Subject" value={subjectId} onChange={setSubjectId} options={data.subjects.map((s) => ({ value: s.id, label: s.name }))} />
      <label className="stack" htmlFor="evaluation-name">Corpus name</label><Input id="evaluation-name" value={name} onChange={(e) => setName(e.target.value)} />
      <label className="stack" htmlFor="evaluation-cases">Reviewed cases (JSON)</label><Textarea id="evaluation-cases" rows={18} value={cases} onChange={(e) => setCases(e.target.value)} />
      <Button disabled={busy} onClick={() => act(() => api('evaluations/admin/corpora', { subjectId, name, cases: JSON.parse(cases) }), 'Evaluation corpus draft saved.')}>Save draft</Button>
      <div className="stack">{dashboard?.corpora.filter((c) => c.subjectId === subjectId).map((c) => <article className="card" key={c.id}><strong>{c.name} · v{c.versionNumber}</strong><p>{c.cases.length} cases · {c.status} · hash {c.contentHash.slice(0, 12)}…</p>{c.status === 'draft' && <Button disabled={busy} onClick={() => act(() => api(`evaluations/admin/corpora/${c.id}/review`, { decision: 'approved' }), 'Corpus approved.')}>Approve reviewed corpus</Button>}</article>)}</div>
    </section>
    <section className="panel stack"><h2>Run a candidate regression</h2>{!approved ? <Empty title="Approve a corpus first">A regression can only run against the active Admin-approved subject corpus.</Empty> : <>
      <label className="stack" htmlFor="evaluation-model">Candidate model</label><Input id="evaluation-model" value={model} onChange={(e) => setModel(e.target.value)} />
      <label className="stack" htmlFor="evaluation-prompt">Prompt version</label><Input id="evaluation-prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      <label className="stack" htmlFor="evaluation-observations">Observed outputs (JSON)</label><Textarea id="evaluation-observations" rows={14} value={observations} onChange={(e) => setObservations(e.target.value)} />
      <Button disabled={busy} onClick={() => act(() => api('evaluations/admin/runs', { corpusId: approved.id, candidateModel: model, promptVersion: prompt, observations: JSON.parse(observations) }), 'Regression completed.')}>Run evaluation</Button></>}
      {dashboard?.runs.filter((r) => r.subjectId === subjectId).map((r) => <article className="card" key={r.id}><strong>{r.passed ? 'PASS' : 'BLOCKED'} · {r.candidateModel} · {r.promptVersion}</strong><p>{Object.entries(r.metrics).map(([key, value]) => `${key}: ${(value * 100).toFixed(1)}%`).join(' · ')}</p>{r.failureReasons.map((reason) => <p className="error" key={reason}>{reason}</p>)}{r.passed && <Button disabled={busy} onClick={() => act(() => api('evaluations/admin/releases', { subjectId, workflow: 'assessment_feedback', mode: 'automatic', runId: r.id, confidenceThreshold: .85 }), 'Passing assessment release activated.')}>Activate automatic feedback</Button>}</article>)}
    </section>
  </div>;
}
