'use client';
/* Effects load remote Admin media/source inventories when the selected subject changes. */
/* eslint-disable react/react-compiler */
import { useEffect, useState } from 'react';
import { api, errorMessage, type EducationalMedia, type MediaSource, type State } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Picker, Empty } from './shared';
import { LearningImage } from './learning-media';

export function MediaAdmin({ data, notify }: { data: State; notify: (message: string) => void }) {
  const [subject,setSubject]=useState('maths'),[sources,setSources]=useState<MediaSource[]>([]),[sourceId,setSourceId]=useState('');
  const [items,setItems]=useState<EducationalMedia[]>([]),[kind,setKind]=useState('geometry_svg');
  const [title,setTitle]=useState('Triangle angle guide'),[alt,setAlt]=useState('A labelled triangle showing its three interior angles.');
  const [parameters,setParameters]=useState('{"angleA":50,"angleB":60}'),[prompt,setPrompt]=useState('Show the concept clearly using a simple scientific classroom illustration.');
  const [notes,setNotes]=useState('Checked against the linked textbook evidence.'),[busy,setBusy]=useState(false),[error,setError]=useState(''),[loading,setLoading]=useState(true);
  async function loadMedia(){setLoading(true);setError('');try{setItems(((await api('media')) as {media:EducationalMedia[]}).media);}catch(cause){setError(errorMessage(cause));}finally{setLoading(false);}}
  useEffect(()=>{void loadMedia();},[]);
  useEffect(()=>{let active=true;void api(`media/admin/sources?subjectId=${encodeURIComponent(subject)}`).then(value=>{if(active){const rows=value as MediaSource[];setSources(rows);setSourceId(rows[0]?.id||'');}}).catch(cause=>{if(active)setError(errorMessage(cause));});return()=>{active=false};},[subject]);
  async function create(event:React.SyntheticEvent<HTMLFormElement>){event.preventDefault();setBusy(true);setError('');try{
    const body={subjectId:subject,sourceChunkId:sourceId,title,altText:alt};
    if(kind==='conceptual_image') await api('media/admin/illustrations',{...body,prompt});
    else {let parsed;try{parsed=JSON.parse(parameters);}catch{throw new Error('Parameters must be valid JSON.');}await api('media/admin/deterministic',{...body,kind,parameters:parsed});}
    await loadMedia();notify(kind==='conceptual_image'?'Illustration generated privately and queued for review.':'Validated visual published.');
  }catch(cause){setError(errorMessage(cause));}finally{setBusy(false);}}
  async function review(id:string,decision:'published'|'rejected'){setBusy(true);setError('');try{await api(`media/admin/${id}/review`,{decision,notes});await loadMedia();notify(`Media ${decision.replace('published','published')}.`);}catch(cause){setError(errorMessage(cause));}finally{setBusy(false);}}
  return <><form className="panel stack" onSubmit={create}><h2>Create source-grounded visual</h2><p>Controlled SVG and plots publish from validated code. OpenAI illustrations remain private until reviewed.</p>
    <div className="two-cols"><Picker label="Subject" value={subject} onChange={setSubject} options={data.subjects.map(row=>({value:row.id,label:row.name}))}/><Picker label="Visual type" value={kind} onChange={setKind} options={[['geometry_svg','Geometry SVG'],['forces_svg','Forces SVG'],['circuit_svg','Circuit SVG'],['plot_svg','Numerical plot'],['conceptual_image','OpenAI conceptual illustration']].map(([value,label])=>({value,label}))}/></div>
    <Picker label="Approved source evidence" value={sourceId} onChange={setSourceId} options={sources.map(row=>({value:row.id,label:`${row.unitCode} · ${row.documentTitle} · page ${row.page}`}))}/>
    {!sources.length&&<p className="source-note">No approved indexed textbook evidence exists for this subject. Publish and index a textbook first.</p>}
    <label htmlFor="media-title">Title<Input id="media-title" value={title} minLength={2} maxLength={180} required onChange={e=>setTitle(e.target.value)}/></label>
    <label htmlFor="media-alt">Accessible description<Textarea id="media-alt" value={alt} minLength={10} maxLength={1000} required onChange={e=>setAlt(e.target.value)}/></label>
    {kind==='conceptual_image'?<label htmlFor="media-prompt">Illustration request<Textarea id="media-prompt" value={prompt} minLength={20} maxLength={4000} required onChange={e=>setPrompt(e.target.value)}/></label>:<label htmlFor="media-parameters">Validated parameters (JSON)<Textarea id="media-parameters" value={parameters} required onChange={e=>setParameters(e.target.value)}/><small>Triangle: angleA/angleB. Forces: left/right. Circuit: voltage/resistance. Plot: points as [[x,y],...].</small></label>}
    {error&&<div className="error" role="alert">{error}</div>}<Button className="primary" type="submit" disabled={busy||!sourceId}>{busy?'Creating…':'Create visual'}</Button></form>
    <section className="spaced"><div className="section-heading"><h2>Private media review</h2><Button variant="outline" onClick={()=>void loadMedia()}>Refresh</Button></div>{loading&&<output>Loading visual media…</output>}
      <div className="learner-grid">{items.map(item=><article className="panel stack" key={item.id}><span className="eyebrow">{item.kind.replaceAll('_',' ')} · {item.status.replaceAll('_',' ')}</span><h3>{item.title}</h3><LearningImage src={item.contentUrl} description={item.altText}/><p className="small">{item.provider}/{item.model} · prompt {item.promptVersion}</p><p className="source-note">Evidence: {item.sourceManifest.map(source=>`${source.documentTitle} · ${source.unitCode} · page ${source.page}`).join('; ')}</p>{item.provider==='openai'&&item.status==='pending_review'&&<><label htmlFor={`media-review-${item.id}`}>Review notes<Textarea id={`media-review-${item.id}`} value={notes} onChange={e=>setNotes(e.target.value)}/></label><div className="button-row"><Button variant="outline" disabled={busy} onClick={()=>void review(item.id,'rejected')}>Reject</Button><Button disabled={busy} onClick={()=>void review(item.id,'published')}>Publish illustration</Button></div></>}</article>)}</div>
      {!loading&&!items.length&&<Empty title="No visual media yet">Create a controlled visual or a conceptual illustration above.</Empty>}</section></>;
}
