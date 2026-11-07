#!/usr/bin/env python3
"""Advance existing pilot prompt pins without broadening audience or other grants.

Run as root with backend .venv Python from the production backend directory:
  sudo .venv/bin/python ../../deploy/ubuntu/update-tutor-chat-release.py
The immutable evidence file is committed with the reviewed release.
"""
import grp
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source-code/backend'))

from dotenv import dotenv_values
from app.config import Settings
from app.ai.prompts import get_tutor_prompt, get_teaching_prompt


def main():
    if os.geteuid() != 0:
        raise SystemExit('Run as root using the backend virtual environment.')
    root = Path(__file__).resolve().parents[2]
    evidence_path = root / 'source-code/backend/evaluations/tutor/chatbot-personalisation-20261107.json'
    raw = evidence_path.read_bytes()
    evidence = json.loads(raw)
    if not evidence['deterministicTestsPassed']:
        raise SystemExit('Release evidence does not record passing tests.')
    env = Path('/etc/akuru/akuru.env')
    settings = Settings(_env_file=env)
    if not settings.tutor_release_gates_required:
        raise SystemExit('Refusing a deployment with disabled tutor release gates.')
    if settings.tutor_text_pilot is None:
        raise SystemExit('No existing pilot. Review non-pilot evaluation releases separately.')
    old = settings.tutor_text_pilot.model_dump(mode='json')
    if old['prompt_version'] not in {'1.1.0', '1.2.0'}:
        raise SystemExit('Unexpected baseline prompt pin; review it before updating.')
    if old.get('supplementary_prompt_version') not in {None, '2.1.0', '2.2.0'}:
        raise SystemExit('Unexpected supplementary prompt pin; review before updating.')
    new = dict(old)
    digest = hashlib.sha256(raw).hexdigest()
    new['prompt_version'] = get_tutor_prompt('explanation').version
    new['evidence_sha256'] = digest
    if old.get('supplementary_prompt_version'):
        new['supplementary_prompt_version'] = get_teaching_prompt('explanation').version
        new['supplementary_evidence_sha256'] = digest
    changed = {'prompt_version', 'evidence_sha256', 'supplementary_prompt_version', 'supplementary_evidence_sha256'}
    assert {k:v for k,v in old.items() if k not in changed} == {k:v for k,v in new.items() if k not in changed}
    key = 'AKURU_TUTOR_TEXT_PILOT'
    lines = [line for line in env.read_text().splitlines()
             if line.split('=',1)[0].strip().removeprefix('export ') != key]
    lines.append(key + '=' + shlex.quote(json.dumps(new, separators=(',',':'))))
    stage = env.with_name('.akuru.env.chat-personality-stage')
    stage.write_text('\n'.join(lines)+'\n'); os.chmod(stage,0o600)
    try:
        validated = Settings(_env_file=stage, tutor_text_pilot=json.loads(dotenv_values(stage)[key]))
        assert validated.tutor_text_pilot.model_dump(mode='json') == new
        backup = env.with_name('akuru.env.before-chat-personality-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
        shutil.copy2(env, backup); os.chmod(backup,0o600)
        os.chown(stage,0,grp.getgrnam('akuru').gr_gid); os.chmod(stage,0o640)
        os.replace(stage,env)
    finally:
        stage.unlink(missing_ok=True)
    target = Path('/data/akuru/release-evidence') / ('chatbot-personalisation-' + digest + '.json')
    target.write_bytes(raw); os.chmod(target,0o640); os.chown(target,0,grp.getgrnam('akuru').gr_gid)
    print('Prompt pins and evidence updated; existing audience, content, model, expiry and release gates preserved.')


if __name__ == '__main__':
    main()
