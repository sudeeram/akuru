#!/usr/bin/env python3
"""Read private diagnostics locally. Payloads require an explicit --content flag."""
import argparse
from collections import deque
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--directory',default='/data/akuru/diagnostics/ai')
parser.add_argument('--trace')
parser.add_argument('--last',type=int,default=30)
parser.add_argument('--content',action='store_true',help='Include protected prompt/reply content; do not paste into public issues.')
args=parser.parse_args()
if not 1<=args.last<=1000:parser.error('--last must be between 1 and 1000')
root=Path(args.directory)
if root.is_symlink():parser.error('Refusing a symlink directory')
rows=deque(maxlen=args.last)
for path in sorted(root.glob('model-calls.jsonl*'),key=lambda p:p.stat().st_mtime):
    if path.is_symlink():parser.error('Refusing a symlink file')
    with path.open() as stream:
        for line in stream:
            try:row=json.loads(line)
            except ValueError:continue
            if args.trace and row.get('traceId')!=args.trace:continue
            if not args.content:row.pop('content',None)
            rows.append(row)
for row in rows:print(json.dumps(row,ensure_ascii=False))
