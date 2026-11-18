"""Restricted final-answer recognition and source-authorised arithmetic steps.

A match is not a statistical model confidence. Unknown grammar abstains. The
caller must verify a current certificate before using results for Students.
"""
import ast
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_UP, ROUND_DOWN
from fractions import Fraction
import hashlib
import json
import re
import unicodedata
from app.errors import DomainError
from app.schemas.assessments import MarkingDecision
from app.schemas.marking_rules import MarkingRules
from app.services import marking_rules

ENGINE='deterministic-v1'
# Bump the version and source hash whenever recognition/allocation policy changes.
def _compute_engine_hash():
    from pathlib import Path
    from app.schemas import deterministic_scoring as schema
    return hashlib.sha256(Path(__file__).read_bytes()+Path(marking_rules.__file__).read_bytes()+Path(schema.__file__).read_bytes()+Path(__file__).with_name("deterministic_validation.py").read_bytes()+Path(__file__).with_name("assessment_marking.py").read_bytes()).hexdigest()

def unique_object(items):
    result={}
    for key,value in items:
        if key in result:fail('Duplicate/conflicting answer fields need review.')
        result[key]=value
    return result


def plain(value):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',value).casefold()).strip().rstrip('.').strip()

def fail(reason):raise DomainError('deterministic_requires_review',reason,409)

def number(text):
    """Return value, lexical significant figures, decimal places, unit and evidence."""
    if len(text)>300:fail('Final answer is too long.')
    text=text.strip();raw=text
    # Preserve superscript exponent semantics before Unicode NFKC joins the digits.
    text=re.sub(r'10([⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+)',lambda m:'10^'+m[1].translate(str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺','0123456789-+')),text)
    text=unicodedata.normalize('NFKC',text).replace('−','-')
    text=re.sub(r'\s*[×x*]\s*10\s*\^\s*([+-]?\d+)','e'+r'\1',text)
    m=re.fullmatch(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+))(?:[eE]([+-]?\d{1,3}))?\s*([^\d\n]{0,60})',text)
    if not m:fail('Use one unambiguous decimal/scientific final answer; unsupported wording needs review.')
    mantissa,exponent,unit=m.groups();exponent=int(exponent or '0')
    if abs(exponent)>30 or len(mantissa)>60:fail('Numeric magnitude/precision exceeds the supported limit.')
    try:value=Decimal(mantissa).scaleb(exponent)
    except InvalidOperation:fail('Invalid decimal answer.')
    if not value.is_finite() or abs(value.adjusted())>60:fail('Unsupported numeric magnitude.')
    digits=mantissa.lstrip('+-').replace('.','').lstrip('0')
    sf=len(digits) if digits else max(1,len(mantissa.split('.')[-1]) if '.'in mantissa else 1)
    if sf>15:fail('More than fifteen significant figures requires review.')
    return value,sf,max(0,-value.as_tuple().exponent),plain(unit),raw

def reference(value):
    if not re.fullmatch(r'[+-]?\d+(?:\.\d+)?(?:/[1-9]\d*)?',value):fail('Invalid source numeric rule.')
    if len(value)>80:fail('Numeric rule too long.')
    with localcontext() as ctx:
        ctx.prec=100
        if '/' in value:
            a,b=value.split('/');return Decimal(a)/Decimal(b)
        return Decimal(value)

def numeric_match(condition,parsed):
    value,sf,dp,_,_=parsed;target=reference(condition.value)
    if condition.allowPowerOfTenScaling:
        if value == 0 or target == 0:return value == target
        a,b=value.normalize().as_tuple(),target.normalize().as_tuple()
        return a.sign==b.sign and a.digits==b.digits
    if condition.roundedFrom:
        if not condition.minimumSignificantFigures<=sf<=15:return False
        quantum=Decimal(1).scaleb(value.adjusted()-sf+1)
        with localcontext() as ctx:
            ctx.prec=100
            return value in (target.quantize(quantum,rounding=ROUND_HALF_UP),target.quantize(quantum,rounding=ROUND_DOWN))
    return value==target and (condition.significantFigures is None or sf==condition.significantFigures) and (condition.decimalPlaces is None or dp==condition.decimalPlaces)

def expression(text):
    """Evaluate a tiny arithmetic AST with exact decimal constants; never eval."""
    if len(text)>200:fail('Working expression too long.')
    text=unicodedata.normalize('NFKC',text).replace('×','*').replace('÷','/').replace('−','-')
    try:tree=ast.parse(text,mode='eval')
    except (SyntaxError,ValueError,RecursionError):fail('Working must be a supported arithmetic expression.')
    if len(list(ast.walk(tree)))>40:fail('Working expression too complex.')
    operations=[]
    def visit(n,depth=0):
        if depth>10:fail('Working expression too deep.')
        if isinstance(n,ast.Constant) and type(n.value)in(int,float):
            raw=ast.get_source_segment(text,n)
            if len(raw)>40 or not re.fullmatch(r'\d+(?:\.\d+)?',raw):fail('Unsupported working constant.')
            return Fraction(Decimal(raw))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            v=visit(n.operand,depth+1);return -v if isinstance(n.op,ast.USub)else v
        if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
            a,b=visit(n.left,depth+1),visit(n.right,depth+1)
            if isinstance(n.op,ast.Div)and b==0:fail('Division by zero in working.')
            operations.append(('divide'if isinstance(n.op,ast.Div)else'multiply'if isinstance(n.op,ast.Mult)else'other',a,b))
            v=a/b if isinstance(n.op,ast.Div)else a*b if isinstance(n.op,ast.Mult)else a+b if isinstance(n.op,ast.Add)else a-b
            if v.numerator.bit_length()>256 or v.denominator.bit_length()>256:fail('Working magnitude exceeds limit.')
            return v
        fail('Only bounded arithmetic is supported in working.')
    visit(tree.body);return operations

def validate(points,maximum,rules):
    parsed=marking_rules.validate_rules(points,maximum,rules);config=parsed.deterministic
    if not config:fail('No deterministic answer rules configured.')
    ids=[m.pointId for m in config.matchers];known={p.get('pointId',p.get('code'))for p in points}
    if len(set(ids))!=len(ids) or set(ids)!=known:fail('Configure exactly one matcher for every marking criterion.')
    for matcher in config.matchers:
        for value in matcher.values:reference(value.value)
        for value in matcher.incorrectValues:reference(value)
        for method in matcher.methods:
            reference(method.right)
            if not method.allowAnyLeft and not method.leftValues:fail('Specify source-authorised left operands.')
            for left in method.leftValues:reference(left)
        if matcher.kind=='set':
            groups=[{plain(x) for x in group}for group in matcher.requiredMembers]
            if any(a&b for i,a in enumerate(groups)for b in groups[i+1:]) or set().union(*groups)&{plain(x)for x in matcher.extraMembers}:fail('Set aliases must identify distinct required/extra members.')
        if matcher.kind=='choice' and {plain(x)for x in matcher.accepted}&{plain(x)for x in matcher.rejected}:fail('Accepted and rejected choices overlap.')
    return parsed

def recognize(answer,points,maximum,rules):
    parsed=validate(points,maximum,rules)
    if len(answer)>12000:fail('Answer exceeds deterministic input limit.')
    keys={m.answerKey for m in parsed.deterministic.matchers}
    if keys!={''}:
        try:fields=json.loads(answer,object_pairs_hook=unique_object)
        except (ValueError,RecursionError):fail('This question needs explicitly labelled JSON answer fields.')
        if not isinstance(fields,dict)or set(fields)!=keys:fail('Provide exactly the required labelled answer fields.')
    else:
        if answer.lstrip().startswith('{'):
            try:single=json.loads(answer,object_pairs_hook=unique_object)
            except (ValueError,RecursionError):fail('Invalid structured final answer.')
            fields={'':single}
        else:fields={'':answer}
    matches={};evidence={};near_precision=set()
    # The same field is parsed once. Whole-text matching does not search for positive keywords.
    for key in keys:
        raw=fields[key];work=[]
        if isinstance(raw,dict):
            if set(raw)-{'final','working'} or not isinstance(raw.get('final'),str):fail('Provide final and optional arithmetic working fields.')
            work=raw.get('working',[])
            if not isinstance(work,list)or len(work)>10 or any(not isinstance(x,str)for x in work):fail('Invalid working list.')
            raw=raw['final']
        if not isinstance(raw,str)or not raw.strip():fail('Missing or ambiguous final answer.')
        ms=[m for m in parsed.deterministic.matchers if m.answerKey==key]
        if len({m.kind for m in ms})!=1:fail('A response field cannot mix numeric and choice grammars.')
        if ms[0].kind=='set':
            tokens=[plain(x) for x in re.split(r'\s*(?:,|;|\band\b|&|\+)\s*|\s+',plain(raw)) if x.strip()]
            for m in ms:
                groups=[{plain(x)for x in group}for group in m.requiredMembers]
                known=set().union(*groups)|{plain(x)for x in m.extraMembers}
                if not tokens or not set(tokens)<=known:fail('Unsupported element/member wording needs review.')
                matches[m.pointId]=all(set(tokens)&group for group in groups)and not set(tokens)&{plain(x)for x in m.extraMembers}
                evidence[m.pointId]=raw
        elif ms[0].kind=='choice':
            value=plain(raw);allowed={plain(x)for m in ms for x in m.accepted+m.rejected}
            if value not in allowed:fail('Unknown or conflicting choice; inspect rather than infer a synonym.')
            for m in ms:matches[m.pointId]=value in {plain(x)for x in m.accepted};evidence[m.pointId]=raw
        else:
            n=number(raw);ops=[(op,line) for line in work if line.strip() for op in expression(line)]
            for m in ms:
                if n[3] and n[3] not in {plain(u)for u in m.units}:fail('Unit is not approved for this answer.')
                if not n[3] and not m.allowMissingUnit:fail('An explicit approved unit is required.')
                hit=any(numeric_match(v,n)for v in m.values)
                if any(not v.roundedFrom and n[0]==reference(v.value)for v in m.values)and not hit:near_precision.add(key)
                supporting=raw
                for method in m.methods:
                    for (op,a,b),line in ops:
                        if op==method.operator and b==Fraction(reference(method.right))and (method.allowAnyLeft or a in {Fraction(reference(v))for v in method.leftValues}):
                            hit=True;supporting=line
                matches[m.pointId]=hit;evidence[m.pointId]=supporting
            if not any(matches[m.pointId]for m in ms):
                if key in near_precision:fail('Equivalent magnitude with unsupported precision needs review.')
                if any(m.methods for m in ms) and not any(n[0]==reference(v)for m in ms for v in m.incorrectValues):fail('No supported credit path established; inspect for other valid method credit.')
    rows=[MarkingDecision(pointId=p['pointId'],criterion=p['criterion'],maxMarks=1,awarded=matches[p['pointId']],marksAwarded=int(matches[p['pointId']]),studentEvidence=evidence[p['pointId']],rationale='Source-bound deterministic criterion match; not a model confidence estimate.',confidence=1)for p in points]
    # JSON encodes exponent/unicode escapes, so exact source evidence is validated against decoded fields above.
    total,out,audit=marking_rules.score(rows,points,maximum,rules)
    audit.update(engine=ENGINE,engineHash=engine_hash(),noModelCalls=True)
    return total,out,audit


def answer_format(rubric):
    config=(rubric.get('scoringRules') or {}).get('deterministic')
    if not config:return None
    return dict(engine=ENGINE,fields=list(dict.fromkeys(m.get('answerKey','') for m in config['matchers'])),
        allowWorking=any(m.get('methods') for m in config['matchers']))


_ENGINE_FINGERPRINT = _compute_engine_hash()

def engine_hash():
    # Pin to the running process. A checkout during deployment cannot change its advertised engine.
    return _ENGINE_FINGERPRINT
