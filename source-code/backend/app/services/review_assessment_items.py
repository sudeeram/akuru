"""Project reviewed mixed-engine questions into independently markable items.

Source inventory keeps its parent question. Only the official assessment draft is
split, so no deterministic proof is dropped or reused for semantic marking.
"""
import re
from app.errors import DomainError
from . import marking_rules


def items(number, data):
    deterministic=[bool(part.scoringRules.deterministic) for part in data.parts]
    if not any(deterministic) or all(deterministic):
        return [(number,None,data)]
    result=[]
    for part in data.parts:
        suffix=re.sub(r'^([^()]+)',r'(\1)',part.label)
        identifier=number+suffix
        if not part.label or len(identifier)>40:
            raise DomainError('assessment_item_number_invalid','Use a non-empty short label for each mixed-engine assessment subpart.',409)
        scoped=data.model_copy(deep=True)
        scoped.parts=[part.model_copy(deep=True)];scoped.marks=part.marks
        scoped.prompt=part.prompt
        scoped.paperSources=list(part.paperSources)
        scoped.candidateVisualAssetIds=[]  # Never mask unresolved candidates.
        if data.candidateVisualAssetIds:
            raise DomainError('assessment_visual_review_required','Review all source candidates before preparing mixed assessment items.',409)
        result.append((identifier,number,scoped))
    if len({number for number,_,_ in result})!=len(result):
        raise DomainError('assessment_item_number_invalid','Mixed assessment item numbers must be distinct.',409)
    return result


def validate(data):
    for _,_,scoped in items('question',data):
        marking_rules.compile_review(scoped)
