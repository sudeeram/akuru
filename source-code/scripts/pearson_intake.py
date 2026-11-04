"""Source-bound Pearson linear Biology/Chemistry draft extraction; never approval.

Native PDF lines retain coordinates for boundary detection. Mark allocations do
not end a subpart: subsequent options and response context stay with that label.
Licensed output belongs under the ignored source tree.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

VERSION = 'pearson-native-layout-v1.2'
TOTAL = re.compile(r'Total for Question\s*(\d+)\s*=\s*(\d+)\s*marks', re.I)
LABEL = re.compile(r'^\(([a-z]+)\)\s*(?:\(([ivx]+)\))?\s*', re.I)
FURNITURE = re.compile(r'DO\s+NOT\s+WRITE|Turn over|^\*?P\d{5,}[A-Z]?\d*\*?$|Total for (?:Question|paper)|^Answer ALL questions|^Some questions must|^answer, put a line|^and then mark|^BLANK PAGE', re.I)
ROMAN = {'i','ii','iii','iv','v','vi','vii','viii','ix','x'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def catalogue(root: Path, subject='biology'):
    qualification, letter = {'biology': ('4BI1','B'), 'chemistry': ('4CH1','C')}[subject]
    rows=[]
    for path in sorted(root.rglob('*.pdf')):
        if path.parent==root/'specification':continue  # Versioned reference intake is separate from exam components.
        m=re.search(r'Paper([12]'+letter+r'R?|'+letter+r'R)-(January|June|November)(\d{4})',path.name,re.I)
        if not m:raise ValueError(f'Unrecognised paper filename: {path.name}')
        component=m[1].upper(); ambiguous=len(component)==2 and component.endswith('R')
        if ambiguous:component='2'+component
        kind='question' if 'question'in path.name.lower() else 'markScheme' if 'markscheme'in path.name.lower() else 'examinerReport'
        with pymupdf.open(path) as pdf:
            texts=[p.get_text() for p in pdf]
            cover=' '.join(texts[0].split())
            code_match=re.search(r'\bPaper\s*:?\s*([12]'+letter+r'R?)\b',cover,re.I)
            ref=re.search(qualification+r'\s*/\s*([12]'+letter+r'R?)\b',cover,re.I)
            internal=(ref or code_match).group(1).upper() if ref or code_match else None
            identity_basis='native_cover'
            if not internal:
                footer_codes=set(re.findall(qualification+r'\s*(?:/|\s)\s*([12]'+letter+r'R?)\b','\n'.join(texts),re.I))
                if len(footer_codes)==1:
                    internal=next(iter(footer_codes)).upper();identity_basis='consistent_native_qualification_footer'
            issues=[]
            if internal!=component:issues.append('internal_component_conflict_or_unreadable')
            if qualification not in '\n'.join(texts[:3]):issues.append('qualification_not_verified')
            if ambiguous:issues.append('filename_missing_paper_number')
            provisional='provisional'in cover.lower() or 'provisional'in path.name.lower()
            rows.append(dict(path=str(path.relative_to(root)),kind=kind,component=component,
                year=int(m[3]),session=m[2].title(),subject=subject,qualification=qualification,
                variant='regional' if component.endswith('R') else 'standard',
                paperKey=f'{qualification}-2017-{m[3]}-{m[2].upper()}-{component}',
                sha256=digest(path),pages=len(pdf),internalComponent=internal,identityBasis=identity_basis,
                provisional=provisional,issues=issues,
                lowTextPages=[i+1 for i,t in enumerate(texts) if len(re.sub(r'\s','',t))<80]))
    apply_identity_overrides(rows)
    return rows


def apply_identity_overrides(rows, overrides=None):
    """Only explicitly reviewed, exact-three-file exceptions may resolve a cover conflict."""
    if overrides is None:
        overrides=json.loads(Path(__file__).with_name('pearson-identity-overrides.json').read_text())
    for exception in overrides:
        selected={}
        for role,sha in exception['sourceSha256'].items():
            candidates=[r for r in rows if r['paperKey']==exception['paperKey'] and r['subject']==exception['subject'] and r['kind']==role and r['sha256']==sha]
            if len(candidates)!=1:break
            selected[role]=candidates[0]
        else:
            report=selected[exception['role']]
            if report['internalComponent']!=exception['coverComponent'] or report['component']!=exception['verifiedComponent']:continue
            report['issues']=[i for i in report['issues'] if i!='internal_component_conflict_or_unreadable']
            report['issues'].append('reviewed_cover_misprint')
            report['identityBasis']='reviewed_body_comparison'
            report['identityReview']=exception['review']
            report['verifiedComponent']=exception['verifiedComponent']
            report['reportPagesByQuestion']=exception.get('reportPagesByQuestion',{})
    return rows


def line_records(pdf):
    records=[]
    for number,page in enumerate(pdf,1):
        for block in page.get_text('dict')['blocks']:
            if block.get('type')!=0:continue
            for line in block['lines']:
                text=''.join(s['text'] for s in line['spans']).strip()
                x0,y0,x1,y1=line['bbox']
                if not text or x0<25 or x0>page.rect.width-55 or y0>page.rect.height-55:continue
                if FURNITURE.search(text) or re.fullmatch(r'[.\s\u2026]{4,}',text) or re.fullmatch(r'\d*\s*\.{5,}\s*',text):continue
                # Source fonts sometimes encode checkbox glyphs as private-use characters.
                # Options are kept as text; the original page retains the actual boxes.
                records.append(dict(page=number,x=x0,y=y0,text=text,box=list(line['bbox'])))
    return sorted(records,key=lambda r:(r['page'],round(r['y']/3),r['x']))


def clean_text(records):
    return '\n'.join(r['text'] for r in records if not (r['x']>400 and re.fullmatch(r'\(\d+\)',r['text'])))


def split_parts(records):
    starts=[];major=''; context={}
    for index,r in enumerate(records):
        m=LABEL.match(r['text']) if r['x']<130 else None
        if not m:continue
        first,minor=m.groups();first=first.lower();minor=minor.lower() if minor else None
        if first in ROMAN and major and not minor:label=f'{major}({first})'
        else:
            major=first;label=f'{major}({minor})' if minor else major
        starts.append((index,label,m.end()))
    stem=clean_text(records[:starts[0][0]]) if starts else ''
    parts=[];issues=[]
    for i,(start,label,prefix) in enumerate(starts):
        end=starts[i+1][0] if i+1<len(starts) else len(records)
        region=records[start:end]; marks=[int(r['text'][1:-1]) for r in region if r['x']>400 and re.fullmatch(r'\(\d+\)',r['text'])]
        body=[dict(r) for r in region];body[0]['text']=body[0]['text'][prefix:]
        text=clean_text(body).strip()
        if not marks and i+1<len(starts) and starts[i+1][1].startswith(label+'('):
            context[label]=text;continue
        if len(marks)!=1:issues.append(f'Part {label}: expected one explicit allocation; found {marks}')
        parent=label.split('(')[0]
        if parent in context and '('in label:text=context[parent]+'\n'+text
        parts.append(dict(label=label,marks=sum(marks),extractionCandidate=text,
            sourcePages=sorted({r['page'] for r in region}),reviewStatus='wording_and_layout_pending'))
    if not parts:
        marks=[int(r['text'][1:-1]) for r in records if r['x']>400 and re.fullmatch(r'\(\d+\)',r['text'])]
        parts=[dict(label='',marks=sum(marks),extractionCandidate=clean_text(records),sourcePages=sorted({r['page'] for r in records}))]
        issues.append('No explicit subpart labels: inspect unlabelled whole-question response.')
    if len({p['label'] for p in parts})!=len(parts):issues.append('Duplicate subpart labels; geometry review required.')
    return stem,parts,issues


def scheme_entries(pdf):
    records=line_records(pdf);starts=[];pending=[]
    for i,r in enumerate(records):
        if r['x']>135:continue
        m=re.match(r'^(\d+)\s*((?:\([a-zivx]+\)\s*)+)',r['text'],re.I)
        if m:starts.append((i,int(m[1]),''.join(re.findall(r'\([a-zivx]+\)',m[2],re.I)),m.end()))
        elif re.fullmatch(r'\d{1,2}',r['text']) and r['x']<110 and any('Number' in item['text'] for item in records[max(0,i-6):i]):
            starts.append((i,int(r['text']),'',len(r['text'])))
        else:
            bare=re.match(r'^((?:\([a-zivx]+\)\s*)+)',r['text'],re.I)
            if bare:pending.append((i,''.join(re.findall(r'\([a-zivx]+\)',bare[1],re.I)),bare.end()))
    for index,label,prefix in pending:
        previous=next((x for x in reversed(starts) if x[0]<index),None)
        following=next((x for x in starts if x[0]>index),None)
        # Missing source question numerals may be inherited only where the next
        # explicit row continues the same major subpart. Admin still verifies it.
        major=label.split(')')[0]
        anchor=following if following and following[2].split(')')[0]==major else previous
        if anchor:starts.append((index,anchor[1],label,prefix))
    starts.sort()
    out=defaultdict(list)
    for n,(start,q,label,prefix) in enumerate(starts):
        end=starts[n+1][0] if n+1<len(starts) else len(records)
        region=[dict(r) for r in records[start:end]];region[0]['text']=region[0]['text'][prefix:]
        text='\n'.join(r['text'] for r in region if not re.fullmatch(r'Question|Number|Answer|Mark|Additional guidance',r['text'],re.I)).strip()
        # (a)(ii) -> a(ii), (b) -> b
        key=re.sub(r'^\(([a-z]+)\)',r'\1',label)
        out[(q,key)].append(dict(text=text,pages=sorted({r['page'] for r in region})))
    # Table cells keep answer and additional-guidance columns separate. The
    # line-based pass remains the conservative fallback for broken tables.
    for page_number,page in enumerate(pdf,1):
        for table in page.find_tables().tables:
            for row in table.extract():
                cells=[cell.strip() for cell in row if cell and cell.strip()]
                if not cells:continue
                match=re.fullmatch(r'(\d+)?\s*((?:\([a-zivx]+\)\s*)*)',cells[0],re.I)
                if not match or not (match[1] or match[2]):continue
                label=re.sub(r'^\(([a-z]+)\)',r'\1',match[2].replace(' ',''))
                candidates=[key for key,values in out.items() if key[1]==label and
                    (not match[1] or key[0]==int(match[1])) and any(page_number in v['pages'] for v in values)]
                if len(candidates)!=1 or len(cells)<3:continue
                mark=cells[-1]
                if not re.fullmatch(r'\d+',mark):continue
                for item in out[candidates[0]]:
                    if page_number in item['pages']:
                        item.setdefault('answerCells',[]).append(cells[1])
                        item.setdefault('guidanceCells',[]).extend(cells[2:-1])
    return out


def proposed_points(answer):
    """Transcribe source bullets; never infer executable scoring semantics."""
    answer=answer.replace('\uf0b7','•')
    if not answer.strip():return []
    if 'only correct answer' in answer.lower():
        candidates=[next((line.strip() for line in answer.splitlines() if re.match(r'^\s*[A-D]\s+(?!is not|is incorrect|is not correct)',line,re.I)), '')]
    elif re.search(r'(?m)^\s*[A-D]\s*\(',answer):
        candidates=[next(line.strip() for line in answer.splitlines() if re.match(r'^\s*[A-D]\s*\(',line))]
    else:
        candidates=re.split(r'(?:^|\n)\s*(?:•|\d+\.(?!\d))\s*',answer)
        candidates=[text.strip() for text in candidates if text.strip() and (len(candidates)==1 or not re.match(r'^(?:An? (?:answer|explanation|description)|The (?:only correct answer|following)|[Rr]eference to)',text.strip()))]
    return [dict(code=f'P{i+1}',text=text,kind='other') for i,text in enumerate(candidates) if text and len(text)<=2000][:200]


def report_sections(pdf):
    # A report may omit whitespace after Question and place entire candidate
    # examples on image-only continuation pages. Keep physical page ranges.
    starts=[];stop=len(pdf)+1
    for page_number,page in enumerate(pdf,1):
        for line in page.get_text().splitlines():
            text=line.strip()
            if re.fullmatch(r'Paper Summary',text,re.I):stop=min(stop,page_number)
            match=re.fullmatch(r'Question\s*(\d+)\s*(?:\([a-z]\))?\s*(?:\(?[ivx]+\)?)?',text,re.I)
            if match:starts.append((page_number,int(match[1])))
    out=defaultdict(list)
    for index,(start,question) in enumerate(starts):
        end=starts[index+1][0] if index+1<len(starts) else stop
        pages=list(range(start,end))
        if pages:
            out[question].append(dict(text='\n'.join(pdf[n-1].get_text() for n in pages),pages=pages))
    return out


def build_bank(root: Path, rows: list[dict], keys: list[str]|None=None):
    grouped=defaultdict(list)
    for row in rows:grouped[row['paperKey']].append(row)
    bank=dict(schemaVersion=1,status='local_draft_unreleased',studentAccess=False,course='igcse',
        subject=rows[0]['subject'],papers=[],questions=[],extractorVersion=VERSION,
        provenance=[dict(role=role,method='native_pdf',guidelineId='akuru-igcse-pastpapers',
            guidelineVersion='1.3.0',processedAt=datetime.now(timezone.utc).isoformat(),
            notes='Deterministic native-layout proposal. Not visually or semantically approved; no AI model used.')
            for role in ['paper','scheme','report']])
    for key,items in sorted(grouped.items()):
        if keys is not None and key not in keys:continue
        selected={}
        for kind in ['question','markScheme','examinerReport']:
            choices=[r for r in items if r['kind']==kind and not r['provisional'] and not any(x in r['issues'] for x in ['internal_component_conflict_or_unreadable','qualification_not_verified'])]
            if len(choices)>1:raise ValueError(f'Ambiguous exact source {key} {kind}')
            if choices:selected[kind]=choices[0]
        if not all(k in selected for k in ['question','markScheme']):raise ValueError(f'No verified paper/scheme pair: {key}')
        for row in selected.values():
            if digest(root/row['path'])!=row['sha256']:raise ValueError('Source changed after catalogue')
        paper=selected['question'];expected=110 if paper['component'][0]=='1' else 70
        with pymupdf.open(root/paper['path']) as pdf:
            records=line_records(pdf)
            totals=[]
            for number,page in enumerate(pdf,1):
                for m in TOTAL.finditer(page.get_text()):totals.append((int(m[1]),int(m[2]),number))
            if [q for q,m,p in totals]!=list(range(1,len(totals)+1)) or sum(m for q,m,p in totals)!=expected:raise ValueError(f'Paper totals fail: {key}')
            with pymupdf.open(root/selected['markScheme']['path']) as scheme:entries=scheme_entries(scheme)
            reports={}
            if 'examinerReport'in selected:
                with pymupdf.open(root/selected['examinerReport']['path']) as report:reports=report_sections(report)
            previous_end=1
            for q,marks,endpage in totals:
                start_candidates=[i for i,r in enumerate(records) if previous_end<=r['page']<=endpage and r['x']<85 and re.match(rf'^{q}\s+(?=[A-Za-z(])',r['text'])]
                if len(start_candidates)>1 and all(re.match(rf'^{q}\s+\(',records[i]['text']) for i in start_candidates[1:]):
                    start_candidates=start_candidates[:1]
                if len(start_candidates)>1:
                    left=min(records[i]['x'] for i in start_candidates)
                    start_candidates=[i for i in start_candidates if records[i]['x']<=left+3]
                if len(start_candidates)!=1:raise ValueError(f'{key} Q{q}: unclear start {start_candidates}')
                start=start_candidates[0]
                # The end is the original total's position, including same-page next questions.
                total_rects=pdf[endpage-1].search_for(f'Total for Question {q}')
                end_y=min((rect.y0 for rect in total_rects),default=pdf[endpage-1].rect.height)
                region=[r for r in records[start:] if r['page']<endpage or r['page']==endpage and r['y']<end_y]
                region=[dict(r) for r in region];region[0]['text']=re.sub(rf'^{q}\s+','',region[0]['text'])
                for r in region[1:]:
                    if r['x']<85 and re.match(rf'^{q}\s+\(',r['text']):r['text']=re.sub(rf'^{q}\s+','',r['text'])
                stem,parts,issues=split_parts(region)
                if len(parts)==1 and parts[0]['label']=='' and parts[0]['marks']==0:
                    parts[0]['marks']=marks
                    issues.append('Whole-question mark allocation taken from the explicit question total; no separate allocation is printed.')
                if sum(p['marks'] for p in parts)!=marks:issues.append(f"Subpart allocations total {sum(p['marks'] for p in parts)}, expected {marks}; must reconcile before approval.")
                for part in parts:
                    matches=entries.get((q,part['label']),[])
                    part['schemeExtractionCandidate']='\n\n'.join(m['text'] for m in matches)
                    part['schemePages']=sorted({p for m in matches for p in m['pages']})
                    answer='\n'.join(t for m in matches for t in m.get('answerCells',[]))
                    part['proposedMarkingPoints']=proposed_points(answer)
                    part['schemeGuidance']='\n'.join(t for m in matches for t in m.get('guidanceCells',[]))
                    if not matches:issues.append(f"Part {part['label']}: scheme row not confidently located.")
                report_rows=reports.get(q,[])
                reviewed_pages=selected.get('examinerReport',{}).get('reportPagesByQuestion',{}).get(str(q))
                if reviewed_pages:
                    with pymupdf.open(root/selected['examinerReport']['path']) as report_pdf:
                        report_rows=[dict(pages=reviewed_pages,text='\n'.join(report_pdf[p-1].get_text() for p in reviewed_pages))]
                scheme_pages=sorted({p for part in parts for p in part['schemePages']})
                bank['questions'].append(dict(paperKey=key,component=paper['component'],number=str(q),marks=marks,
                    sharedStemExtractionCandidate=stem,rawQuestionExtraction=clean_text(region),studentPrompt=None,
                    subparts=parts,source=dict(questionPdfPages=sorted({r['page'] for r in region}),schemePdfPages=scheme_pages,
                        reportHeadingCandidatePdfPages=sorted({p for item in report_rows for p in item['pages']})),
                    markScheme=dict(rawExtraction='\n\n'.join(p['schemeExtractionCandidate'] for p in parts),markingPoints=[]),
                    examinerReport=dict(rawExtraction='\n\n'.join(r['text'] for r in report_rows),approvedComments=[],reviewStatus='native_candidates_handwriting_unverified'),
                    topicMappings=[],issues=issues,reviewStatus='not_approved_for_import_or_students'))
                previous_end=endpage
        bank['papers'].append(dict(paperKey=key,component=paper['component'],variant=paper['variant'],year=paper['year'],session=paper['session'],
            identityExceptions={k:r['identityReview'] for k,r in selected.items() if r.get('identityReview')},
            files={k:r['path'] for k,r in selected.items()},sourceSha256={k:r['sha256'] for k,r in selected.items()},questionCount=len(totals),totalMarks=expected))
    validate_bank(bank)
    return bank


def validate_bank(bank):
    if bank.get('status')!='local_draft_unreleased' or bank.get('studentAccess') is not False:
        raise ValueError('Draft-only bank required')
    for paper in bank['papers']:
        questions=[q for q in bank['questions'] if q['paperKey']==paper['paperKey']]
        if len(questions)!=paper['questionCount'] or sum(q['marks'] for q in questions)!=paper['totalMarks']:
            raise ValueError('Question count or total marks mismatch')
        for q in questions:
            parts=q['subparts']
            if not parts or len({p['label'] for p in parts})!=len(parts) or sum(p['marks'] for p in parts)!=q['marks']:
                raise ValueError(f"{paper['paperKey']} Q{q['number']}: subpart inventory requires correction")
