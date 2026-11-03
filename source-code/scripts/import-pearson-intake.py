#!/usr/bin/env python3
"""Resumable Admin-API draft intake. Never approves, publishes or edits old reviews.

Default is a source-hash-validated dry run. Keep credential/receipt files ignored.
"""
from __future__ import annotations
import argparse,fcntl,hashlib,http.cookiejar,http.client,json,math,os,re,ssl,time,urllib.error,urllib.parse,urllib.request
from collections import Counter
from pathlib import Path
import certifi
from dotenv import dotenv_values


class Client:
    def __init__(self,origin,credential_file):
        parsed=urllib.parse.urlparse(origin)
        if parsed.scheme!='https' or parsed.path not in {'','/'} or parsed.username or parsed.query:raise ValueError('Use an HTTPS origin without a path or credentials')
        self.origin=origin.rstrip('/');self.csrf=''
        self.opener=urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())),urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        env=dotenv_values(credential_file)
        self.csrf=self.call('auth/login',{'username':env['AKURU_ADMIN_USERNAME'],'password':env['AKURU_ADMIN_PASSWORD']})['csrfToken']
    def call(self,path,body=None,filename=None,_attempt=0):
        headers={'Origin':self.origin};data=None
        if body is not None:
            headers.update({'Content-Type':'application/pdf' if filename else 'application/json','X-CSRF-Token':self.csrf})
            data=body if filename else json.dumps(body).encode()
        if filename:headers['X-Filename']=filename
        try:
            with self.opener.open(urllib.request.Request(self.origin+'/api/v1/'+path,data=data,headers=headers),timeout=240) as response:
                try:return json.load(response)
                except http.client.IncompleteRead:
                    if body is not None or _attempt>=3:raise
                    time.sleep(1)
                    return self.call(path,_attempt=_attempt+1)
        except urllib.error.HTTPError as error:
            if body is None and error.code in {429,502,503,504} and _attempt<3:
                error.close();time.sleep(2**_attempt)
                return self.call(path,_attempt=_attempt+1)
            try:detail=json.loads(error.read()).get('error',{});message=detail.get('message','Request failed');code=detail.get('code','unknown')
            except Exception:message='Request failed';code='unknown'
            raise RuntimeError(f'{error.code} {code}: {message}') from None


def save_private(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.new');fd=os.open(temp,os.O_CREAT|os.O_TRUNC|os.O_WRONLY,0o600)
    os.fchmod(fd,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(data,stream,ensure_ascii=False,indent=2)
    os.replace(temp,path)


def planned_banks(root,keys=None):
    batches=[]
    for file in sorted((root/'.akuru-intake').glob('4*.json')):
        bank=json.loads(file.read_text())
        if bank.get('status')!='local_draft_unreleased' or bank.get('studentAccess') is not False:raise ValueError('Only unreleased drafts may be imported')
        if len(bank['papers'])!=1:raise ValueError('Use one source-bound paper per batch')
        paper=bank['papers'][0]
        if keys and paper['paperKey']not in keys:continue
        for kind,relative in paper['files'].items():
            path=(root/relative).resolve()
            if not path.is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=paper['sourceSha256'][kind]:raise ValueError('Source path/hash mismatch')
        batches.append(bank)
    if keys and set(keys)!={b['papers'][0]['paperKey'] for b in batches}:raise ValueError('Requested paper has no valid draft bank')
    return batches


def await_ready(client,document_id):
    deadline=time.monotonic()+1800
    while time.monotonic()<deadline:
        job=client.call(f'documents/{document_id}/jobs/latest')
        if job['status']in {'needs_review','completed'}:return
        if job['status']=='failed':raise RuntimeError(f"Document processing failed: {job.get('errorCode')}; review/retry through Admin")
        time.sleep(5)
    raise RuntimeError('Document processing pending; rerun safely using receipt')


def same_content(saved, expected):
    # Server may add exact block evidence to the supplied page evidence.
    def clean(data):
        if isinstance(data,dict):
            return {k:(sorted({(item['page'],item.get('assetId')) for item in v},key=str)
                       if k in {'paperSources','schemeSources','reportSources'} else clean(v)) for k,v in data.items()}
        if isinstance(data,list):return [clean(item) for item in data]
        return data
    return clean(saved)==clean(expected)


def drawing_required(prompt):
    return bool(re.search(r'\b(?:draw|sketch)\b.{0,100}\b(?:diagram|graph|line|structure|cell|label|curve)\b|\bplot\b.{0,80}\b(?:graph|grid|point|data|result)',prompt,re.I|re.S))


def enrich_question(q, live, pages):
    data=live['data']
    def sources(numbers,kind):
        lookup={p['pageNumber']:p for p in pages.get(kind,[])}
        return [dict(page=n,assetId=lookup[n]['renderAssetId']) for n in numbers if n in lookup]
    by_label={p['label']:p for p in q['subparts']}
    report=q['source']['reportHeadingCandidatePdfPages']
    for part in data['parts']:
        proposal=by_label[part['label']]
        part['paperSources']=sources(proposal['sourcePages'],'question')
        part['schemeSources']=sources(proposal['schemePages'],'markScheme')
        part['reportSources']=sources(report,'examinerReport')
        raw=proposal['schemeExtractionCandidate']
        # Preserve exact text as unreviewed source transcription, not invented
        # atomic credit rules. A separate editor can turn these into reviewed points.
        part['markingPoints']=proposal.get('proposedMarkingPoints',[])
        part['responseType']='drawing' if drawing_required(part['prompt']) else 'text'
        part['assessmentReadiness']='manual_only'
        part['assessmentReadinessReason']=('Native source proposal only. Marking rules, conditional credit and handwritten report examples require Admin review.\n'+ '\n'.join(q['issues'])+'\n\nExact scheme transcription candidate:\n'+raw)[:4000]
        # Native report text contains candidate examples too; never promote it to examinerAdvice.
        part['examinerAdvice']=''
        part['coverageReason']='Topic mapping not yet reviewed. Use the linked Biology textbook evidence to confirm all concepts and prerequisites.'
    return data



_TOPIC_STOP=set('the and for that this with from are was were which what when where how why explain describe state give name suggest identify calculate using used use answer question figure diagram table following shown show results information student students investigation experiment study mark marks point points some one two three four five each other only more most less than does not can could would should has have had they their these those into about'.split())


def topic_terms(text):
    return {word.lower() for word in re.findall(r"[A-Za-z]{4,}",text) if word.lower() not in _TOPIC_STOP}


def suggest_topics(prompt, topic_evidence):
    terms=topic_terms(prompt)
    corpus=[topic_terms(' '.join(c['text'] for c in item['chunks'])) for item in topic_evidence]
    frequency=Counter(term for vocabulary in corpus for term in vocabulary)
    ranked=[]
    for item,vocabulary in zip(topic_evidence,corpus):
        overlap={term for term in terms & vocabulary if frequency[term]<=4}
        if len(overlap)<3:continue
        score=sum(math.log(1+len(corpus)/frequency[term]) for term in overlap)
        ranked.append((score,item,sorted(overlap)))
    ranked.sort(key=lambda row:(-row[0],row[1]['topicRef']))
    return [(item,terms) for score,item,terms in ranked[:2] if score>=ranked[0][0]*.8] if ranked else []


def topic_reason(q, part, evidence):
    hints=suggest_topics(q.get('sharedStemExtractionCandidate','')+' '+part['prompt'],evidence)
    if not hints:return part['coverageReason']
    return 'Proposed matches only; verify full concepts and prerequisites. '+ '; '.join(item['code']+' '+item['title']+' (source terms: '+', '.join(terms[:8])+')' for item,terms in hints)+'. Original printed-page evidence has not been selected automatically.'


def prepare_rich_seed(bank, evidence):
    bank['reviewProposalVersion']=1
    for q in bank['questions']:
        for part in q['subparts']:
            # Build the same bounded fields as the legacy enrichment path, with
            # no asset IDs: the server resolves pages against the exact versions.
            template={'data':{'parts':[{'label':part['label'],'prompt':part['extractionCandidate']}]}}
            fields=enrich_question(q,template,{})['parts'][0]
            if evidence is not None:fields['coverageReason']=topic_reason(q,fields,evidence)
            part['reviewProposal']={k:fields[k] for k in ('markingPoints','responseType','assessmentReadinessReason','coverageReason')}


def rich_seed_matches(bank, response):
    if bank.get('reviewProposalVersion')!=1:return False
    for q in bank['questions']:
        live=next((item for item in response['questions'] if item['number']==q['number']),None)
        if not live or live['status']!='unreviewed' or live['data']['prompt']!=q['rawQuestionExtraction']:return False
        if len(live['data']['parts'])!=len(q['subparts']):return False
        for part,actual in zip(q['subparts'],live['data']['parts']):
            if actual['label']!=part['label'] or actual['marks']!=part['marks'] or actual['prompt']!=part['extractionCandidate']:return False
            if actual['status']!='unreviewed' or actual['assessmentReadiness']!='manual_only' or actual['topicRefs'] or actual['coverage']!='unreviewed':return False
            for field,expected in part['reviewProposal'].items():
                if field=='markingPoints':expected=[dict(dependsOn=None,followThrough=False,acceptedAnswers=[],**point) for point in expected]
                if actual[field]!=expected:return False
            for field,expected in [('paperSources',part['sourcePages']),('schemeSources',part['schemePages']),('reportSources',q['source']['reportHeadingCandidatePdfPages'])]:
                if {s['page'] for s in actual[field]}!=set(expected):return False
    return True

def run(args):
    root=args.source_root.resolve();banks=planned_banks(root,args.paper_key)
    if not banks:raise ValueError('No source-validated draft banks selected')
    if not args.execute:
        print(json.dumps(dict(mode='dry_run',papers=len(banks),questions=sum(len(b['questions']) for b in banks),files=sum(len(b['papers'][0]['files']) for b in banks),studentAccess=False)));return
    if not args.origin or not args.credentials:raise ValueError('--execute requires --origin and --credentials')
    receipt=args.receipt or root/'.akuru-intake'/'production-receipts.json'
    state=json.loads(receipt.read_text()) if receipt.exists() else dict(origin=args.origin.rstrip('/'),papers={})
    if state['origin']!=args.origin.rstrip('/'):raise ValueError('Receipt belongs to a different origin')
    client=Client(args.origin,args.credentials)
    existing=client.call('documents')['documents'];topic_evidence=None
    for bank in banks:
        paper=bank['papers'][0]
        if 'examinerReport' not in paper['files']:
            bank['provenance']=[{**p,'method':'unknown','notes':'No verified examiner report is attached; absent or quarantined source.'} if p['role']=='report' else p for p in bank['provenance']]
        key=paper['paperKey'];entry=state['papers'].setdefault(key,dict(documents={},seeded=False,enriched=False,visuals=False))
        selected={}
        for kind,relative in paper['files'].items():
            sha=paper['sourceSha256'][kind];api_kind={'question':'past_paper','markScheme':'mark_scheme','examinerReport':'examiner_report'}[kind]
            matches=[d for d in existing if d['checksum']==sha and not d.get('removedAt')]
            if len(matches)>1:raise RuntimeError('Duplicate active source identity; resolve before intake')
            if matches:
                document=matches[0]
                if (document['subjectId'],document['courseId'],document['kind'],document['component'],document['year'],document['session'],document['variant'])!=(bank['subject'],bank['course'],api_kind,paper['component'],paper['year'],paper['session'],paper['variant']):raise RuntimeError('Existing hash has a different source identity')
                if kind!='question' and document['sourceDocumentId']!=selected['question']:raise RuntimeError('Companion is attached to a different paper')
            else:
                params=dict(kind=api_kind,courseId=bank['course'],subjectId=bank['subject'],title=f'Pearson Edexcel {bank["subject"].title()} {paper["session"]} {paper["year"]} {paper["component"]} {api_kind.replace("_"," ")}',year=paper['year'],session=paper['session'],component=paper['component'],variant=paper['variant'],publisher='Pearson')
                if kind!='question':params['sourceDocumentId']=selected['question']
                path=root/relative
                result=client.call('documents?'+urllib.parse.urlencode(params),path.read_bytes(),path.name);document=result['document'];existing.append(document)
            selected[kind]=document['id'];entry['documents'][kind]=dict(id=document['id'],sha256=sha,versionId=document['versionId'])
            save_private(receipt,state)
            print(f'{key} {kind}: uploaded/verified {document["id"]}',flush=True)
        for document_id in selected.values():await_ready(client,document_id)
        endpoint='admin/official-paper-reviews/'+selected['question']
        try:current=client.call(endpoint)
        except RuntimeError as error:
            if not str(error).startswith('404'):raise
            current=None
        expected=len(bank['questions'])
        if current and current['questionCount'] and not entry['seeded']:
            if not entry.get('seedPending') or len(current['questions'])!=expected or any(q['revision']!=1 or q['status']!='unreviewed' for q in current['questions']):
                raise RuntimeError('Review already has questions not owned by this receipt; refusing to modify')
            wanted={q['number']:q for q in bank['questions']}
            if any(q['number'] not in wanted or q['data']['marks']!=wanted[q['number']]['marks'] or q['data']['prompt']!=wanted[q['number']]['rawQuestionExtraction'] for q in current['questions']):raise RuntimeError('Interrupted seed read-back mismatch')
            entry['seeded']=True;entry.pop('seedPending',None);save_private(receipt,state)
        if current and current.get('schemeDocumentId') not in (None, selected['markScheme']):raise RuntimeError('Existing review uses a different scheme')
        if current and current.get('reportDocumentId') not in (None, selected.get('examinerReport')):raise RuntimeError('Existing review uses a different report')
        if not current or (selected.get('examinerReport') and not current.get('reportDocumentId')):
            current=client.call(endpoint+'/start',dict(schemeDocumentId=selected['markScheme'],reportDocumentId=selected.get('examinerReport'),expectedQuestionCount=expected))
        new_seed=False
        if not current['questionCount']:
            if args.suggest_topics and topic_evidence is None:
                topic_evidence=[client.call(endpoint+'/topics/'+topic['topicRef']+'/evidence') for topic in client.call(endpoint+'/topics')]
                save_private(root/'.akuru-intake/topic-evidence.json',topic_evidence)
            prepare_rich_seed(bank,topic_evidence if args.suggest_topics else None)
            entry['seedPending']=True;save_private(receipt,state)
            current=client.call(endpoint+'/seed',dict(draftBank=bank))
            entry['seeded']=True;entry.pop('seedPending',None);new_seed=True;save_private(receipt,state)
        pending=entry.get('pendingQuestion')
        if pending:
            saved=next(q for q in current['questions'] if q['number']==pending['number'])
            if saved['revision']==pending['expectedRevision']+1 and same_content(saved['data'],pending['data']):
                entry.setdefault('enrichedQuestions',{})[pending['number']]=saved['revision']
                entry.pop('pendingQuestion');save_private(receipt,state)
            elif saved['revision']==pending['expectedRevision']:
                entry.pop('pendingQuestion');save_private(receipt,state)
            else:raise RuntimeError('Pending write conflicts with current review; refusing overwrite')
        if args.refresh_generated:entry['enriched']=False
        if new_seed and rich_seed_matches(bank,current):
            entry['enriched']=True
            entry['enrichedQuestions']={q['number']:q['revision'] for q in current['questions']}
            entry['richSeedVersion']=1;save_private(receipt,state)
        if not entry['enriched']:
            # Never overwrite resumed reviews if an Admin has already edited a part.
            if any(q['status']!='unreviewed' or any(p['status']!='unreviewed' for p in q['data']['parts']) for q in current['questions']):raise RuntimeError('Admin review started: skip automated enrichment and review manually')
            if args.suggest_topics and topic_evidence is None:
                topic_evidence=[client.call(endpoint+'/topics/'+topic['topicRef']+'/evidence') for topic in client.call(endpoint+'/topics')]
                save_private(root/'.akuru-intake/topic-evidence.json',topic_evidence)
            pages={kind:client.call(f'documents/{doc}/extraction')['pages'] for kind,doc in selected.items()}
            for q in bank['questions']:
                live=next(item for item in current['questions'] if item['number']==q['number'])
                done=entry.setdefault('enrichedQuestions',{}).get(q['number'])
                if done is not None:
                    if live['revision']!=done:raise RuntimeError('Question changed after enrichment; refusing overwrite')
                    if not args.refresh_generated:continue
                elif live['revision']!=1:raise RuntimeError('Question has edits outside this receipt; refusing overwrite')
                desired=enrich_question(q,live,pages)
                if args.suggest_topics:
                    for part in desired['parts']:
                        part['topicRefs']=[]  # Hints are not confirmed coverage links.
                        part['coverage']='unreviewed'
                        part['coverageReason']=topic_reason(q,part,topic_evidence)
                pending=dict(number=q['number'],expectedRevision=live['revision'],status='unreviewed',data=desired)
                entry['pendingQuestion']=pending;save_private(receipt,state)
                try:
                    updated=client.call(endpoint+'/questions',pending)
                except (http.client.IncompleteRead,TimeoutError,ConnectionError):
                    # The write may have committed. Read back; do not repeat a POST.
                    updated=client.call(endpoint)
                    saved=next(item for item in updated['questions'] if item['number']==q['number'])
                    if saved['revision']!=pending['expectedRevision']+1 or not same_content(saved['data'],desired):raise RuntimeError('Ambiguous write; pending receipt retained for manual reconciliation')
                entry['enrichedQuestions'][q['number']]=next(item['revision'] for item in updated['questions'] if item['number']==q['number'])
                entry.pop('pendingQuestion',None);save_private(receipt,state)
            entry['enriched']=True;save_private(receipt,state)
        if not entry['visuals']:
            before_visuals=client.call(endpoint)
            for question in before_visuals['questions']:
                if question['revision']!=entry['enrichedQuestions'][question['number']]:raise RuntimeError('Review changed before visual generation')
            entry['visualCandidates']=client.call(endpoint+'/visual-candidates/generate',{});entry['visuals']=True
            after_visuals=client.call(endpoint)
            for question in after_visuals['questions']:
                before=next(q for q in before_visuals['questions'] if q['number']==question['number'])
                original=dict(before['data']);changed=dict(question['data']);original.pop('candidateVisualAssetIds',None);changed.pop('candidateVisualAssetIds',None)
                if question['revision'] not in {before['revision'],before['revision']+1} or not same_content(original,changed):raise RuntimeError('Unexpected review changes during visual generation')
                entry['enrichedQuestions'][question['number']]=question['revision']
            save_private(receipt,state)
        verified=client.call(endpoint)
        assert verified['questionCount']==expected and verified['approvedCount']==0
        for question in verified['questions']:
            old=question.get('extractionAnalysis')
            if old and old.get('isCurrent'):continue
            def estimate(scope):
                triage=scope.get('extractionConfidence') or {'percent':0,'reasons':['No extraction estimate available.']}
                return dict(percent=min(70,triage['percent']),reasons=triage['reasons'],sourceChecks=[
                    dict(role=role,status='not_checked' if kind in selected else 'not_available',percent=None,pages=[],
                        reasons=['Native extraction triage only; semantic correctness and exact visual/report interpretation require review.'])
                    for role,kind in [('paper','question'),('scheme','markScheme'),('report','examinerReport')]])
            part_estimates=[dict(label=p['label'],**estimate(p)) for p in question['data']['parts']]
            overall=estimate(question['data']);overall['percent']=min(overall['percent'],*(p['percent'] for p in part_estimates))
            analysis=client.call(endpoint+'/questions/'+question['number']+'/analyses',dict(
                expectedQuestionRevision=question['revision'],expectedAnalysisVersion=question['analysisVersion'],
                expectedContentHash=question['analysisContentHash'],stage='extraction',methodVersion=bank.get('extractorVersion','pearson-native-layout-v1'),
                provenance=bank['provenance'],question=overall,parts=part_estimates))
            entry.setdefault('analysisVersions',{})[question['number']]=analysis['version'];save_private(receipt,state)
        entry.update(status='draft_review_ready',questionCount=expected,reviewUrl=args.origin.rstrip('/')+'/admin/exam-documents/review/'+selected['question'])
        save_private(receipt,state);print(f'{key}: {expected} questions ready for Admin review',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source_root',type=Path);parser.add_argument('--paper-key',action='append');parser.add_argument('--origin');parser.add_argument('--credentials',type=Path);parser.add_argument('--receipt',type=Path);parser.add_argument('--execute',action='store_true');parser.add_argument('--suggest-topics',action='store_true');parser.add_argument('--refresh-generated',action='store_true',help='Refresh only drafts whose exact last revisions are in this receipt');args=parser.parse_args()
    if args.execute:
        lockpath=args.source_root/'.akuru-intake/intake.lock';lockpath.parent.mkdir(parents=True,exist_ok=True)
        with lockpath.open('a') as lock:
            os.chmod(lockpath,0o600)
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise SystemExit('Another intake is running for this source root')
            run(args)
    else:run(args)
