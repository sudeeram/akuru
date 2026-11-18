#!/usr/bin/env python3
"""Reuse installed dependencies only when inputs, runtime and inventory match a receipt."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def digest(value):
    return hashlib.sha256(value).hexdigest()


def capture(command, cwd):
    return subprocess.check_output(['sudo','-u','akuru',*command],cwd=cwd,stderr=subprocess.DEVNULL)


def snapshot(component, source):
    folder=source/component
    if component=='frontend':
        inputs=[folder/'package.json',folder/'package-lock.json']
        runtime=[capture(['node','--version'],folder),capture(['npm','--version'],folder)]
        inventory=capture(['npm','ls','--all','--json'],folder)
    else:
        inputs=[folder/'requirements-production.lock']
        runtime=[capture([str(folder/'.venv/bin/python'),'-c',
            'import sys,platform;print(sys.version);print(platform.platform());print(platform.machine())'],folder)]
        capture([str(folder/'.venv/bin/python'),'-m','pip','check'],folder)
        inventory=capture([str(folder/'.venv/bin/python'),'-m','pip','freeze','--all'],folder)
    values=[(p.name,digest(p.read_bytes())) for p in inputs]
    return dict(schema=1,component=component,inputs=values,
        runtime=digest(b'\0'.join(runtime)+os.uname().machine.encode()),inventory=digest(inventory))


def matches(receipt, current):
    try:return json.loads(receipt.read_text())==json.loads(json.dumps(current))
    except (OSError,ValueError):return False


def record(receipt, current):
    receipt.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=receipt.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(current,f);f.flush();os.fsync(f.fileno())
        os.replace(name,receipt)
    finally:
        if os.path.exists(name):os.unlink(name)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['check','record']);p.add_argument('component',choices=['frontend','backend'])
    p.add_argument('--source',type=Path,required=True);p.add_argument('--state-dir',type=Path,required=True);a=p.parse_args()
    try:
        current=snapshot(a.component,a.source)
        path=a.state_dir/(a.component+'.json')
        if a.action=='record':record(path,current)
        elif not matches(path,current):
            print(a.component+': dependency receipt absent or inputs/runtime/inventory changed');return 1
        print(a.component+': installed dependency inventory verified');return 0
    except (OSError,ValueError,subprocess.CalledProcessError):
        print(a.component+': dependency verification failed; installation required',file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
