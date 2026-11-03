#!/usr/bin/env python3
"""Build deterministic, unpublished Pearson proposal batches (no network writes)."""
import argparse,json
from pathlib import Path
from pearson_intake import catalogue,build_bank,VERSION


def main():
 p=argparse.ArgumentParser();p.add_argument('source_root',type=Path);p.add_argument('--subject',choices=['biology','chemistry'],default='biology');p.add_argument('--paper-key',action='append');p.add_argument('--catalogue-only',action='store_true');args=p.parse_args()
 root=args.source_root.resolve();out=root/'.akuru-intake';out.mkdir(exist_ok=True)
 rows=catalogue(root,args.subject);(out/'catalogue.json').write_text(json.dumps(rows,indent=2)+'\n')
 if args.catalogue_only:print(f'{len(rows)} PDFs catalogued');return
 keys=args.paper_key or sorted({r['paperKey'] for r in rows});summary=[]
 for key in keys:
  try:
   bank=build_bank(root,rows,[key]);target=out/(key+'.json');target.write_text(json.dumps(bank,ensure_ascii=False,indent=2)+'\n')
   entry=dict(paperKey=key,status='draft_built',path=target.name,questions=len(bank['questions']),parts=sum(len(q['subparts']) for q in bank['questions']),issues=sum(len(q['issues']) for q in bank['questions']))
  except ValueError as error:entry=dict(paperKey=key,status='blocked',reason=str(error))
  summary.append(entry);print(json.dumps(entry),flush=True)
 (out/'build-summary.json').write_text(json.dumps(dict(extractorVersion=VERSION,papers=summary),indent=2)+'\n')
 if any(r['status']=='blocked' for r in summary):raise SystemExit(1)


if __name__=='__main__':main()
