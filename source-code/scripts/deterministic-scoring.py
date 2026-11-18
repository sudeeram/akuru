#!/usr/bin/env python3
"""Admin API tooling for prepared, source-reviewed deterministic scoring packages.

No provider SDK, API inference call, SQL connection or executable package code.
Source files/credentials and receipts are private (0600); never commit them.
"""
import argparse,copy,hashlib,importlib.util,json,os,sys,uuid
from pathlib import Path

spec=importlib.util.spec_from_file_location('intake',Path(__file__).with_name('import-pearson-intake.py'))
intake=importlib.util.module_from_spec(spec);spec.loader.exec_module(intake)

def sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def canonical(rules):
 r=copy.deepcopy(rules)
 if r.get('deterministic'):r['deterministic'].pop('certificateId',None)
 return r

def case_hash(cases):
 return sha([dict(expectedMarks=None,expectedPoints=[],requiresReview=False,holdout=False)|c for c in cases])

def package_hash(package):
 return sha([package.get('markingPoints'),package['rules'],package['cases'],package['sourceNotes'],package.get('provenance',{})])

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('command',choices=['fetch','preview','apply','record-assessment','validate','history','release','inventory'])
 p.add_argument('--base-url',default='https://akuru.magicalinternational.com');p.add_argument('--credentials',type=Path,required=True)
 p.add_argument('--paper',required=True);p.add_argument('--number');p.add_argument('--part')
 p.add_argument('--package',type=Path);p.add_argument('--receipt',type=Path);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--enable-tutor',action='store_true',help='Explicitly restore the named eligible Tutor part only')
 a=p.parse_args();root=f'admin/official-paper-reviews/{a.paper}';c=intake.Client(a.base_url,a.credentials)
 try:
  review=c.call(root)
  if a.command=='inventory':
   result=[dict(number=q['number'],part=v['label'],marks=v['marks'],readiness=v['assessmentReadiness'],status=v['status'],engine=(v['scoringRules'].get('deterministic')or{}).get('engine','legacy/model-or-manual'))for q in review['questions']for v in q['data']['parts']]
  else:
   if not a.number:p.error('--number is required')
   q=next(q for q in review['questions']if q['number']==a.number)
   part=next((v for v in q['data']['parts']if v['label']==a.part),None)
   if a.command=='fetch':
    result=dict(schema=1,paperId=a.paper,question=q,capabilities=c.call(root+'/deterministic-capabilities'),sourceContext=c.call(root+f'/questions/{a.number}/accuracy-context'))
   elif a.command=='history':result=c.call(root+f'/questions/{a.number}/deterministic-validations')
   elif a.command=='release':
    if not a.enable_tutor or not part:p.error('Release requires --part and explicit --enable-tutor')
    result=c.call(root+f'/questions/{a.number}/chat-release',dict(partLabel=a.part,revision=q['revision'],confirmSelfContained=True,enabled=True))
   else:
    if not a.package:p.error('--package is required')
    package=json.loads(a.package.read_text())
    if package['paperId']!=a.paper or package['number']!=a.number:raise ValueError('Package identity mismatch')
    if a.command=='record-assessment':
     # The operator must supply source-comparison findings; do not manufacture a confidence score.
     bound=json.loads(a.receipt.read_text())['appliedContentHash'] if a.receipt else package['expectedContentHash']
     if bound!=q['analysisContentHash']:raise ValueError('Source assessment package is stale')
     result=c.call(root+f'/questions/{a.number}/analyses',dict(**package['assessment'],expectedQuestionRevision=q['revision'],expectedAnalysisVersion=q['analysisVersion'],expectedContentHash=q['analysisContentHash']))
    else:
     if not part or package['partLabel']!=a.part:raise ValueError('Package subpart mismatch')
     if a.command in {'preview','apply'}:
      if package['expectedContentHash']!=q['analysisContentHash']or package['expectedRevision']!=q['revision']:raise ValueError('Package source/revision is stale; inspect again')
      result=dict(number=a.number,part=a.part,currentRevision=q['revision'],replacesRules=part['scoringRules']!=package['rules'],fixtureCount=len(package['cases']),noModelCalls=True)
      if a.command=='apply':
       data=copy.deepcopy(q['data']);target=next(v for v in data['parts']if v['label']==a.part)
       if 'markingPoints'in package:target['markingPoints']=package['markingPoints']
       target['scoringRules']=copy.deepcopy(package['rules']);target['scoringRules']['deterministic']['certificateId']=None
       target.update(assessmentReadiness='manual_only',assessmentReadinessReason='Prepared deterministic rules; current server replay required.')
       c.call(root+'/questions',dict(number=a.number,expectedRevision=q['revision'],status=q['status'],data=data))
       current=next(v for v in c.call(root)['questions']if v['number']==a.number)
       result.update(appliedContentHash=current['analysisContentHash'],revision=current['revision'],packageHash=package_hash(package),rulesHash=sha(canonical(next(p for p in current['data']['parts']if p['label']==a.part)['scoringRules'])))
     elif a.command=='validate':
      if not a.receipt:p.error('--receipt from the apply step is required')
      receipt=json.loads(a.receipt.read_text())
      if receipt['appliedContentHash']!=q['analysisContentHash']:raise ValueError('Applied content changed; inspect/prepare a new package')
      if receipt['packageHash']!=package_hash(package)or receipt['rulesHash']!=sha(canonical(part['scoringRules'])):raise ValueError('Package or configured rules changed; prepare a new reviewed receipt')
      caps=c.call(root+'/deterministic-capabilities');hist=c.call(root+f'/questions/{a.number}/deterministic-validations')
      fixturehash=case_hash(package['cases'])
      existing=next((v for v in hist if v['part']==a.part and v['current']and v['passed']and v['fixtureHash']==fixturehash),None)
      if existing:result=existing
      else:
       result=c.call(root+f'/questions/{a.number}/validate-deterministic',dict(requestId=str(uuid.uuid5(uuid.NAMESPACE_URL,sha([a.paper,a.number,a.part,q['revision'],caps['engineHash'],package['cases']]))),partLabel=a.part,expectedRevision=q['revision'],expectedEngineHash=caps['engineHash'],confirmSourceReviewed=True,sourceNotes=package['sourceNotes'],provenance=package.get('provenance',{}),cases=package['cases']))
  intake.save_private(a.output,result)
  print('Saved private receipt:',a.output)
  if isinstance(result,dict):
   print(json.dumps({k:result[k]for k in ('passed','coverageComplete','noModelCalls','revision')if k in result}))
   if result.get('passed')is False:raise SystemExit(2)
 finally:
  try:c.call('auth/logout',{})
  except ValueError:pass

if __name__=='__main__':main()
