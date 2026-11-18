"""Exercise real temporary Git histories; no production/service mutations."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[3]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'deploy/ubuntu'/f'{name}.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
planner=load('release-plan');cache=load('dependency-cache')

@pytest.fixture
def repo(tmp_path,monkeypatch):
    monkeypatch.setattr(planner,"runtime_versions",lambda r:{"frontend":"fixture-node","backend":"fixture-python"})
    subprocess.run(['git','init','-q',str(tmp_path)],check=True)
    (tmp_path/'source-code/frontend/dist/server').mkdir(parents=True)
    def commit(path):
        p=tmp_path/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('change\n'+p.read_text() if p.exists() else 'new\n')
        subprocess.run(['git','-C',str(tmp_path),'add','--',path],check=True)
        subprocess.run(['git','-C',str(tmp_path),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
        return planner.git(tmp_path,'rev-parse','HEAD')
    base=commit('README.md');env=tmp_path/'runtime.env';env.write_text('non-secret fixture')
    state=tmp_path/'accepted.json'
    state.write_text(json.dumps(dict(schema=1,accepted=True,release_sha=base,
        environment_sha256=hashlib.sha256(env.read_bytes()).hexdigest(),runtimes=planner.runtime_versions(tmp_path))))
    # A real deployed environment has a backend interpreter. Tests replace just this runtime probe.
    return tmp_path,commit,state,env

@pytest.mark.parametrize('path,expected',[
 ('source-code/frontend/features/chat.tsx',(True,False,False,False)),
 ('source-code/backend/app/services/marking.py',(False,True,False,False)),
 ('source-code/backend/migrations/versions/001.py',(False,True,True,False)),
 ('source-code/backend/app/seed_catalog.py',(False,True,False,True)),
 ('user-docs/guide.md',(False,False,False,False)),
 ('guidelines/pastpapers/guide.md',(False,False,False,False)),
 ('source-code/frontend/docs/architecture.md',(False,False,False,False)),
 ('source-code/scripts/run-web.mjs',(True,True,True,True)),
 ('deploy/ubuntu/install-services.sh',(True,True,True,True)),
 ('unknown-runtime.conf',(True,True,True,True)),
])
def test_selects_changed_components(repo,monkeypatch,path,expected):
    root,commit,state,env=repo
    monkeypatch.setattr(planner,'runtime_versions',lambda r:json.loads(state.read_text())['runtimes'])
    target=commit(path);result=planner.plan(root,target,state,env)
    assert tuple(result[k] for k in ('frontend','backend','migrations','catalog'))==expected
    assert result['backup']==any(expected[:2])
    assert result['accepted'] is False


def test_missing_unaccepted_unknown_or_nonancestor_baseline_forces_full(repo,monkeypatch):
    root,commit,state,env=repo;target=commit('user-docs/x.md')
    for content in ['broken',json.dumps({'schema':1,'accepted':False}),json.dumps({'schema':1,'accepted':True,'release_sha':'f'*40})]:
        state.write_text(content);assert planner.plan(root,target,state,env)['full']
    state.unlink();assert planner.plan(root,target,state,env)['full']


def test_env_or_runtime_change_and_explicit_full(repo,monkeypatch):
    root,commit,state,env=repo;target=commit('user-docs/x.md')
    old=json.loads(state.read_text());runtime=old['runtimes']|{'frontend':'changed-node'}
    monkeypatch.setattr(planner,'runtime_versions',lambda r:runtime)
    p=planner.plan(root,target,state,env);assert p['frontend'] and not p['backend']
    assert planner.plan(root,target,state,env,True)['full']
    env.write_text('different fixture');assert planner.plan(root,target,state,env)['full']


def test_missing_frontend_output_is_rebuilt(repo,monkeypatch):
    root,commit,state,env=repo
    monkeypatch.setattr(planner,'runtime_versions',lambda r:json.loads(state.read_text())['runtimes'])
    (root/'source-code/frontend/dist/server').rmdir()
    p=planner.plan(root,planner.git(root,'rev-parse','HEAD'),state,env)
    assert p['frontend'] and p['backup']


def test_dependency_receipts_require_identical_inputs_runtime_and_inventory(tmp_path):
    path=tmp_path/'cache/backend.json';original=dict(schema=1,inputs=[('lock','hash')],runtime='runtime',inventory='packages')
    assert not cache.matches(path,original)
    cache.record(path,original);assert cache.matches(path,original)
    for key in ('inputs','runtime','inventory'):
        assert not cache.matches(path,original|{key:'changed'})
    path.write_text('bad');assert not cache.matches(path,original)
    assert path.stat().st_mode & 0o077 == 0


def test_inventory_failures_are_not_reused(tmp_path,monkeypatch):
    def broken(*args):raise subprocess.CalledProcessError(1,['fixture'])
    monkeypatch.setattr(cache,'capture',broken)
    with pytest.raises(subprocess.CalledProcessError):cache.snapshot('frontend',tmp_path)


def test_shell_has_read_only_plan_lock_and_acceptance_before_state_advance():
    path=ROOT/'deploy/ubuntu/deploy-reviewed-release.sh';s=path.read_text()
    subprocess.run(['bash','-n',str(path)],check=True)
    assert 'flock -n 9' in s and '--plan' in s
    assert s.index('run_stage acceptance')<s.index('run_stage accepted_baseline')
    assert 'systemctl restart "${services[@]}"' in s
    assert 'timings-${run_id}.tsv' in s


def test_dependency_snapshot_detects_file_and_actual_inventory_drift(tmp_path,monkeypatch):
    folder=tmp_path/'frontend';folder.mkdir()
    (folder/'package.json').write_text('{}');(folder/'package-lock.json').write_text('{"lockfileVersion":3}')
    inventory=[b'{"dependencies":{}}']
    def fake(command,cwd):
        if command[:2]==['npm','ls']:return inventory[0]
        return b'fixture-version'
    monkeypatch.setattr(cache,'capture',fake)
    first=cache.snapshot('frontend',tmp_path)
    (folder/'package-lock.json').write_text('{"lockfileVersion":3,"changed":true}')
    second=cache.snapshot('frontend',tmp_path)
    assert first['inputs']!=second['inputs'] and first['inventory']==second['inventory']
    inventory[0]=b'{"dependencies":{"unexpected":{}}}'
    third=cache.snapshot('frontend',tmp_path)
    assert third['inventory']!=second['inventory']


def test_plan_cli_does_not_create_deployment_evidence(repo):
    root,commit,state,env=repo
    target=commit('source-code/frontend/features/example.tsx')
    output=subprocess.check_output(['python3',str(ROOT/'deploy/ubuntu/release-plan.py'),
        '--root',str(root),'--target',target,'--state',str(state),'--environment-file',str(env)])
    assert json.loads(output)['release_sha']==target
    assert not list(root.glob('timings-*'))
    assert json.loads(state.read_text())['release_sha']!=target
