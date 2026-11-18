"""Content dependencies for independently reviewed subparts.

The aggregate parent prompt/source union is not shared scientific context.
Only the actual shared stem, shared visuals and this part's sources bind it.
Historical analyses without bindings retain conservative question-wide validity.
"""
import copy
import uuid
from types import SimpleNamespace
from sqlalchemy import select
from app.models import OfficialQuestionAnalysis


def part_ref(question, label):
    return str(uuid.uuid5(question.id, 'part:'+label))


def binding(db, workspace, question, label):
    from .official_question_analyses import content_hash, source_manifest
    data=copy.deepcopy(question.review_data)
    part=next((p for p in data['parts']if p['label']==label),None)
    if part is None:return None
    data.update(parts=[part],prompt=data.get('sharedStem',''),marks=part['marks'],paperSources=part.get('paperSources',[]))
    return content_hash(db,SimpleNamespace(review_data=data),source_manifest(db,workspace))


def bindings(db, workspace, question):
    return {p['label']:binding(db,workspace,question,p['label'])for p in question.review_data['parts']}


def current_analysis(db,workspace,question,label):
    from .question_auto_approval import current_accuracy
    current=current_accuracy(db,workspace,question)
    if current:return current
    expected=binding(db,workspace,question,label)
    for row in db.scalars(select(OfficialQuestionAnalysis).where(
        OfficialQuestionAnalysis.question_id==question.id,OfficialQuestionAnalysis.stage=='accuracy'
    ).order_by(OfficialQuestionAnalysis.version_number.desc()).limit(100)):
        if row.analysis_data.get('_scopeBindings',{}).get(label)==expected:return row
    return None
