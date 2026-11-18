#!/usr/bin/env python3
"""Conservative Git-based release selection; never executes application changes."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


def runtime_versions(root):
    result = {}
    for name, command in [('frontend', ['node', '--version']),
                          ('backend', [str(Path(root)/'source-code/backend/.venv/bin/python'), '--version'])]:
        try:result[name] = subprocess.check_output(command, stderr=subprocess.DEVNULL).decode().strip()
        except (OSError, subprocess.CalledProcessError):result[name] = None
    return result


def plan(root, target, state_path, environment_file=None, force=False):
    target = git(root, 'rev-parse', target + '^{commit}')
    flags = dict(frontend=False, backend=False, migrations=False, catalog=False)
    reasons = []
    env_hash = hashlib.sha256(Path(environment_file).read_bytes()).hexdigest() if environment_file else None
    try:
        state = json.loads(Path(state_path).read_text())
        baseline = state['release_sha']
        if state.get('schema') != 1 or not state.get('accepted'):
            raise ValueError('Unaccepted baseline')
        git(root, 'merge-base', '--is-ancestor', baseline, target)
        if env_hash is None or env_hash != state.get('environment_sha256'):
            reasons.append('Runtime environment changed or cannot be verified')
            force = True
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError):
        baseline = None
        force = True
        reasons.append('No verified ancestor deployment baseline; full deployment required')
    runtimes = runtime_versions(root)
    if baseline is not None:
        for component, version in runtimes.items():
            if version is None or state.get('runtimes', {}).get(component) != version:
                flags[component] = True
                reasons.append(component + ' runtime changed or cannot be verified')
    paths = [] if baseline is None else subprocess.check_output(
        ['git','-C',str(root),'diff','--no-renames','--name-only','-z',baseline,target]).decode().split('\0')[:-1]
    for path in paths:
        if path.startswith(('source-code/frontend/tests/', 'source-code/frontend/docs/',
                            'source-code/backend/tests/', 'source-code/backend/docs/',
                            'source-code/todo/', 'source-code/docs/', 'developer-docs/', 'user-docs/',
                            'guidelines/', '.github/', 'openclaw/')) or path in ('README.md', 'AGENTS.md'):
            continue
        if path.startswith('source-code/frontend/'):
            flags['frontend'] = True
        elif path.startswith('source-code/backend/'):
            flags['backend'] = True
            if path.startswith('source-code/backend/migrations/') or path == 'source-code/backend/alembic.ini':
                flags['migrations'] = True
            if path == 'source-code/backend/app/seed_catalog.py':
                flags['catalog'] = True
        else:
            force = True
            reasons.append('Shared/operational or unclassified change: ' + path)
    if not (Path(root)/'source-code/frontend/dist/server').is_dir():
        flags['frontend'] = True
        reasons.append('Frontend build output missing')
    if force:
        flags = dict.fromkeys(flags, True)
        reasons.append('Full deployment selected')
    services = (['akuru-api','akuru-worker'] if flags['backend'] else []) + (['akuru-web'] if flags['frontend'] else [])
    return dict(schema=1, release_sha=target, baseline_sha=baseline, environment_sha256=env_hash,
        accepted=False, runtimes=runtimes, full=force, **flags, services=services,
        backup=bool(services), changed_files=paths, reasons=reasons)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--target',required=True)
    p.add_argument('--state',type=Path,required=True);p.add_argument('--environment-file',type=Path)
    p.add_argument('--full',action='store_true');a=p.parse_args()
    print(json.dumps(plan(a.root,a.target,a.state,a.environment_file,a.full),indent=2))

if __name__=='__main__':main()
