'use client';
/* Form labels wrap design-system inputs; the accessibility rule does not resolve their rendered controls. */
/* eslint-disable jsx-a11y/label-has-associated-control */
import { useEffect, useState } from 'react';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  getDocumentExtraction, getPaperReview, getReviewTopicEvidence, getReviewTopics,
  savePaperReviewQuestion, seedPaperReview, startPaperReview, prepareOfficialReviewDrafts, errorMessage,
  type Doc, type DocumentExtraction, type PaperReview, type ReviewQuestionData,
  type ReviewPart, type ReviewStatus, type CoverageStatus,
} from '@/api';

const reviewStatuses: ReviewStatus[] = ['unreviewed', 'needs_correction', 'ready_for_approval', 'approved', 'excluded'];
const coverageStatuses: CoverageStatus[] = ['unreviewed', 'supported', 'partial_or_uncertain', 'outside_current_coverage'];
const label = (value: string) => value.replaceAll('_', ' ');

function emptyPart(): ReviewPart {
  return {label: 'a', marks: 1, prompt: '', markingPoints: [], alternatives: [], examinerAdvice: '',
    paperSources: [], schemeSources: [], reportSources: [], coverage: 'unreviewed', topicRefs: [], coverageReason: '', status: 'unreviewed'};
}
function emptyQuestion(): ReviewQuestionData {
  return {marks: 1, sharedStem: '', prompt: '', paperSources: [], visualAssetIds: [], visualAltText: '',
    parts: [emptyPart()], exclusionReason: ''};
}

function SourcePage({documentId, extraction, title, selectedPage, onPage, onAttach, onAttachBlock}: {
  documentId?: string|null; extraction?: DocumentExtraction|null; title: string;
  selectedPage: number; onPage: (value: number) => void; onAttach?: () => void;
  onAttachBlock?: (blockId: string) => void;
}) {
  const page = extraction?.pages.find((item) => item.pageNumber === selectedPage);
  return <section className="panel stack" style={{minWidth: 0}} aria-label={`${title} evidence`}>
    <strong>{title}</strong>
    {!documentId ? <p>No source attached.</p> : !extraction ? <p>Loading reviewed source pages…</p> : <>
      <div className="button-row">
        <label>PDF page <Input type="number" min={1} max={extraction.pages.length} value={selectedPage} onChange={(event) => onPage(Number(event.target.value))} style={{width: 85}}/></label>
        <span>of {extraction.pages.length}</span>
        {onAttach && <Button variant="outline" disabled={!page} onClick={onAttach}>Link this page</Button>}
      </div>
      {page ? <>
        <span className="small">{page.printedPageLabel ? `Book page ${page.printedPageLabel}` : `PDF page ${page.pageNumber}`}</span>
        <Image src={`/api/v1/documents/${documentId}/assets/${page.originalRenderAssetId || page.renderAssetId}/content`}
          alt={`${title}, page ${page.pageNumber}`} width={800} height={1100} unoptimized
          style={{width:'100%',height:'auto',maxHeight:520,objectFit:'contain',objectPosition:'top',borderRadius:8}}/>
        <details><summary>Extracted blocks · link exact evidence</summary>{page.blocks.map((block) => <div key={block.id} className="panel stack"><p className="small">{block.text.slice(0,600) || block.kind}</p>{onAttachBlock && <Button variant="outline" onClick={() => onAttachBlock(block.id)}>Link this block</Button>}</div>)}</details>
      </> : <p>Choose a valid page.</p>}
    </>}
  </section>;
}

export function OfficialPaperReview({paperId, documents, navigate}: {
  paperId: string; documents: Doc[]; navigate: (path: string) => void;
}) {
  const paper = documents.find((document) => document.id === paperId);
  const companions = documents.filter((document) => document.paperId === paperId || document.id === paperId);
  const [review, setReview] = useState<PaperReview|null>(null);
  const [schemeId, setSchemeId] = useState('');
  const [reportId, setReportId] = useState('');
  const [expectedCount, setExpectedCount] = useState('');
  const [draftFile, setDraftFile] = useState<File|null>(null);
  const [triageFile, setTriageFile] = useState<File|null>(null);
  const [topics, setTopics] = useState<{topicRef:string;code:string;title:string}[]>([]);
  const [evidence, setEvidence] = useState<{pageNumber:number;text:string}[]>([]);
  const [evidenceTopic, setEvidenceTopic] = useState('');
  const [selected, setSelected] = useState('');
  const [number, setNumber] = useState('');
  const [data, setData] = useState<ReviewQuestionData>(emptyQuestion());
  const [status, setStatus] = useState<ReviewStatus>('unreviewed');
  const [revision, setRevision] = useState(0);
  const [activePart, setActivePart] = useState(0);
  const [paperExtraction, setPaperExtraction] = useState<DocumentExtraction|null>(null);
  const [schemeExtraction, setSchemeExtraction] = useState<DocumentExtraction|null>(null);
  const [reportExtraction, setReportExtraction] = useState<DocumentExtraction|null>(null);
  const [paperPage, setPaperPage] = useState(1);
  const [schemePage, setSchemePage] = useState(1);
  const [reportPage, setReportPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    let active = true;
    void getPaperReview(paperId).then((value) => {if (active) setReview(value);}).catch(() => {});
    void getReviewTopics(paperId).then((value) => {if (active) setTopics(value);}).catch(() => {});
    void getDocumentExtraction(paperId).then((value) => {if (active) setPaperExtraction(value);}).catch(() => {});
    return () => { active = false; };
  }, [paperId]);
  useEffect(() => {
    if (!review?.schemeDocumentId) return;
    let active = true;
    void getDocumentExtraction(review.schemeDocumentId).then((value) => {if (active) setSchemeExtraction(value);}).catch(() => {});
    return () => {active = false;};
  }, [review?.schemeDocumentId]);
  useEffect(() => {
    if (!review?.reportDocumentId) return;
    let active = true;
    void getDocumentExtraction(review.reportDocumentId).then((value) => {if (active) setReportExtraction(value);}).catch(() => {});
    return () => {active = false;};
  }, [review?.reportDocumentId]);
  useEffect(() => {
    if (!evidenceTopic) return;
    let active = true;
    void getReviewTopicEvidence(paperId, evidenceTopic).then((value) => {if(active) setEvidence(value.chunks);}).catch(() => {});
    return () => {active=false;};
  }, [paperId, evidenceTopic]);

  async function act(action: () => Promise<PaperReview>, message: string) {
    setBusy(true); setError(''); setNotice('');
    try { const value = await action(); setReview(value); if (number) {
      const row = value.questions.find((question) => question.number === number);
      if (row) chooseQuestion(row);
    } setNotice(message); }
    catch (cause) {setError(errorMessage(cause));}
    finally {setBusy(false);}
  }
  function chooseQuestion(row: PaperReview['questions'][number]) {
    setSelected(row.number); setNumber(row.number); setData(structuredClone(row.data));
    setStatus(row.status); setRevision(row.revision); setActivePart(0);
    setPaperPage(row.data.paperSources[0]?.page || 1);
    setSchemePage(row.data.parts[0]?.schemeSources[0]?.page || 1);
    setReportPage(row.data.parts[0]?.reportSources[0]?.page || 1);
  }
  function updatePart(next: ReviewPart) {
    setData((current) => ({...current, parts: current.parts.map((part, index) => index === activePart ? next : part)}));
  }
  const part = data.parts[activePart];
  const pageAsset = (extraction: DocumentExtraction|null, pageNumber: number) => extraction?.pages.find((row) => row.pageNumber === pageNumber)?.renderAssetId;
  function linkPage(kind: 'paper'|'scheme'|'report', blockId?: string) {
    const [extraction, pageNumber, field] = kind === 'paper' ? [paperExtraction,paperPage,'paperSources'] as const :
      kind === 'scheme' ? [schemeExtraction,schemePage,'schemeSources'] as const : [reportExtraction,reportPage,'reportSources'] as const;
    const assetId = pageAsset(extraction, pageNumber);
    if (!assetId || !part) return;
    const entry = {page:pageNumber,assetId,blockId:blockId||null};
    if (kind === 'paper') setData((current) => ({...current,paperSources: current.paperSources.some((s) => s.page === pageNumber && s.blockId === (blockId||null)) ? current.paperSources : [...current.paperSources,entry]}));
    updatePart({...part,[field]: part[field].some((source) => source.page === pageNumber && source.blockId === (blockId||null)) ? part[field] : [...part[field],entry]});
  }
  const markingText = part?.markingPoints.map((point) => `${point.code}|${point.kind}|${point.text}${point.dependsOn ? `|${point.dependsOn}` : ''}`).join('\n') || '';
  const sourceList = (sources: {page:number}[]) => sources.map((source) => source.page).join(', ') || 'None';

  if (!paper) return <section className="panel"><p>Past paper not found.</p><Button onClick={() => navigate('/admin/exam-documents/past-papers')}>Back to papers</Button></section>;
  return <div className="stack">
    <section className="panel stack"><div className="spread"><div><h2>Official-paper review · {paper.name}</h2><p>Admin-only draft. Saving or approving a question does not release it to Students.</p></div><Button variant="outline" onClick={() => navigate('/admin/exam-documents/past-papers')}>Back to papers</Button></div>
      {error && <p className="error" role="alert">{error}</p>}{notice && <output>{notice}</output>}
      {!review ? <div className="stack">
        <label>Exact marking scheme <select value={schemeId} onChange={(event) => setSchemeId(event.target.value)}><option value="">Attach later</option>{companions.filter((doc) => doc.kind === 'Marking scheme').map((doc) => <option key={doc.id} value={doc.id}>{doc.name}</option>)}</select></label>
        <label>Examiner report <select value={reportId} onChange={(event) => setReportId(event.target.value)}><option value="">Absent or attach later</option>{companions.filter((doc) => doc.kind === 'Examiner report').map((doc) => <option key={doc.id} value={doc.id}>{doc.name}</option>)}</select></label>
        <label>Expected complete question count <Input type="number" min={0} max={200} value={expectedCount} onChange={(event) => setExpectedCount(event.target.value)}/></label>
        <Button disabled={busy || !paperExtraction} onClick={() => void act(() => startPaperReview(paperId,{schemeDocumentId:schemeId||null,reportDocumentId:reportId||null,expectedQuestionCount:Number(expectedCount)||0}), 'Review workspace created.')}>Start Admin review</Button>
      </div> : <>
        <p><strong>{review.approvedCount} approved / {review.questionCount} saved / {review.expectedQuestionCount || 'unknown'} expected</strong> · {review.wholePaperReady ? 'Internal review complete' : 'Review incomplete'}</p>
        {review.blockers.map((blocker) => <p key={blocker} className="small">• {blocker}</p>)}
        {review.wholePaperReady && <Button variant="outline" disabled={busy} onClick={() => {
          setBusy(true); setError('');
          void prepareOfficialReviewDrafts(paperId)
            .then(() => setNotice('Official paper and exact-scheme drafts prepared. Review and publish each source separately from Exam Documents. Student access remains closed until the published pairing passes.'))
            .catch((cause) => setError(errorMessage(cause)))
            .finally(() => setBusy(false));
        }}>Prepare official paper and scheme drafts</Button>}
        {(!review.schemeDocumentId || !review.reportDocumentId) && <div className="button-row">
          {!review.schemeDocumentId && <label>Attach scheme <select value={schemeId} onChange={(event) => setSchemeId(event.target.value)}><option value="">Choose</option>{companions.filter((doc) => doc.kind === 'Marking scheme').map((doc) => <option key={doc.id} value={doc.id}>{doc.name}</option>)}</select></label>}
          {!review.reportDocumentId && <label>Attach report <select value={reportId} onChange={(event) => setReportId(event.target.value)}><option value="">Optional</option>{companions.filter((doc) => doc.kind === 'Examiner report').map((doc) => <option key={doc.id} value={doc.id}>{doc.name}</option>)}</select></label>}
          <Button variant="outline" disabled={busy || (!schemeId && !reportId)} onClick={() => void act(() => startPaperReview(paperId,{schemeDocumentId:schemeId||null,reportDocumentId:reportId||null}), 'Source attached.')}>Attach selected source</Button>
        </div>}
      </>}
    </section>
    {review && <>
      {review.questionCount === 0 && <section className="panel stack"><h3>Import draft proposals</h3><p>Use the private unreleased bank only after uploading the exact source PDFs. Every imported item remains unapproved.</p>
        <label>Draft bank JSON <Input type="file" accept="application/json,.json" onChange={(event) => setDraftFile(event.target.files?.[0]||null)}/></label>
        <label>Optional coverage triage JSON <Input type="file" accept="application/json,.json" onChange={(event) => setTriageFile(event.target.files?.[0]||null)}/></label>
        <Button disabled={!draftFile || busy} onClick={() => void act(async () => seedPaperReview(paperId,JSON.parse(await draftFile!.text()) as object,triageFile ? JSON.parse(await triageFile.text()) as object:undefined),'Unapproved source proposals imported.')}>Import proposals for review</Button>
      </section>}
      <div className="button-row" aria-label="Question review navigation">
        {review.questions.map((question) => <Button key={question.number} variant={selected===question.number?'default':'outline'} onClick={() => chooseQuestion(question)}>{question.number} · {label(question.status)}</Button>)}
        <Button variant="outline" onClick={() => {setSelected('');setNumber('');setRevision(0);setStatus('unreviewed');setData(emptyQuestion());}}>Add question</Button>
      </div>
      <section className="panel stack"><div className="two-cols"><label>Question number <Input value={number} disabled={revision>0} onChange={(event) => setNumber(event.target.value)}/></label><label>Marks <Input type="number" min={1} value={data.marks} onChange={(event) => setData({...data,marks:Number(event.target.value)})}/></label></div>
        <label>Shared stem <Textarea value={data.sharedStem} onChange={(event) => setData({...data,sharedStem:event.target.value})}/></label>
        <label>Full reviewed question prompt <Textarea rows={6} value={data.prompt} onChange={(event) => setData({...data,prompt:event.target.value})}/></label>
        <p className="small">Linked paper pages: {sourceList(data.paperSources)}</p>
        <label>Question status <select value={status} onChange={(event) => setStatus(event.target.value as ReviewStatus)}>{reviewStatuses.map((item) => <option key={item} value={item}>{label(item)}</option>)}</select></label>
        {status==='excluded' && <label>Exclusion reason <Textarea value={data.exclusionReason} onChange={(event) => setData({...data,exclusionReason:event.target.value})}/></label>}
        <div className="button-row">{data.parts.map((row,index) => <Button key={index} variant={activePart===index?'default':'outline'} onClick={() => setActivePart(index)}>{row.label} · {row.marks} marks</Button>)}<Button variant="outline" onClick={() => {setData({...data,parts:[...data.parts,{...emptyPart(),label:String.fromCharCode(97+data.parts.length)}]});setActivePart(data.parts.length);}}>Add subpart</Button></div>
        {part && <div className="panel stack"><div className="two-cols"><label>Subpart label <Input value={part.label} onChange={(event) => updatePart({...part,label:event.target.value})}/></label><label>Subpart marks <Input type="number" min={1} value={part.marks} onChange={(event) => updatePart({...part,marks:Number(event.target.value)})}/></label></div>
          <label>Reviewed subpart wording <Textarea rows={4} value={part.prompt} onChange={(event) => updatePart({...part,prompt:event.target.value})}/></label>
          <label>Exact marking points · code|kind|text|optional dependency <Textarea rows={5} value={markingText} onChange={(event) => updatePart({...part,markingPoints:event.target.value.split('\n').filter(Boolean).map((line,index) => {const [code,kind,text,dependsOn]=line.split('|');return {code:code||`P${index+1}`,kind:(['method','accuracy','independent','communication'].includes(kind)?kind:'other') as ReviewPart['markingPoints'][number]['kind'],text:text||'',dependsOn:dependsOn||null};})})}/></label>
          <label>Accepted alternatives · one per line <Textarea value={part.alternatives.join('\n')} onChange={(event) => updatePart({...part,alternatives:event.target.value.split('\n').filter(Boolean)})}/></label>
          <label>Examiner guidance <Textarea value={part.examinerAdvice} onChange={(event) => updatePart({...part,examinerAdvice:event.target.value})}/></label>
          <p className="small">Paper pages: {sourceList(part.paperSources)} · Scheme pages: {sourceList(part.schemeSources)} · Report pages: {sourceList(part.reportSources)}</p>
          <label>Coverage decision <select value={part.coverage} onChange={(event) => updatePart({...part,coverage:event.target.value as CoverageStatus,topicRefs:[]})}>{coverageStatuses.map((value) => <option value={value} key={value}>{label(value)}</option>)}</select></label>
          {part.coverage==='supported' && <fieldset><legend>Published Chemistry topics</legend>{topics.map((topic) => <label key={topic.topicRef} style={{display:'block'}}><input type="checkbox" checked={part.topicRefs.includes(topic.topicRef)} onChange={(event) => updatePart({...part,topicRefs:event.target.checked?[...part.topicRefs,topic.topicRef]:part.topicRefs.filter((ref) => ref!==topic.topicRef)})}/> {topic.code} · {topic.title}</label>)}</fieldset>}
          <label>Coverage reason <Textarea value={part.coverageReason} onChange={(event) => updatePart({...part,coverageReason:event.target.value})}/></label>
          <label>Subpart review status <select value={part.status} onChange={(event) => updatePart({...part,status:event.target.value as ReviewStatus})}>{reviewStatuses.filter((item) => item!=='excluded').map((value) => <option value={value} key={value}>{label(value)}</option>)}</select></label>
        </div>}
        <label>Approved visual asset IDs · one per line <Textarea value={data.visualAssetIds.join('\n')} onChange={(event) => setData({...data,visualAssetIds:event.target.value.split('\n').map((value) => value.trim()).filter(Boolean)})}/></label>
        <label>Accessible visual description <Textarea value={data.visualAltText} onChange={(event) => setData({...data,visualAltText:event.target.value})}/></label>
        <Button disabled={busy || !number.trim()} onClick={() => void act(() => savePaperReviewQuestion(paperId,{number,expectedRevision:revision,status,data}), 'Question review saved.')}>
          Save question review</Button>
      </section>
      <div className="two-cols" style={{alignItems:'start'}}>
        <SourcePage documentId={paperId} extraction={paperExtraction} title="Question paper" selectedPage={paperPage} onPage={setPaperPage} onAttach={part?()=>linkPage('paper'):undefined} onAttachBlock={part?(id)=>linkPage('paper',id):undefined}/>
        <SourcePage documentId={review.schemeDocumentId} extraction={schemeExtraction} title="Exact marking scheme" selectedPage={schemePage} onPage={setSchemePage} onAttach={part?()=>linkPage('scheme'):undefined} onAttachBlock={part?(id)=>linkPage('scheme',id):undefined}/>
        <SourcePage documentId={review.reportDocumentId} extraction={reportExtraction} title="Examiner report" selectedPage={reportPage} onPage={setReportPage} onAttach={part?()=>linkPage('report'):undefined} onAttachBlock={part?(id)=>linkPage('report',id):undefined}/>
        <section className="panel stack"><strong>Published textbook evidence</strong><select aria-label="Textbook topic" value={evidenceTopic} onChange={(event) => {setEvidenceTopic(event.target.value);setEvidence([]);}}><option value="">Choose topic</option>{topics.map((topic) => <option value={topic.topicRef} key={topic.topicRef}>{topic.code} · {topic.title}</option>)}</select><div style={{maxHeight:520,overflow:'auto'}}>{evidence.map((chunk,index) => <details key={`${chunk.pageNumber}-${index}`}><summary>Extracted page {chunk.pageNumber}</summary><p>{chunk.text}</p></details>)}</div><p className="small">Text similarity does not approve a mapping; check the assessed concept and source page.</p></section>
      </div>
    </>}
  </div>;
}
