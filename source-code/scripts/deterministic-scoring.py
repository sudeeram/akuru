#!/usr/bin/env python3
"""Admin API tooling for prepared, source-reviewed deterministic scoring packages.

No provider SDK, API inference call, SQL connection or executable package code.
Source files/credentials and receipts are private (0600); never commit them.
"""
import argparse,copy,hashlib,importlib.util,json,os,sys,uuid,subprocess
from pathlib import Path

spec=importlib.util.spec_from_file_location('intake',Path(__file__).with_name('import-pearson-intake.py'))
intake=importlib.util.module_from_spec(spec);spec.loader.exec_module(intake)

def sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def canonical(rules):
 r=copy.deepcopy(rules)
 if r.get('deterministic'):r['deterministic'].pop('certificateId',None)
 return r

def point_signature(points):
 return [dict(code='',text='',kind='other',dependsOn=None,followThrough=False,acceptedAnswers=[])|p for p in points]

def case_hash(cases):
 return sha([dict(expectedMarks=None,expectedPoints=[],requiresReview=False,holdout=False)|c for c in cases])

def package_hash(package):
 return sha([package.get('markingPoints'),package['rules'],package['cases'],package['sourceNotes'],package.get('provenance',{})])


def batch(args):
 """Resume reviewed package steps; never refresh stale source preconditions."""
 if not args.package:raise ValueError('Batch requires --package pointing to a private manifest array')
 manifest=json.loads(args.package.read_text())
 if not isinstance(manifest,list)or not 1<=len(manifest)<=100:raise ValueError('Use 1–100 reviewed batch entries')
 outcomes=[]
 for entry in manifest:
  if not isinstance(entry,dict)or set(entry)-{'number','partLabel','package','enableTutor'}:raise ValueError('Invalid batch entry')
  number=str(entry['number']);part=entry['partLabel']
  if not isinstance(part,str)or not 1<=len(part)<=40 or len(number)>40 or type(entry.get('enableTutor',False))is not bool:raise ValueError('Invalid batch identity/release flag')
  file=(args.package.parent/entry['package']).resolve()
  package=json.loads(file.read_text())
  if package['paperId']!=args.paper or package['number']!=number or package['partLabel']!=part:raise ValueError('Batch package identity mismatch')
  base=f"admin/official-paper-reviews/{args.paper}"
  client=intake.Client(args.base_url,args.credentials)
  try:
   review=client.call(base);question=next(q for q in review['questions']if q['number']==number)
   target=next(p for p in question['data']['parts']if p['label']==part)
   history=client.call(base+f'/questions/{number}/deterministic-validations')
   complete=next((v for v in history if v['part']==part and v['current']and v['passed']and v['fixtureHash']==case_hash(package['cases'])),None)
   # A current server proof is source/engine bound. A local receipt alone is not.
   certified=bool(complete and target.get('assessmentReadiness')=='automatic' and canonical(target['scoringRules'])==canonical(package['rules']) and ('markingPoints'not in package or point_signature(target['markingPoints'])==point_signature(package['markingPoints'])))
  finally:
   try:client.call('auth/logout',{})
   except ValueError:pass
  prefix=args.output.parent/(file.stem+'-batch')
  receipt=Path(str(prefix)+'-apply.json')
  common=[sys.executable,str(Path(__file__).resolve()),'--base-url',args.base_url,'--credentials',str(args.credentials),'--paper',args.paper,'--number',number,'--part',part,'--package',str(file)]
  if not certified:
   applied=json.loads(receipt.read_text())if receipt.exists()else None
   if applied:
    if applied['packageHash']!=package_hash(package)or applied['appliedContentHash']!=question['analysisContentHash']or applied['rulesHash']!=sha(canonical(target['scoringRules'])):raise ValueError('Batch receipt is stale; inspect and prepare again')
   else:subprocess.run([*common,'apply','--output',str(receipt)],check=True)
   analysis=Path(str(prefix)+'-analysis.json')
   subprocess.run([*common,'record-assessment','--receipt',str(receipt),'--output',str(analysis)],check=True)
   subprocess.run([*common,'validate','--receipt',str(receipt),'--output',str(prefix)+'-validation.json'],check=True)
  if entry.get('enableTutor'):
   if not args.enable_tutor:raise ValueError('Batch Tutor release also requires --enable-tutor')
   subprocess.run([*common,'release','--enable-tutor','--output',str(prefix)+'-release.json'],check=True)
  outcomes.append(dict(number=number,part=part,certified=True,resumed=certified))
  intake.save_private(args.output,outcomes)
 print('Completed reviewed batch entries:',len(outcomes),'; no model calls')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('command',choices=['fetch','preview','apply','record-assessment','validate','history','release','inventory','batch','replay'])
 p.add_argument('--base-url',default='https://akuru.magicalinternational.com');p.add_argument('--credentials',type=Path,required=True)
 p.add_argument('--paper',required=True);p.add_argument('--number');p.add_argument('--part')
 p.add_argument('--package',type=Path);p.add_argument('--receipt',type=Path);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--enable-tutor',action='store_true',help='Explicitly restore the named eligible Tutor part only')
 a=p.parse_args()
 if a.command=='batch':return batch(a)
 root=f'admin/official-paper-reviews/{a.paper}';c=intake.Client(a.base_url,a.credentials)
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
     elif a.command in {'validate','replay'}:
      if a.command=='validate':
       if not a.receipt:p.error('--receipt from the apply step is required')
       receipt=json.loads(a.receipt.read_text())
       if receipt['appliedContentHash']!=q['analysisContentHash']:raise ValueError('Applied content changed; inspect/prepare a new package')
       if receipt['packageHash']!=package_hash(package)or receipt['rulesHash']!=sha(canonical(part['scoringRules'])):raise ValueError('Package or configured rules changed; prepare a new reviewed receipt')
      else:
       if package['expectedContentHash']!=q['analysisContentHash']or package['expectedRevision']!=q['revision']:raise ValueError('Replay source/revision changed; inspect again')
       if canonical(package['rules'])!=canonical(part['scoringRules'])or ('markingPoints'in package and point_signature(package['markingPoints'])!=point_signature(part['markingPoints'])):raise ValueError('Replay package does not match the saved source-reviewed rubric')
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
