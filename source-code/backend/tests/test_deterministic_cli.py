"""Prepared package CLI uses authenticated API replay, not local pass assertions."""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


@pytest.fixture
def cli():
    path = Path(__file__).resolve().parents[2] / 'scripts/deterministic-scoring.py'
    spec = importlib.util.spec_from_file_location('deterministic_cli', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_apply_receipt_and_server_validation(cli, monkeypatch, tmp_path):
    rules = dict(version=3, deterministic=dict(engine='deterministic-v1', matchers=[dict(pointId='P1',kind='choice',accepted=['A'],rejected=['B'])]))
    question = dict(number='1', revision=1, status='approved', analysisContentHash='source-before',
        data=dict(parts=[dict(label='a',scoringRules=dict(version=1),assessmentReadiness='manual_only')]))
    calls = []
    class Client:
        def __init__(self,*args): pass
        def call(self,path,payload=None):
            calls.append((path,payload))
            if path.endswith('/deterministic-capabilities'): return dict(engineHash='e'*64)
            if path.endswith('/deterministic-validations'): return []
            if path.endswith('/validate-deterministic'):
                assert payload['expectedRevision']==2
                assert payload['cases'][0]['answer']=='A'
                assert 'passed' not in payload
                return dict(passed=True,noModelCalls=True,coverageComplete=True)
            if path.endswith('/questions'):
                question.update(data=payload['data'],revision=2,analysisContentHash='source-after')
                return {}
            if path=='auth/logout': return {}
            return dict(questions=[copy.deepcopy(question)])
    monkeypatch.setattr(cli.intake,'Client',Client)
    package=dict(paperId='paper',number='1',partLabel='a',expectedRevision=1,expectedContentHash='source-before',rules=rules,cases=[dict(answer='A',expectedMarks=1,expectedPoints=['P1'])],sourceNotes='Exact original source reviewed.',provenance={})
    file=tmp_path/'package.json';file.write_text(json.dumps(package))
    receipt=tmp_path/'apply.json';output=tmp_path/'validation.json'
    common=['tool','--credentials',str(tmp_path/'secret.env'),'--paper','paper','--number','1','--part','a','--package',str(file)]
    monkeypatch.setattr(sys,'argv',common+['apply','--output',str(receipt)])
    cli.main()
    assert json.loads(receipt.read_text())['appliedContentHash']=='source-after'
    assert receipt.stat().st_mode&0o777==0o600
    monkeypatch.setattr(sys,'argv',common+['validate','--receipt',str(receipt),'--output',str(output)])
    cli.main()
    assert json.loads(output.read_text())['passed']
    package['cases'][0]['expectedMarks']=0;file.write_text(json.dumps(package))
    with pytest.raises(ValueError,match='changed'):
        cli.main()
    assert sum(path.endswith('/validate-deterministic') for path,_ in calls)==1
    # An engine-upgrade replay validates existing rules without reapplying them.
    package['cases'][0]['expectedMarks']=1
    package.update(expectedRevision=2,expectedContentHash='source-after')
    file.write_text(json.dumps(package))
    monkeypatch.setattr(sys,'argv',common+['replay','--output',str(output)])
    cli.main()
    assert sum(path.endswith('/questions') for path,_ in calls)==1
    assert sum(path.endswith('/validate-deterministic') for path,_ in calls)==2



def test_batch_resumes_only_current_server_proofs(cli,monkeypatch,tmp_path):
    from types import SimpleNamespace
    rules=dict(version=3,deterministic=dict(engine='deterministic-v1',matchers=[]))
    package=dict(paperId='paper',number='1',partLabel='a',rules=rules,cases=[dict(answer='A',expectedMarks=1)],sourceNotes='Reviewed exact original source.',provenance={})
    file=tmp_path/'item.json';file.write_text(json.dumps(package))
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps([dict(number='1',partLabel='a',package='item.json')]))
    class Client:
        def __init__(self,*args):pass
        def call(self,path,payload=None):
            if path=='auth/logout':return {}
            if path.endswith('/deterministic-validations'):return [dict(part='a',current=True,passed=True,fixtureHash=cli.case_hash(package['cases']))]
            return dict(questions=[dict(number='1',analysisContentHash='source',data=dict(parts=[dict(label='a',scoringRules=rules,assessmentReadiness='automatic')]))])
    monkeypatch.setattr(cli.intake,'Client',Client)
    def no_replay(*args,**kwargs):pytest.fail('A current identical server certificate must not be repeated')
    monkeypatch.setattr(cli.subprocess,'run',no_replay)
    out=tmp_path/'receipts.json'
    cli.batch(SimpleNamespace(package=manifest,base_url='https://example.test',credentials=tmp_path/'private.env',paper='paper',output=out,enable_tutor=False))
    assert json.loads(out.read_text())==[dict(number='1',part='a',certified=True,resumed=True)]
