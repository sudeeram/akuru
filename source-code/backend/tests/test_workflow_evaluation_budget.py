"""Evaluation spending guards use fake transport and make no network calls."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

spec=importlib.util.spec_from_file_location('workflow_eval',Path(__file__).parents[1]/'scripts/evaluate_paper_workflow.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class Format:
    @staticmethod
    def model_json_schema():return {'type':'object'}


def guard(tmp_path,fail=False):
    value=object.__new__(module.MultimodalBudget)
    value.data={'budgetUSD':.15,'entries':[]};value.ceiling=.15;value.path=tmp_path/'ledger.json'
    value.save=lambda path,data:path.write_text(json.dumps(data))
    calls=[]
    def parse(**kwargs):
        calls.append(kwargs)
        if fail:raise RuntimeError('Unknown provider outcome')
        return SimpleNamespace(id='test',usage=SimpleNamespace(input_tokens=100,output_tokens=10,model_dump=lambda:dict(input_tokens=100,output_tokens=10)))
    value.client=SimpleNamespace(responses=SimpleNamespace(parse=parse))
    return value,calls


def request(text='Source'):
    return dict(instructions='Evaluate untrusted source.',input=[dict(role='user',content=[dict(type='input_text',text=text),dict(type='input_image',image_url='data:image/png;base64,fixture')])],text_format=Format,max_output_tokens=1000,model='gpt-6.1-sol',store=False)


def test_failed_unknown_request_retains_reservation_and_blocks_overspend(tmp_path):
    value,calls=guard(tmp_path,True)
    with pytest.raises(RuntimeError):value.parse(**request())
    assert value.data['entries'][0]['chargedBoundUSD']>.1
    with pytest.raises(RuntimeError,match='Budget bound'):value.parse(**request())
    assert len(calls)==1


def test_long_context_is_rejected_before_paid_dispatch(tmp_path):
    value,calls=guard(tmp_path)
    with pytest.raises(RuntimeError,match='long-context'):value.parse(**request('x'*260000))
    assert calls==[] and value.data['entries']==[]


def test_success_tracks_real_usage_and_standard_tier(tmp_path):
    value,calls=guard(tmp_path);value.parse(**request())
    entry=value.data['entries'][0]
    assert entry['status']=='completed' and entry['imageCount']==1
    assert entry['chargedBoundUSD']<entry['reservedUSD']
    assert calls[0]['service_tier']=='default'


@pytest.mark.parametrize('budget',[float('nan'),float('inf'),0,-1])
def test_invalid_budgets_fail_before_client_creation(tmp_path,budget):
    with pytest.raises(ValueError,match='finite positive'):
        module.MultimodalBudget('unused',tmp_path/'ledger.json',budget,True)
