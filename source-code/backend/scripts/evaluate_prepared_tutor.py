"""Opt-in, budget-bounded live evaluation of the real Tutor service on private packages.

No default paid calls: use --live only with an explicitly authorised dollar budget.
Creates and drops a disposable schema on localhost, never touches normal app tables.
All material/results must stay in a Git-ignored local output directory.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import dotenv_values


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as f:json.dump(data,f,ensure_ascii=False,indent=2,default=str)
    temporary.replace(path)


class BudgetClient:
    """No retries; reserve a conservative full request before dispatch.

    Unknown usage retains the full reservation. A resumed run uses the same ledger.
    This is a local spend bound at the recorded Standard rates, not billing retrieval.
    """
    def __init__(self, key, ledger, ceiling, live):
        from openai import OpenAI
        import httpx
        self.client=OpenAI(api_key=key,max_retries=0,timeout=60,http_client=httpx.Client(trust_env=False)) if live else None
        self.path=ledger;self.live=live;self.ceiling=ceiling;self.case_id=None;self.requests=[]
        import fcntl
        ledger.parent.mkdir(parents=True,exist_ok=True)
        self.lock=open(str(ledger)+'.lock','a')
        os.chmod(str(ledger)+'.lock',0o600)
        fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.data=json.loads(ledger.read_text()) if ledger.exists() else {'budgetUSD':ceiling,'entries':[]}
        if self.data['budgetUSD']!=ceiling:raise ValueError('Existing ledger uses another budget; do not reset or overwrite it.')
        self.responses=self

    def parse(self,**kwargs):
        from app.schemas.tutor_agent import TutorProviderOutput
        if not self.live:
            from types import SimpleNamespace
            task=json.loads(kwargs['input'][0]['content'][0]['text'])
            refs=[c['citationRef'] for c in task['approvedCitations']][:1]
            if kwargs['text_format'].__name__ == 'TutorTeachingOutput':
                response = kwargs['text_format'](answerBasis='grounded' if refs else 'supplementary',
                    groundedContent='Dry-run pipeline check.' if refs else '',
                    additionalContent='' if refs else 'Dry-run additional explanation.', boundaryContent='',
                    citationRefs=refs, followUpChoices=[], proposedSignals=[])
            else:
                response = TutorProviderOutput(content='Dry-run pipeline check; not a teaching-quality response.',citationRefs=refs)
            return SimpleNamespace(output_parsed=response,usage=SimpleNamespace(input_tokens=0,output_tokens=0,total_tokens=0),id='dry-run')
        if any(part.get('type')!='input_text' for row in kwargs['input'] for part in row['content']):
            raise RuntimeError('This evaluation budget implementation accepts text input only.')
        # Byte count is a deliberately conservative text-token upper bound. Add
        # 10,000 tokens for schema/protocol overhead, reject unexpectedly large input.
        schema=kwargs['text_format'].model_json_schema()
        body=json.dumps({'instructions':kwargs['instructions'],'input':kwargs['input'],'schema':schema},ensure_ascii=False)
        upper_input=len(body.encode('utf-8'))+10000
        if upper_input>60000:raise RuntimeError('Evaluation input exceeds the conservative token budget.')
        output=kwargs['max_output_tokens']
        # Reserve above recorded Standard input/cache-write and output rates.
        reserve=upper_input*3/1_000_000 + output*12/1_000_000
        committed=sum(entry.get('chargedBoundUSD',0) for entry in self.data['entries'])
        if committed+reserve>self.ceiling:raise RuntimeError('Evaluation budget exhausted before request; no request dispatched.')
        entry={'caseId':self.case_id,'reservedUSD':reserve,'chargedBoundUSD':reserve,'status':'reserved',
               'model':kwargs['model'],'timeUTC':datetime.now(timezone.utc).isoformat()}
        self.data['entries'].append(entry);save(self.path,self.data)
        task=json.loads(kwargs['input'][0]['content'][0]['text'])
        kwargs['service_tier']='default'
        try:
            response=self.client.responses.parse(**kwargs)
            usage=response.usage
            if usage is not None:
                raw=usage.model_dump();inp=usage.input_tokens;out=usage.output_tokens
                cached=(raw.get('input_tokens_details') or {}).get('cached_tokens',0) or 0
                estimated=((inp-cached)*2+cached*.1+out*10)/1_000_000
                bound=(inp*3+out*12)/1_000_000
                entry.update({'status':'completed','usage':raw,'estimatedUSD':estimated,
                              'chargedBoundUSD':min(reserve,bound),'responseId':response.id})
            else:entry['status']='completed_usage_unknown'
            self.requests.append({'caseId':self.case_id,'task':task,'usage':entry.get('usage'),
                                  'estimatedUSD':entry.get('estimatedUSD'),'responseId':response.id})
            save(self.path,self.data)
            return response
        except Exception as exc:
            # Never save provider bodies/messages: they can echo credentials.
            entry.update({'status':'failed_usage_unknown','errorType':type(exc).__name__})
            save(self.path,self.data)
            raise

    def close(self):
        if self.client:self.client.close()
        self.lock.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for option in ['package','decisions','cases','credentials','output','ledger']:parser.add_argument('--'+option,type=Path,required=True)
    parser.add_argument('--budget-usd',type=float,default=2)
    parser.add_argument('--live',action='store_true')
    parser.add_argument('--supplementary',action='store_true',help='Evaluate the separately gated supplementary teaching prompt.')
    args=parser.parse_args()
    if not 0<args.budget_usd<=2:raise SystemExit('This reviewed pilot allows at most US$2.')
    if args.output.exists() and list(args.output.glob('case-*.json')):raise SystemExit('Use a new output folder; retain the existing budget ledger across reruns.')
    creds=dotenv_values(args.credentials)
    key=creds.get('OPENAI_API_KEY');model=creds.get('OPENAI_MODEL')
    if not key or model!='gpt-6.1-sol':raise SystemExit('Evaluation credentials must contain a key and OPENAI_MODEL=gpt-6.1-sol.')
    backend=dotenv_values(Path('.env'))
    other=dotenv_values(args.credentials.parent/'akuru-openclaw.env')
    backend_keys = set(json.loads(backend.get('AKURU_OPENAI_ACCOUNT_KEYS') or '{}').values())
    backend_keys.update({backend.get('AKURU_OPENAI_API_KEY'),other.get('OPENAI_API_KEY')})
    if key in backend_keys:
        raise SystemExit('Evaluation key must be separate from backend/OpenClaw keys.')
    # Process-only overrides. No credentials/environment file is modified.
    overrides={'AKURU_OPENAI_API_KEY':key,'AKURU_OPENAI_MODEL':model,
       'AKURU_OPENAI_ACCOUNT_KEYS':json.dumps({'EVALUATION':key}),'AKURU_AI_PROVIDER':'openai',
       'AKURU_EMBEDDING_PROVIDER':'local','AKURU_AI_MAX_RETRIES':'0','AKURU_AI_MAX_OUTPUT_TOKENS':'4000',
       'AKURU_AI_MAX_INPUT_CHARACTERS':'24000','AKURU_TUTOR_TEXT_ENABLED':'true',
       'AKURU_TUTOR_TOOLS_ENABLED':'true','AKURU_TUTOR_VOICE_ENABLED':'false',
       'AKURU_TUTOR_RELEASE_GATES_REQUIRED':'false','AKURU_COOKIE_SECURE':'false',
       'AKURU_TUTOR_SUPPLEMENTARY_ENABLED':str(args.supplementary).lower()}
    os.environ.update(overrides)
    from sqlalchemy import create_engine,select,text
    from sqlalchemy.orm import Session
    from app.config import get_settings
    from app.database import Base
    from app import models as m
    from app.security import Principal,hash_password
    from app.seed_catalog import seed
    from app.storage.local import LocalObjectStorage
    from app.services import prepared_textbooks as prepared,textbook_structures as books,tutor_profiles,tutor_sessions,tutor_agent
    from app.schemas.prepared_textbooks import PreparedReviewRequest
    from app.schemas.textbook_structures import TextbookCreateRequest,GroupSaveRequest,TopicSaveRequest,PublishStructureRequest,PublishTopicContentRequest
    from app.schemas.tutor_profiles import TutorProfileInput
    from app.schemas.tutor_sessions import TutorSessionStartRequest,TutorEndSessionRequest
    from app.schemas.tutor_agent import TutorAgentTurnRequest
    from app.ai.provider import OpenAIProvider
    settings=get_settings()
    if settings.database_host not in {'localhost','127.0.0.1','::1'}:raise SystemExit('Evaluation requires a localhost database.')
    cases=json.loads(args.cases.read_text())
    if not 1<=len(cases)<=20:raise SystemExit('Use 1–20 predeclared questions.')
    schema='akuru_eval_'+uuid.uuid4().hex
    engine=create_engine(settings.database_url)
    budget=BudgetClient(key,args.ledger,args.budget_usd,args.live)
    result={'model':model,'live':args.live,'budgetUSD':args.budget_usd,'schema':schema,
      'packageSha256':hashlib.sha256(args.package.read_bytes()).hexdigest(),
      'casesSha256':hashlib.sha256(args.cases.read_bytes()).hexdigest(),
      'ratesUSDPerMillion':{'input':2,'cachedInput':.1,'output':10},
      'rateSource':'https://developers.openai.com/api/docs/models/gpt-6.1-sol',
      'retrieval':'existing local hash embeddings; no paid embeddings',
      'boundary':'Real Tutor service and OpenAIProvider, injected budget client; synthetic learner in disposable schema. No browser/production release. No image pixels sent to model.',
      'cases':[]}
    args.output.mkdir(parents=True,exist_ok=True)
    created=False;connection=None;db=None;transaction=None
    try:
        with engine.begin() as setup:setup.execute(text(f'CREATE SCHEMA "{schema}"'))
        created=True
        connection=engine.connect().execution_options(schema_translate_map={None:schema})
        Base.metadata.create_all(connection);connection.commit()
        transaction=connection.begin();db=Session(bind=connection,join_transaction_mode='create_savepoint',expire_on_commit=False)
        seed(db)
        admin=m.User(username='eval-admin',display_name='Evaluation administrator',role='admin',password_hash=hash_password(uuid.uuid4().hex),must_change_password=False)
        parent=m.User(username='eval-parent',display_name='Synthetic parent',role='parent',password_hash=hash_password(uuid.uuid4().hex),must_change_password=False)
        student=m.User(username='eval-student',display_name='Synthetic learner',role='student',password_hash=hash_password(uuid.uuid4().hex),must_change_password=False)
        db.add_all([admin,parent,student]);db.flush()
        db.add(m.StudentProfile(student_id=student.id,parent_id=parent.id));db.flush()
        db.add_all([m.StudentSubject(student_id=student.id,subject_id='chemistry'),m.StudentProgression(student_id=student.id,course_id='igcse',grade=10,term=1,is_current=True)])
        db.commit();ap=Principal(user=admin,session=None);sp=Principal(user=student,session=None)
        book=books.create_textbook(db,ap,TextbookCreateRequest(courseId='igcse',subjectId='chemistry',title='Topic 1 local teaching evaluation',edition='source edition unverified — evaluation only',publisher='owner-supplied screenshots',groupLabel='unit'))
        book=books.save_group(db,ap,book.textbookRef,GroupSaveRequest(code='1',title='Principles of Chemistry',summary='',sequence=1))
        book=books.save_topic(db,ap,book.textbookRef,book.groups[0].groupRef,TopicSaveRequest(code='1',title='States of Matter',sequence=1))
        topic_ref=book.groups[0].topics[0].topicRef
        with tempfile.TemporaryDirectory(prefix='akuru-tutor-evaluation-') as directory:
            storage=LocalObjectStorage(Path(directory))
            imported=prepared.import_package(db,storage,ap,book.textbookRef,topic_ref,args.package.read_bytes())
            docid=uuid.UUID(imported['documentId'])
            state=prepared.review_state(db,book.textbookRef,topic_ref,docid)
            notes=json.loads(args.decisions.read_text())['decisions']
            prepared.confirm_review(db,ap,book.textbookRef,topic_ref,docid,PreparedReviewRequest(contentHash=state['contentHash'],confirmWholeDocument=True,decisions=notes))
            for asset in books.list_topic_visual_assets(db,book.textbookRef,topic_ref,str(docid)):
                books.update_topic_visual_asset(db,ap,book.textbookRef,topic_ref,str(docid),asset.assetRef,'approved',asset.caption,asset.altText)
            books.update_topic_source_role(db,ap,book.textbookRef,topic_ref,str(docid),'primary')
            books.publish_structure(db,ap,book.textbookRef,PublishStructureRequest(confirmCourse=True,confirmSubject=True,confirmEdition=True,confirmStructure=True))
            books.publish_topic_content(db,ap,book.textbookRef,topic_ref,PublishTopicContentRequest(confirmSources=True,confirmExtraction=True,confirmTopic=True))
            topic=db.scalar(select(m.TextbookTopic).where(m.TextbookTopic.public_ref==topic_ref))
            plan=m.CurriculumPlan(course_id='igcse',subject_id='chemistry',textbook_id=topic.textbook_id,version_number=1,status='published',created_by=admin.id,published_by=admin.id,published_at=datetime.now(timezone.utc))
            db.add(plan);db.flush();db.add(m.CurriculumPlanTopic(plan_id=plan.id,grade=10,term=1,topic_id=topic.id));db.commit()
            profile=tutor_profiles.create(db,sp,TutorProfileInput(name='Evaluation Tutor',presentation='neutral',avatarCode='akuru-spark',voiceCode='bright-companion',tone='encouraging',explanationDepth='standard'))
            provider=OpenAIProvider(api_key=key,model=model,timeout_seconds=60,max_retries=0,max_concurrency=1,max_pages=8,max_input_characters=24000,max_image_bytes=1024,max_output_tokens=4000,client=budget)
            sessions={}; active_session=None
            for case in cases:
                group=case.get('sessionGroup',case['id'])
                if group not in sessions:
                    if active_session:
                        tutor_sessions.end(db,settings,sp,active_session,TutorEndSessionRequest(requestKey='eval-end-'+uuid.uuid4().hex))
                    sessions[group]=tutor_sessions.start(db,settings,sp,TutorSessionStartRequest(subjectId='chemistry',topicRef=topic_ref,profileRef=profile.profileRef,requestKey='eval-session-'+uuid.uuid4().hex)).sessionRef
                    active_session=sessions[group]
                budget.case_id=case['id'];before=len(budget.requests);started=time.monotonic()
                row={**case,'status':'pending'}
                try:
                    reply=tutor_agent.complete_turn(db,settings,sp,sessions[group],TutorAgentTurnRequest(message=case['message'],teachingMode=case.get('teachingMode','explanation'),requestKey='eval-turn-'+uuid.uuid4().hex),generator=lambda request,operation:provider.generate(request))
                    row.update({'status':'completed','response':reply.model_dump(mode='json'),'providerCalled':len(budget.requests)>before,
                                'request':budget.requests[-1] if len(budget.requests)>before else None})
                    # Source/asset integrity is deterministic and distinct from semantic review.
                    row['checks']={'citationRefsAuthorised':True,'printedLabelsPresent':all(c.printedPageLabel for c in reply.citations),'visualAssetsAccessible':True}
                    for c in reply.citations:
                        asset_id=uuid.UUID(hex=c.assetRef.removeprefix('asset_'));asset=db.get(m.DocumentAsset,asset_id)
                        if not asset or not storage.exists(asset.object_key):row['checks']['visualAssetsAccessible']=False
                except Exception as exc:
                    row.update({'status':'failed','errorType':type(exc).__name__,'safeErrorCode':getattr(exc,'code',None)})
                    if hasattr(exc,'errors'):
                        row['validationErrors']=[{'loc':err['loc'],'type':err['type'],'message':err['msg']} for err in exc.errors(include_input=False,include_url=False)]
                    import traceback
                    row['errorFrames']=[{'file':Path(frame.filename).name,'line':frame.lineno,'function':frame.name} for frame in traceback.extract_tb(exc.__traceback__)]
                    # Stop on operational errors; do not repeatedly spend against an invalid setup.
                    result['cases'].append(row);save(args.output/f"case-{case['id']}.json",row)
                    print(f"Case {case['id']}: failed ({row['errorType']}); stopping.",flush=True)
                    break
                row['elapsedSeconds']=round(time.monotonic()-started,2)
                result['cases'].append(row);save(args.output/f"case-{case['id']}.json",row)
                print(f"Case {case['id']}: {row['status']}; provider called={row.get('providerCalled')}; {row['elapsedSeconds']}s",flush=True)
        result['fixtureCompleted']=True
    except Exception as exc:
        result['setupError']={'type':type(exc).__name__,'safeCode':getattr(exc,'code',None)}
        print('Evaluation stopped:',type(exc).__name__,getattr(exc,'code',''),flush=True)
    finally:
        if db:db.close()
        if transaction and transaction.is_active:transaction.rollback()
        if connection:connection.close()
        if created:
            with engine.begin() as cleanup:cleanup.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose();budget.close()
        result['schemaDropped']=created
        result['usageLedger']=budget.data
        save(args.output/'results.json',result)
        print('Saved local evaluation report. Disposable schema removed:',created,flush=True)
    if result.get('setupError') or any(r['status']=='failed' for r in result['cases']):raise SystemExit(1)


if __name__=='__main__':main()
