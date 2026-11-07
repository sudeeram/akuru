import json
import os
import stat
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace as Row

import pytest
from pydantic import BaseModel
from app.config import Settings
from app.ai import diagnostics as d


def config(tmp_path, **overrides):
    return Settings(_env_file=None,database_password='database-secret-123',ai_diagnostics_enabled=True,
        ai_diagnostics_capture_content=True,ai_diagnostics_directory=str(tmp_path/'private'),
        openai_account_keys={'MAIN':'sk-demo-key'},**overrides)


def records(settings):
    return [json.loads(line) for path in sorted(__import__('pathlib').Path(settings.ai_diagnostics_directory).glob('model-calls.jsonl*')) for line in path.read_text().splitlines()]


def test_call_captures_payload_and_response_with_same_request_trace_and_no_credentials(tmp_path):
    settings=config(tmp_path)
    class Output(BaseModel): answer: str
    response=Row(id='resp_a',status='completed',output_parsed=Output(answer='A nucleus contains DNA'),usage=Row(total_tokens=30))
    calls=[]
    with d.request_context(settings,'/api/v1/tutoring/sessions/session_a/agent-turns') as trace:
        returned=d.model_call('responses','model-a',{'instructions':'Teach safely','task':json.dumps({'question':'Explain cells','password':'never-write-me'}),'authorization':'Bearer never-write-me','apiKey':'never-write-me','source':'sk-demo-key database-secret-123','pages':[{'hasImage':True}]},lambda:calls.append(1) or response)
        d.api_error('tutor_output_invalid','The Tutor returned inconsistent teaching boundaries.',502)
    assert returned is response and calls==[1]
    rows=records(settings);assert [r['event'] for r in rows]==['model.request','model.response','api.error']
    assert all(r['traceId']==trace for r in rows)
    assert rows[0]['callId']==rows[1]['callId']
    assert rows[1]['content']['output']['answer']=='A nucleus contains DNA'
    text=json.dumps(rows)
    assert 'Explain cells' in text and 'never-write-me' not in text and 'sk-demo-key' not in text and 'database-secret-123' not in text
    assert stat.S_IMODE(os.stat(settings.ai_diagnostics_directory).st_mode)==0o700
    assert stat.S_IMODE(os.stat(settings.ai_diagnostics_directory+'/model-calls.jsonl').st_mode)==0o600


def test_disabled_and_metadata_only_modes(tmp_path):
    settings=config(tmp_path)
    d.record('disabled',settings=settings.model_copy(update={'ai_diagnostics_enabled':False}),content={'question':'private'})
    assert not __import__('pathlib').Path(settings.ai_diagnostics_directory).exists()
    d.record('summary',settings=settings.model_copy(update={'ai_diagnostics_capture_content':False}),content={'question':'private'})
    row=records(settings)[0];assert row['contentCaptured'] is False and 'content' not in row
    assert 'private' not in json.dumps(row)


def test_logs_cannot_change_model_errors_or_make_a_second_call(tmp_path):
    settings=config(tmp_path);calls=[]
    class Failure(RuntimeError): code='provider_timeout'
    def fail():calls.append(1);raise Failure('Bearer never-log-this')
    with pytest.raises(Failure):d.model_call('responses','model-a',{},fail,settings=settings)
    rows=records(settings)
    assert calls==[1] and rows[-1]['event']=='model.error' and rows[-1]['code']=='provider_timeout'
    assert 'never-log-this' not in json.dumps(rows)


def test_filesystem_failure_is_nonfatal_and_symlinks_are_not_followed(tmp_path):
    settings=config(tmp_path)
    directory=__import__('pathlib').Path(settings.ai_diagnostics_directory);directory.mkdir()
    target=tmp_path/'outside';target.write_text('untouched')
    (directory/'model-calls.jsonl').symlink_to(target)
    response=Row(output_parsed=None,id='r',usage=None)
    assert d.model_call('responses','model',{},lambda:response,settings=settings) is response
    assert target.read_text()=='untouched'


def test_image_embedding_and_realtime_outputs_exclude_binary_vectors_and_ephemeral_secret(tmp_path):
    settings=config(tmp_path)
    for kind in ['images','embeddings','realtime-session']:
        response=Row(id='r',value='ephemeral-secret-do-not-log',data=[Row(b64_json='raw-image-do-not-log',embedding=[1234567])],usage=None)
        d.model_call(kind,'model',{'prompt':'a cell'},lambda:response,settings=settings)
    text=json.dumps(records(settings))
    assert 'ephemeral-secret' not in text and 'raw-image' not in text and '1234567' not in text


def test_bounded_rotation_retention_and_concurrent_json_lines(tmp_path):
    settings=config(tmp_path)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i:d.record('parallel',settings=settings,index=i),range(24)))
    assert len(records(settings))==24
    path=__import__('pathlib').Path(settings.ai_diagnostics_directory)/'model-calls.jsonl'
    os.utime(path,(time.time()-9*86400,)*2)
    small=settings.model_copy(update={'ai_diagnostics_max_file_bytes':450})
    for i in range(12):d.record('rotated',settings=small,index=i)
    rows=records(settings)
    assert not any(r['event']=='parallel' for r in rows)
    assert len(list(path.parent.glob('model-calls.jsonl*')))<=6
    assert rows


def test_capture_limit_is_explicit(tmp_path):
    settings=config(tmp_path,ai_diagnostics_max_content_characters=1000)
    d.record('long',settings=settings,content={'text':'x'*2000})
    row=records(settings)[0]
    assert row['contentTruncated'] and len(row['content'])==1000


from test_auth_integration import auth_client  # noqa: E402,F401

@pytest.mark.integration
def test_real_http_error_is_traceable_without_logging_auth_headers(auth_client,monkeypatch,tmp_path):
    import app.main as main
    settings=config(tmp_path)
    monkeypatch.setattr(main,'settings',main.settings.model_copy(update={
        'ai_diagnostics_enabled':True,'ai_diagnostics_capture_content':True,
        'ai_diagnostics_directory':settings.ai_diagnostics_directory}))
    client=auth_client[0]
    response=client.get('/api/v1/tutoring/sessions/missing-session/tools',headers={'Authorization':'Bearer never-log-this'})
    assert response.status_code==401
    trace=response.headers['X-AKURU-Trace-ID']
    rows=records(settings)
    assert any(r['event']=='api.error' and r['status']==401 and r['traceId']==trace for r in rows)
    assert any(r['event']=='http.response' and r['status']==401 for r in rows)
    assert 'never-log-this' not in json.dumps(rows)



def test_real_text_provider_records_each_existing_sdk_attempt_without_image_pixels(tmp_path):
    from test_ai_provider import provider, request, FakeResponses, ExtractionResult, TimeoutResponses
    from app.ai.base import AIProviderError
    settings=config(tmp_path)
    fake=FakeResponses(ExtractionResult(title='Cells',source_pages=[3]))
    with d.request_context(settings,'/api/v1/tutoring/example'):
        provider(fake,max_input_characters=10000).generate(request(image_data_url='data:image/png;base64,YWJj'))
    rows=records(settings)
    assert len(fake.calls)==1 and rows[-1]['content']['output']['title']=='Cells'
    assert rows[0]['content']['pages'][0]['hasImage'] is True
    assert 'YWJj' not in json.dumps(rows)
    timeout=TimeoutResponses()
    with d.request_context(settings,'/api/v1/tutoring/example'):
        with pytest.raises(AIProviderError): provider(timeout,max_retries=1).generate(request())
    rows=records(settings)
    assert timeout.calls==2 and sum(r['event']=='model.error' for r in rows)==2
