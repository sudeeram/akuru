'use client';
import { useEffect, useId, useState } from 'react';
import { request } from '@/api/core/client';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { toast } from '@/components/ui/toast';

type Readiness = {parts: {number:string;partLabel:string;contentApproval:string;sourceAccuracy:{current:boolean;percent:number|null;origin?:string};scoringReadiness:{status:string;reason:string};tutorEligible:boolean;blockers:{code:string;message?:string}[]}[]};
type Preview={previewHash:string;affectedParts:string[];carriedForwardParts:string[];changes:{partLabel:string;fields:string[];before:unknown;after:unknown}[]};
export function DeveloperReviewTools({paperId,number,disabled,onSaved}:{paperId:string;number:string;disabled:boolean;onSaved:()=>void}) {
  const id=useId();
  const [status,setStatus]=useState<Readiness|null>(null);
  const [body,setBody]=useState('');
  const [prepared,setPrepared]=useState<{id:string;preview:Preview}|null>(null);
  const [confirmed,setConfirmed]=useState(false);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const root=`admin/official-paper-reviews/${paperId}`;
  useEffect(()=>{let active=true;void request<Readiness>(`${root}/readiness`).then(value=>{if(active)setStatus(value);}).catch(()=>{if(active)setError('Could not load review readiness.');});return()=>{active=false;};},[root]);
  const act=async(operation:()=>Promise<void>)=>{setBusy(true);setError('');try{await operation();}catch(cause){setError(cause instanceof Error?cause.message:'Review operation failed.');}finally{setBusy(false);}};
  return <details className="panel stack"><summary>Source corrections and preserved reviews · no model calls</summary>
    <p>Prepared source comparisons can be applied through authenticated developer APIs. Changed content is checked again; unchanged, source-bound reviews are carried forward. Scoring and Student release remain separate gates.</p>
    <div className="table-scroll"><table><thead><tr><th>Part</th><th>Content approval</th><th>Source comparison</th><th>Scoring</th><th>Tutor eligibility</th></tr></thead><tbody>{status?.parts.filter(p=>p.number===number).map(p=><tr key={p.partLabel}><td>{p.partLabel}</td><td>{p.contentApproval.replaceAll('_',' ')}</td><td>{p.sourceAccuracy.current?`${p.sourceAccuracy.percent}% · ${p.sourceAccuracy.origin==='carried_forward'?'Carried forward':'Current'}`:'Recheck required'}</td><td>{p.scoringReadiness.status.replaceAll('_',' ')}<small>{p.scoringReadiness.reason}</small></td><td>{p.tutorEligible?'Eligible':p.blockers.map(b=>b.message||b.code.replaceAll('_',' ')).join('; ')}</td></tr>)}</tbody></table></div>
    <label htmlFor={id}>Prepared correction package (optional Admin inspection route)</label>
    <Textarea id={id} value={body} rows={5} disabled={busy||disabled} onChange={e=>{setBody(e.target.value);setPrepared(null);setConfirmed(false);}} placeholder="Paste the source-reviewed change-set JSON. Never include passwords or API keys."/>
    <Button variant="outline" disabled={busy||disabled||!body.trim()} onClick={()=>void act(async()=>{const payload=JSON.parse(body);if(payload.number!==number)throw new Error('Select the question named in this package.');const staged=await request<{id:string}>(`${root}/change-sets`,{method:'POST',body:payload});const preview=await request<Preview>(`${root}/change-sets/${staged.id}/preview`);setPrepared({id:staged.id,preview});})}>Stage and preview correction</Button>
    {prepared&&<div className="stack"><p>Affected parts: {prepared.preview.affectedParts.join(', ')}. Preserved siblings: {prepared.preview.carriedForwardParts.join(', ')||'None'}.</p>
      {prepared.preview.changes.map(change=><details key={change.partLabel}><summary>Part {change.partLabel}: {change.fields.join(', ')||'source comparison only'}</summary><div className="table-scroll"><pre>{JSON.stringify({before:change.before,after:change.after},null,2)}</pre></div></details>)}
      <label htmlFor={`${id}-confirm`}><input id={`${id}-confirm`} type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/>I checked this exact source-based correction preview.</label>
      <Button disabled={busy||disabled||!confirmed} onClick={()=>void act(async()=>{await request(`${root}/change-sets/${prepared.id}/apply`,{method:'POST',body:{requestId:crypto.randomUUID(),expectedPreviewHash:prepared.preview.previewHash,evaluateApproval:true,releaseTutor:false}});toast.add({title:'Source correction saved; approval policy evaluated. Student release was not requested.',type:'success'});onSaved();})}>Apply correction and check approval</Button>
    </div>}
    {error&&<p role="alert">{error}</p>}
  </details>;
}
