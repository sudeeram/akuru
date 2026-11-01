"""Spend guard tests use a fake transport; never call OpenAI or a database."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from pydantic import BaseModel

spec=importlib.util.spec_from_file_location('evaluation_runner',Path(__file__).parents[1]/'scripts/evaluate_prepared_tutor.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class Output(BaseModel):
    content:str


def arguments():
    return dict(model='gpt-6.1-sol',instructions='Teach from evidence.',input=[{'role':'user','content':[{'type':'input_text','text':json.dumps({'approvedCitations':[]})}]}],text_format=Output,max_output_tokens=4000,store=False)


def test_budget_reserves_before_transport_and_preserves_unknown_spend(tmp_path):
    budget=runner.BudgetClient('unused',tmp_path/'ledger.json',2,False);budget.live=True
    def fail(**kwargs):raise TimeoutError('unknown response')
    budget.client=SimpleNamespace(responses=SimpleNamespace(parse=fail),close=lambda:None)
    try:
        with pytest.raises(TimeoutError):budget.parse(**arguments())
        entry=json.loads(budget.path.read_text())['entries'][0]
        assert entry['chargedBoundUSD']==entry['reservedUSD']>0
        assert entry['status']=='failed_usage_unknown'
    finally:budget.close()


def test_budget_blocks_before_dispatch_and_reconciles_reported_usage(tmp_path):
    ledger=tmp_path/'ledger.json'
    budget=runner.BudgetClient('unused',ledger,2,False);budget.live=True
    calls=[]
    def response(**kwargs):
        calls.append(kwargs)
        raw={'input_tokens':500,'output_tokens':50,'total_tokens':550,'input_tokens_details':{'cached_tokens':20}}
        return SimpleNamespace(id='test',usage=SimpleNamespace(**raw,model_dump=lambda:raw))
    budget.client=SimpleNamespace(responses=SimpleNamespace(parse=response),close=lambda:None)
    try:
        budget.parse(**arguments())
        assert len(calls)==1 and calls[0]['service_tier']=='default'
        entry=budget.data['entries'][0]
        assert entry['chargedBoundUSD']<entry['reservedUSD']
        assert entry['estimatedUSD']==pytest.approx((480*2+20*.1+50*10)/1e6)
        budget.data['entries'].append({'chargedBoundUSD':1.999})
        with pytest.raises(RuntimeError,match='budget exhausted'):budget.parse(**arguments())
        assert len(calls)==1
    finally:budget.close()
