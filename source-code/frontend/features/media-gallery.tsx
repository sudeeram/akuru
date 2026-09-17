'use client';
import { useEffect, useState } from 'react';
import { api, errorMessage, type EducationalMedia } from '@/lib/api';
import { LearningImage } from './learning-media';
export function MediaGallery({studentId,subjectId}:{studentId:string;subjectId:string}){
 const [items,setItems]=useState<EducationalMedia[]>([]),[error,setError]=useState('');
 useEffect(()=>{let active=true;void api(`media?studentId=${studentId}&subjectId=${encodeURIComponent(subjectId)}`).then(value=>{if(active)setItems((value as {media:EducationalMedia[]}).media)}).catch(cause=>{if(active)setError(errorMessage(cause))});return()=>{active=false}},[studentId,subjectId]);
 if(error)return <p className="error" role="alert">Visual explanations could not load. Reopen this subject to retry.</p>;
 if(!items.length)return null;
 return <section className="spaced"><div className="section-heading"><h2>Visual explanations</h2></div><div className="learner-grid">{items.map(item=><article className="panel" key={item.id}><h3>{item.title}</h3><LearningImage src={`${item.contentUrl}?studentId=${studentId}`} description={item.altText}/><p className="source-note">Supporting visual. Official source evidence: {item.sourceManifest.map(source=>`${source.documentTitle}, ${source.topicCode}, page ${source.page}`).join('; ')}</p></article>)}</div></section>;
}
