'use client';
/* State effects load server-owned quota records and audit history. */
/* eslint-disable react/react-compiler */
import { useCallback, useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { errorMessage, getTutorAdminQuotas, getTutorQuotaAudit, updateTutorAdminQuota, type TutorQuota, type TutorQuotaAudit } from '@/lib/api';
import { Empty } from './shared';

const number = (value: string) => Math.max(0, Number.parseInt(value, 10) || 0);

export function TutorQuotaAdmin({ notify }: { notify: (message: string) => void }) {
  const [items, setItems] = useState<TutorQuota[]>([]), [selected, setSelected] = useState('');
  const [draft, setDraft] = useState<TutorQuota | null>(null), [reason, setReason] = useState('');
  const [audit, setAudit] = useState<TutorQuotaAudit | null>(null), [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const load = useCallback(async () => { try { const result = await getTutorAdminQuotas(); setItems(result.quotas); setSelected((value) => { const next = value || result.quotas[0]?.studentRef || ''; setDraft(result.quotas.find((item) => item.studentRef === next) || null); return next; }); setError(''); } catch (cause) { setError(errorMessage(cause)); } }, []);
  useEffect(() => { void load(); }, [load]);
  useEffect(() => { if (selected) void getTutorQuotaAudit(selected).then(setAudit).catch((cause) => setError(errorMessage(cause))); }, [selected]);
  if (!items.length && !error) return <Empty title="No student accounts">Create a child account before assigning a tutor allowance.</Empty>;
  return <div className="stack">
    {error && <div className="error" role="alert">{error}</div>}
    <section className="panel stack"><h2>Per-child tutor allowance</h2><p>Requests, text tokens and voice time renew together. Provider account budgets and credentials remain separate.</p>
      <label className="stack"><span>Student</span><select value={selected} onChange={(event) => { const next = event.target.value; setSelected(next); setDraft(items.find((item) => item.studentRef === next) || null); }}>{items.map((item) => <option key={item.studentRef} value={item.studentRef}>{item.studentName}</option>)}</select></label>
      {draft && <form className="stack" onSubmit={async (event) => { event.preventDefault(); setBusy(true); setError(''); try { await updateTutorAdminQuota(draft.studentRef, { periodDays: draft.periodDays, requestAllowance: draft.requests.allowance, textTokenAllowance: draft.textTokens.allowance, voiceMinuteAllowance: draft.voiceMinutes.allowance, enabled: draft.enabled, reason }); setReason(''); await load(); setAudit(await getTutorQuotaAudit(draft.studentRef)); notify('Tutor allowance updated.'); } catch (cause) { setError(errorMessage(cause)); } finally { setBusy(false); } }}>
        <div className="three-cols"><label className="stack" htmlFor="quota-period"><span>Period in days</span><Input id="quota-period" type="number" min="1" max="366" value={draft.periodDays} onChange={(event) => setDraft({...draft, periodDays: number(event.target.value)})} /></label><label className="stack" htmlFor="quota-requests"><span>AI requests</span><Input id="quota-requests" type="number" min="0" value={draft.requests.allowance} onChange={(event) => setDraft({...draft, requests: {...draft.requests, allowance: number(event.target.value)}})} /></label><label className="stack" htmlFor="quota-tokens"><span>Text tokens</span><Input id="quota-tokens" type="number" min="0" value={draft.textTokens.allowance} onChange={(event) => setDraft({...draft, textTokens: {...draft.textTokens, allowance: number(event.target.value)}})} /></label></div>
        <label className="stack" htmlFor="quota-voice"><span>Voice minutes</span><Input id="quota-voice" type="number" min="0" value={draft.voiceMinutes.allowance} onChange={(event) => setDraft({...draft, voiceMinutes: {...draft.voiceMinutes, allowance: number(event.target.value)}})} /></label>
        <label className="check-label"><input type="checkbox" checked={draft.enabled} onChange={(event) => setDraft({...draft, enabled: event.target.checked})} /> Tutor AI enabled</label>
        <label className="stack" htmlFor="quota-reason"><span>Audit reason</span><Input id="quota-reason" minLength={3} maxLength={300} required value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Why is this allowance changing?" /></label>
        <Button className="primary" type="submit" disabled={busy || reason.trim().length < 3}>{busy ? 'Saving…' : 'Save allowance'}</Button>
      </form>}
    </section>
    {draft && <section className="panel stack"><h2>Current usage</h2><p><span className="pill">{draft.state.toUpperCase()}</span> Renews {new Date(draft.renewsAt).toLocaleString()}</p><div className="three-cols">{([['Requests', draft.requests], ['Text tokens', draft.textTokens], ['Voice minutes', draft.voiceMinutes]] as const).map(([label, value]) => <article className="card" key={label}><strong>{value.remaining.toLocaleString()}</strong><p>{label} remaining</p><small>{value.used.toLocaleString()} of {value.allowance.toLocaleString()} used</small></article>)}</div><p>{draft.fallbackMessage}</p></section>}
    <section className="panel stack"><h2>Allowance audit history</h2>{audit?.events.length ? audit.events.map((event) => <article className="card" key={event.createdAt}><strong>{event.reason}</strong><p>{new Date(event.createdAt).toLocaleString()}</p></article>) : <p>No allowance changes recorded yet.</p>}</section>
  </div>;
}
