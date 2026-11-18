#!/usr/bin/env python3
"""Authenticated no-inference review authoring. Credentials/exports stay private.

Prepared writes require explicit source-bound input; this tool never invents
findings, refreshes stale hashes, invokes a provider or connects to PostgreSQL.
"""
import argparse,importlib.util,json,sys,uuid
from pathlib import Path
spec=importlib.util.spec_from_file_location('intake',Path(__file__).with_name('import-pearson-intake.py'))
intake=importlib.util.module_from_spec(spec);spec.loader.exec_module(intake)

READS={'export':'review-package','readiness':'readiness','history':'review-history','releases':'chat-releases'}
WRITES={'stage':'change-sets','batch':'review-batches','validate-release':'release-validation','evidence-propose':'evidence-links'}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('command',choices=[*READS,*WRITES,'preview','apply','status','batch-status','resume','approve','source-context','topic-evidence','evidence-review'])
 p.add_argument('--base-url',default='https://akuru.magicalinternational.com')
 p.add_argument('--credentials',type=Path,required=True);p.add_argument('--paper',type=uuid.UUID,required=True)
 p.add_argument('--number');p.add_argument('--operation',type=uuid.UUID);p.add_argument('--topic')
 p.add_argument('--input',type=Path);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();root=f'admin/official-paper-reviews/{a.paper}'
 if a.command in WRITES or a.command in {'apply','resume','approve','evidence-review'}:
  if not a.input:p.error('Prepared writes require --input; no implicit edits are performed')
  payload=json.loads(a.input.read_text())
 else:payload=None
 if a.command in {'preview','apply','status','batch-status','resume','evidence-review'}and not a.operation:p.error('--operation is required')
 if a.command in {'approve','source-context'}and not a.number:p.error('--number is required')
 if a.command=='topic-evidence'and not a.topic:p.error('--topic is required')
 client=intake.Client(a.base_url,a.credentials)
 try:
  if a.command in READS:
   route=root+'/'+READS[a.command]
   if a.command=='export'and a.number:
    from urllib.parse import urlencode
    route+='?'+urlencode({'number':a.number})
   result=client.call(route)
  elif a.command in WRITES:result=client.call(root+'/'+WRITES[a.command],payload)
  elif a.command in {'preview','status'}:result=client.call(root+f'/change-sets/{a.operation}'+('/preview'if a.command=='preview'else''))
  elif a.command=='apply':result=client.call(root+f'/change-sets/{a.operation}/apply',payload)
  elif a.command=='batch-status':result=client.call(root+f'/review-batches/{a.operation}')
  elif a.command=='resume':result=client.call(root+f'/review-batches/{a.operation}/resume',payload)
  elif a.command=='approve':result=client.call(root+f'/questions/{a.number}/auto-approval',payload)
  elif a.command=='source-context':result=client.call(root+f'/questions/{a.number}/accuracy-context')
  elif a.command=='topic-evidence':result=client.call(root+f'/topics/{a.topic}/evidence')
  elif a.command=='evidence-review':result=client.call(root+f'/evidence-links/{a.operation}/review',payload)
  intake.save_private(a.output,result)
  print('Saved private review receipt:',a.output)
  if isinstance(result,dict):print(json.dumps({k:result[k]for k in ['id','state','noInference','modelInvocations','completed','total']if k in result},default=str))
 finally:
  try:client.call('auth/logout',{})
  except (ValueError,RuntimeError):pass

if __name__=='__main__':main()
