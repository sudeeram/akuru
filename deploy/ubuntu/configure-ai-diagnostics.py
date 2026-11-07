#!/usr/bin/env python3
"""Explicitly configure private model diagnostics without changing other settings."""
import argparse
from datetime import datetime,timezone
import grp
import os
from pathlib import Path
import pwd
import shlex
import shutil
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'source-code/backend'))
from app.config import Settings

parser=argparse.ArgumentParser(description=__doc__)
group=parser.add_mutually_exclusive_group(required=True)
group.add_argument('--enable-content',action='store_true')
group.add_argument('--metadata-only',action='store_true')
group.add_argument('--disable',action='store_true')
args=parser.parse_args()
if os.geteuid()!=0:raise SystemExit('Run as root with the backend virtual environment.')
env=Path('/etc/akuru/akuru.env')
original=Settings(_env_file=env)
keys={'AKURU_AI_DIAGNOSTICS_ENABLED':'false' if args.disable else 'true',
      'AKURU_AI_DIAGNOSTICS_CAPTURE_CONTENT':'true' if args.enable_content else 'false',
      'AKURU_AI_DIAGNOSTICS_DIRECTORY':'/data/akuru/diagnostics/ai',
      'AKURU_AI_DIAGNOSTICS_RETENTION_DAYS':'7',
      'AKURU_AI_DIAGNOSTICS_MAX_CONTENT_CHARACTERS':'200000',
      'AKURU_AI_DIAGNOSTICS_MAX_FILE_BYTES':'10485760'}
lines=[line for line in env.read_text().splitlines() if line.split('=',1)[0].strip().removeprefix('export ') not in keys]
lines+=['','# Private operational AI diagnostics; contains student text when capture is enabled.']
lines += [key+'='+shlex.quote(value) for key,value in keys.items()]
stage=env.with_name('.akuru.env.ai-diagnostics-stage')
fd=os.open(stage,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
try:
    with os.fdopen(fd,'w') as stream:stream.write('\n'.join(lines)+'\n')
    changed=Settings(_env_file=stage)
    fields={key.removeprefix('AKURU_').lower() for key in keys}
    assert original.model_dump(exclude=fields)==changed.model_dump(exclude=fields)
    path=Path(changed.ai_diagnostics_directory)
    if path.is_symlink():raise SystemExit('Refusing symlink diagnostics directory.')
    path.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.chown(path,pwd.getpwnam('akuru').pw_uid,grp.getgrnam('akuru').gr_gid);os.chmod(path,0o700)
    backup=env.with_name('akuru.env.before-ai-diagnostics-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6])
    shutil.copy2(env,backup);os.chmod(backup,0o600)
    os.chown(stage,0,grp.getgrnam('akuru').gr_gid);os.chmod(stage,0o640)
    os.replace(stage,env)
finally:stage.unlink(missing_ok=True)
print('Diagnostics configured; all other settings, access grants and credentials preserved. Restart API and worker to apply.')
