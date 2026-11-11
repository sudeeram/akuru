"""Opt-in, one-question live source/curriculum evaluation through authenticated APIs.

Run from the repository root. Defaults to dry run. Outputs contain licensed source
material and MUST be Git ignored. --apply requires --live and explicit operator
approval; it records a current assessment and retries guarded Tutor releases,
never edits wording, image decisions, rubric readiness or manual mappings.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'source-code/backend'))
from dotenv import dotenv_values
from app.ai.base import AIRequest, SourcePage
from app.ai.provider import OpenAIProvider
from app.schemas.accuracy_jobs import AccuracyJobRequest, ModelAccuracy
from app.services.accuracy_jobs import _assessment
from app.services.paper_curriculum import resolve


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


class MultimodalBudget:
    """Reserve text byte upper bound + 20k tokens/image, no retries.

    Uses the existing evaluation ledger's recorded conservative Standard rates
    ($3/M input, $12/M output), not a billing API or a guarantee for arbitrary
    models. Operator must confirm these rates bound the selected model.
    Unknown usage retains the full reservation. Never reuse a different budget.
    """
    def __init__(self, key, ledger, ceiling, rate_confirmed):
        if not rate_confirmed:
            raise ValueError('Confirm the recorded rates bound this evaluation model.')
        from openai import OpenAI
        import httpx, fcntl, os
        self.save = module('save_eval', ROOT/'source-code/backend/scripts/evaluate_prepared_tutor.py').save
        self.path=ledger; self.ceiling=ceiling
        ledger.parent.mkdir(parents=True,exist_ok=True)
        self.lock=open(str(ledger)+'.lock','a');os.chmod(str(ledger)+'.lock',0o600)
        fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.data=json.loads(ledger.read_text())if ledger.exists()else dict(budgetUSD=ceiling,entries=[])
        if self.data['budgetUSD']!=ceiling:raise ValueError('Budget ledger mismatch; do not reset it.')
        self.client=OpenAI(api_key=key,max_retries=0,timeout=180,http_client=httpx.Client(trust_env=False))
        self.responses=self

    def parse(self,**kwargs):
        images=sum(p.get('type')=='input_image'for r in kwargs['input']for p in r['content'])
        text=[p for r in kwargs['input']for p in r['content']if p.get('type')=='input_text']
        body=json.dumps(dict(instructions=kwargs['instructions'],text=text,schema=kwargs['text_format'].model_json_schema()),ensure_ascii=False)
        upper=len(body.encode())+10000+images*20000
        if upper>250000:raise RuntimeError('Refusing long-context pricing before dispatch.')
        reservation=(upper*3+kwargs['max_output_tokens']*12)/1_000_000
        if sum(e['chargedBoundUSD']for e in self.data['entries'])+reservation>self.ceiling:
            raise RuntimeError('Budget bound exceeded; no request sent.')
        entry=dict(timeUTC=datetime.now(timezone.utc).isoformat(),status='reserved',model=kwargs['model'],
            imageCount=images,reservedUSD=reservation,chargedBoundUSD=reservation)
        entry.update(pricingSource='https://developers.openai.com/api/docs/models/gpt-6.1-sol',pricingVerified='2026-11-11',rateBoundInputPerMillion=3,rateBoundOutputPerMillion=12)
        self.data['entries'].append(entry);self.save(self.path,self.data)
        try:
            response=self.client.responses.parse(**kwargs,service_tier='default')
            usage=response.usage
            if usage:
                bound=(usage.input_tokens*3+usage.output_tokens*12)/1_000_000
                entry.update(status='completed',usage=usage.model_dump(),chargedBoundUSD=min(reservation,bound),responseId=response.id)
            else:entry['status']='completed_usage_unknown'
            self.save(self.path,self.data);return response
        except Exception as exc:
            entry.update(status='failed_usage_unknown',errorType=type(exc).__name__)
            self.save(self.path,self.data);raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--origin',required=True);p.add_argument('--credentials',type=Path,required=True)
    p.add_argument('--evaluation-env',type=Path,required=True);p.add_argument('--paper',required=True)
    p.add_argument('--number',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--budget',type=float,default=2);p.add_argument('--live',action='store_true')
    p.add_argument('--apply',action='store_true');p.add_argument('--confirm-recorded-rate-bound',action='store_true')
    args=p.parse_args()
    import subprocess
    ignored=subprocess.run(['git','check-ignore','-q',str(args.output)],cwd=ROOT).returncode==0
    if not ignored:raise ValueError('Evaluation output must be Git ignored.')
    if args.apply and not args.live:raise ValueError('--apply requires --live')
    intake=module('intake',ROOT/'source-code/scripts/import-pearson-intake.py')
    client=intake.Client(args.origin,args.credentials);base='admin/official-paper-reviews/'+args.paper
    try:
        review=client.call(base);q=next(v for v in review['questions']if v['number']==args.number)
        context=client.call(base+'/questions/'+args.number+'/accuracy-context')
        intake.save_private(args.output/'context.json',context)
        if not args.live:
            print('Context captured; no model call or production mutation.');return
        env=dotenv_values(args.evaluation_env)
        if not env['OPENAI_MODEL'].startswith('gpt-6.1-sol'):
            raise ValueError('This recorded price guard is verified only for GPT-6.1 Sol.')
        budget=MultimodalBudget(env['OPENAI_API_KEY'],args.output/'budget-ledger.json',args.budget,args.confirm_recorded_rate_bound)
        provider=OpenAIProvider(api_key=env['OPENAI_API_KEY'],model=env['OPENAI_MODEL'],timeout_seconds=180,
            max_retries=0,max_concurrency=1,max_pages=24,max_input_characters=200000,
            max_image_bytes=4000000,max_output_tokens=8000,client=budget)
        result=provider.generate(AIRequest(purpose='paper_extraction',prompt_name='final-source-accuracy',
            prompt_version=context['promptVersion'],instructions=context['instructions'],task=context['task'],
            output_type=ModelAccuracy,pages=tuple(SourcePage(**v)for v in context['pages'])))
        row=SimpleNamespace(review_data=q['data'])
        mapped,checks=resolve(None,result.output,context['curriculumSources'],row)
        if mapped!=row.review_data:raise ValueError('Evaluation proposes new mappings; use the queued workflow to apply them.')
        request=AccuracyJobRequest(requestId=__import__('uuid').uuid4(),number=q['number'],expectedRevision=context['revision'],
            expectedContentHash=context['contentHash'],expectedAnalysisVersion=context['analysisVersion'])
        previous=SimpleNamespace(analysis_data=q['accuracyAnalysis'])if q.get('accuracyAnalysis')else None
        payload=_assessment(result,row,request,previous,context['allowedPages'],checks)
        # This is a real external API evaluation, distinct from original extraction.
        intake.save_private(args.output/'assessment.json',dict(payload=payload.model_dump(mode='json'),usage=asdict(result.usage)))
        print('Evaluation complete; model:',result.model,'input/output tokens:',result.usage.input_tokens,result.usage.output_tokens)
        if args.apply:
            recorded=client.call(base+'/questions/'+args.number+'/analyses',payload.model_dump(mode='json'))
            released=client.call(base+'/auto-tutor-release',{})
            intake.save_private(args.output/'receipt.json',dict(assessment=recorded,releases=released))
            print('Current assessment recorded; guarded releases checked. Manual decisions preserved.')
    finally:
        try:client.call('auth/logout',{})
        except json.JSONDecodeError:pass

if __name__=='__main__':main()
