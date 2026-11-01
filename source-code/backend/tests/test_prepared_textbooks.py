import copy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import uuid
import zipfile

import pytest
from PIL import Image
from sqlalchemy import select

from app.database import get_db
from app.errors import DomainError
from app.main import app
from app.models import Document, DocumentEvent, RetrievalChunk, TextbookTopicContentVersion, TextbookTopicVisualAsset, User, DocumentVersion, DocumentPage, DocumentJob, TextbookTopicDocument
from app.security import hash_password
from app.services.prepared_textbooks import read_package
from test_auth_integration import auth_client  # noqa: F401


def package_data():
    image = Image.new('RGB', (200, 200), '#ffffff')
    stream = io.BytesIO(); image.save(stream, 'PNG'); page = stream.getvalue()
    stream = io.BytesIO(); image.crop((10, 20, 80, 90)).save(stream, 'PNG'); crop = stream.getvalue()
    digest = lambda value: hashlib.sha256(value).hexdigest()
    return {
        'format': 'akuru-textbook-preparation-v1',
        'identity': {'course': 'igcse', 'subject': 'chemistry', 'topicTitle': 'States of Matter'},
        'provenance': {'method': 'test_visual_assisted', 'modelId': None}, 'guideline': {'version': '1.0.0'},
        'pages': [{'id': 'p8', 'printedPage': '8', 'sourcePath': 'pages/p8.png', 'sha256': digest(page), 'width': 200, 'height': 200}],
        'blocks': [{'id': 'b1', 'page': 8, 'kind': 'paragraph', 'title': 'Diffusion', 'text': 'Particles spread from higher concentration to lower concentration.', 'figureRefs': ['1.1']},
                   {'id': 't1', 'page': 8, 'kind': 'table', 'title': 'Mass measurements', 'columns': ['Container', 'Mass / g'], 'rows': [['Basin', '25.72'], ['Missing', None]]},
                   {'id': 's1', 'page': 8, 'kind': 'procedure', 'title': 'Safety', 'items': ['Wear eye protection.', 'Use teacher supervision.']}],
        'figures': [{'id': '1.1', 'page': 8, 'pageId': 'p8', 'path': 'figures/f1.png', 'sha256': digest(crop), 'bboxPixels': [10,20,80,90], 'caption': 'Particle diffusion', 'altText': 'Particles spreading out.'}],
        'exercises': [{'id': 'Q1', 'page': 8, 'stem': 'Describe diffusion.', 'parts': [{'label': 'a', 'prompt': 'Explain the concentration change.', 'figureRefs': ['1.1']}], 'marks': None}],
        'reviewIssues': [{'id': 'SCI-01', 'page': 8, 'title': 'Clarify concentration', 'reason': 'Check definition', 'action': 'Review wording', 'blocks': ['b1']}],
    }, {'pages/p8.png': page, 'figures/f1.png': crop}


def archive(data=None, files=None):
    if data is None: data, files = package_data()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('topic-package.json', json.dumps(data))
        for name, value in files.items(): z.writestr(name, value)
    return stream.getvalue()


def test_read_valid_source_pixels_and_structures():
    package, files = read_package(archive())
    assert package.blocks[1].rows[1][1] is None
    assert package.exercises[0].parts[0].figureRefs == ['1.1']
    assert len(files) == 2


@pytest.mark.parametrize('change', ['traversal','unexpected','checksum','bounds','wrong_crop','unknown_figure','unknown_issue_block','ragged_table','duplicate_page','unreadable_image'])
def test_rejects_unsafe_or_inconsistent_packages(change):
    data, files = package_data()
    if change == 'traversal': files['../secret'] = b'not allowed'
    if change == 'unexpected': files['script.py'] = b'print(1)'
    if change == 'checksum': data['pages'][0]['sha256'] = '0'*64
    if change == 'bounds': data['figures'][0]['bboxPixels'] = [10,20,500,900]
    if change == 'wrong_crop':
        stream = io.BytesIO(); Image.new('RGB', (70,70), 'red').save(stream,'PNG'); files['figures/f1.png'] = stream.getvalue()
        data['figures'][0]['sha256'] = hashlib.sha256(files['figures/f1.png']).hexdigest()
    if change == 'unknown_figure': data['blocks'][0]['figureRefs'] = ['99.1']
    if change == 'unknown_issue_block': data['reviewIssues'][0]['blocks'] = ['missing']
    if change == 'ragged_table': data['blocks'][1]['rows'] = [['one']]
    if change == 'duplicate_page': data['pages'].append(copy.deepcopy(data['pages'][0]))
    if change == 'unreadable_image':
        files['pages/p8.png'] = b'invalid'; data['pages'][0]['sha256'] = hashlib.sha256(b'invalid').hexdigest()
    with pytest.raises(DomainError): read_package(archive(data, files))


def test_duplicate_archive_members_rejected():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        z.writestr('topic-package.json','{}')
        with pytest.warns(UserWarning): z.writestr('topic-package.json','{}')
    with pytest.raises(DomainError): read_package(stream.getvalue())


@pytest.mark.integration
@pytest.mark.parametrize("use_pilot", [False, True])
def test_admin_import_review_publish_and_retrieval_pipeline(auth_client, use_pilot):
    pilot = Path(__file__).resolve().parents[3] / 'textbooks/igcse/chemistry/Unit1-Topic1/ai-prepared-v1/topic1-import-v1.zip'
    if use_pilot and not pilot.exists():
        pytest.skip('Private licensed pilot is not distributed in Git; synthetic scenario still runs in CI.')
    client, username, password = auth_client
    base='/api/v1/admin/textbooks'
    assert client.post(base+'/missing/topics/missing/prepared-packages/import',content=archive()).status_code == 401
    login=client.post('/api/v1/auth/login',json={'username':username,'password':password}).json()
    headers={'X-CSRF-Token':login['csrfToken']}
    book=client.post(base,headers=headers,json={'courseId':'igcse','subjectId':'chemistry','title':'Prepared package test','edition':'2026','publisher':'Test','groupLabel':'unit'}).json()
    book_ref=book['textbookRef']
    r=client.post(f'{base}/{book_ref}/groups',headers=headers,json={'code':'1','title':'Unit 1','summary':'','sequence':1});assert r.status_code==200,r.text
    group=r.json()['groups'][0]
    r=client.post(f"{base}/{book_ref}/groups/{group['groupRef']}/topics",headers=headers,json={'code':'1','title':'States of Matter','sequence':1,'syllabusRef':'','description':''});assert r.status_code==200,r.text
    topic_ref=r.json()['groups'][0]['topics'][0]['topicRef']
    endpoint=f'{base}/{book_ref}/topics/{topic_ref}/prepared-packages'
    binary={**headers,'Content-Type':'application/octet-stream'}
    assert client.post(endpoint+'/import',content=archive(),headers={'Content-Type':'application/octet-stream'}).status_code==403
    r=client.post(endpoint+'/preview',headers=binary,content=archive());assert r.status_code==200,r.text
    assert r.json()['role']=='supporting'
    session=next(app.dependency_overrides[get_db]())
    assert not session.scalar(select(Document).where(Document.sha256==r.json()['sha256']))
    bad,files=package_data();bad['identity']['subject']='maths'
    assert client.post(endpoint+'/import',headers=binary,content=archive(bad,files)).status_code==422
    content=pilot.read_bytes() if use_pilot else archive()
    r=client.post(endpoint+'/import',headers=binary,content=content);assert r.status_code==201,r.text
    document_id=r.json()['documentId']
    r=client.post(endpoint+'/import',headers=binary,content=content);assert r.status_code==201 and r.json()['alreadyImported']
    assert session.get(Document,uuid.UUID(document_id)).review_state=='pending'
    extraction=client.get(f'/api/v1/documents/{document_id}/extraction');assert extraction.status_code==200,extraction.text
    blocks=[block for page in extraction.json()['pages'] for block in page['blocks']]
    assert len(blocks)==(82 if use_pilot else 5) and all(b['needsReview'] for b in blocks)
    assert any('eye protection' in b['text'].lower() for b in blocks)
    assert any('25.72' in b['text'] for b in blocks)
    if use_pilot: assert any('Word bank: boils, solution' in b['text'] for b in blocks)
    # A separate visual-reference file has a different physical page index but
    # the same printed label. Flashcards must link to it by printed label.
    source_package, source_files = read_package(content)
    ref_label='7' if use_pilot else '8'
    ref_source=next(page for page in source_package.pages if page.printedPage==ref_label)
    ref_png=source_files[ref_source.sourcePath]
    ref_response=client.post(f'{base}/{book_ref}/topics/{topic_ref}/documents',params={'role':'visual_reference'},
        headers={**headers,'Content-Type':'image/png','X-Filename':'visual-reference.png','Idempotency-Key':uuid.uuid4().hex},content=ref_png)
    assert ref_response.status_code==201,ref_response.text
    ref_data=ref_response.json();ref_id=uuid.UUID(ref_data['document']['id']);ref_version=uuid.UUID(ref_data['document']['versionId'])
    from app.services.document_processing import _store_asset
    from app.storage import get_storage
    storage=app.dependency_overrides[get_storage]()
    version=session.get(DocumentVersion,ref_version)
    asset=_store_asset(session,storage,version,'test_reference',1,1,'page_render','image/png',ref_png,None)
    ref_page=DocumentPage(document_version_id=ref_version,page_number=1,printed_page_label=ref_label,
        width_points=ref_source.width,height_points=ref_source.height,render_asset_id=asset.id,native_text='',
        extraction_method='test_reference',confidence=0,needs_review=False,page_metadata={'printedPageLabelConfirmed':True})
    session.add(ref_page)
    session.get(Document,ref_id).review_state='reviewed';version.status='completed'
    session.scalar(select(DocumentJob).where(DocumentJob.document_version_id==ref_version)).status='completed'
    session.scalar(select(TextbookTopicDocument).where(TextbookTopicDocument.document_version_id==ref_version)).review_status='ready'
    session.commit()
    url=endpoint+f'/{document_id}/review'
    state=client.get(url).json()
    decisions={issue['id']: 'Integration-test annotation only; this is not approval of the real textbook.' for issue in state['issues']}
    assert client.post(url,headers=headers,json={'contentHash':state['contentHash'],'confirmWholeDocument':True,'decisions':{}}).status_code==422
    assert client.post(url,headers=headers,json={'contentHash':'0'*64,'confirmWholeDocument':True,'decisions':{'SCI-01':'Confirmed.'}}).status_code==409
    r=client.post(url,headers=headers,json={'contentHash':state['contentHash'],'confirmWholeDocument':True,'decisions':decisions});assert r.status_code==200,r.text
    assert r.json()['confirmed']
    visual=session.scalar(select(TextbookTopicVisualAsset).where(TextbookTopicVisualAsset.document_version_id==uuid.UUID(extraction.json()['versionId'])))
    assert visual.status=='selected'
    assets=client.get(f'{base}/{book_ref}/topics/{topic_ref}/sources/{document_id}/visual-assets').json()
    for asset in assets:
        r=client.patch(f"{base}/{book_ref}/topics/{topic_ref}/sources/{document_id}/visual-assets/{asset['assetRef']}",headers=headers,json={'status':'approved','caption':asset['caption'],'altText':asset['altText']});assert r.status_code==200,r.text
    r=client.patch(f'{base}/{book_ref}/topics/{topic_ref}/sources/{document_id}',headers=headers,json={'role':'primary'});assert r.status_code==200,r.text
    r=client.post(f'{base}/{book_ref}/publish',headers=headers,json={'confirmCourse':True,'confirmSubject':True,'confirmEdition':True,'confirmStructure':True});assert r.status_code==200,r.text
    r=client.post(f'{base}/{book_ref}/topics/{topic_ref}/publish',headers=headers,json={'confirmSources':True,'confirmExtraction':True,'confirmTopic':True});assert r.status_code==200,r.text
    chunks=session.scalars(select(RetrievalChunk).where(RetrievalChunk.document_id==uuid.UUID(document_id),RetrievalChunk.status=='active')).all()
    assert chunks and all(chunk.topic_content_version_id for chunk in chunks)
    assert any('higher concentration' in chunk.content for chunk in chunks)
    assert any('Reviewed teaching clarification' in chunk.content for chunk in chunks)
    assert any('25.72' in chunk.content for chunk in chunks)
    content_version=session.get(TextbookTopicContentVersion,chunks[0].topic_content_version_id)
    assert len(content_version.extraction_manifest['visualAssets'])==(19 if use_pilot else 1)
    # Flashcard source rendering resolves the actual approved crop, never an unrelated diagram.
    from app.services import flashcards
    if use_pilot:
        equation=next(chunk for chunk in chunks if 'NH₃(g)' in chunk.content)
        source=flashcards._source(session, equation, SimpleNamespace(visual_asset_id=None, card_metadata={}), 'test-session', 0)
        assert source['printedPage']=='7' and '1.14' in source['visual']['caption']
        assert source['visual']['contentUrl'].startswith('/api/v1/flashcards/student/sessions/')
    else:
        source=flashcards._source(session, next(chunk for chunk in chunks if 'higher concentration' in chunk.content), SimpleNamespace(visual_asset_id=None, card_metadata={}), 'test-session', 0)
        assert source['printedPage']=='8' and '1.1' in source['visual']['caption']
    assert source['textbookPageUrl'].endswith(str(ref_page.id))
    r=client.post(f'{base}/{book_ref}/topics/{topic_ref}/retrieval-preflight',headers=headers,json={'queries':['diffusion particles concentration','solubility mass water temperature']})
    assert r.status_code==200 and r.json()['passed'],r.text
    if use_pilot:
        from app.services import retrieval
        from app.config import get_settings
        probes=[('ammonia hydrochloric acid white ring diffusion', 'ammonia'),
                ('solubility potassium nitrate evaporating basin crystals mass', '25.72'),
                ('calculate solubility mass crystals water 100g solvent', '61.4'),
                ('solute solvent saturated solution temperature', 'saturat'),
                ('evaporation boiling temperature surface particles', 'evaporation'),
                ('potassium chloride solubility temperature', 'chloride')]
        for query, expected in probes:
            evidence=retrieval._topic_evidence(session,get_settings(),uuid.uuid4(),'chemistry',query,5,{chunks[0].topic_id})
            assert evidence and any(expected in row.content.lower() for row in evidence),(query,[row.content for row in evidence])
            assert all(row.printedPage and row.topicRef==topic_ref for row in evidence)
    assert client.post(url,headers=headers,json={'contentHash':client.get(url).json()['contentHash'],'confirmWholeDocument':True,'decisions':{'SCI-01':'Cannot overwrite published evidence.'}}).status_code==409
    assert session.scalar(select(DocumentEvent).where(DocumentEvent.document_id==uuid.UUID(document_id),DocumentEvent.event_type=='prepared_package_reviewed'))


@pytest.mark.integration
@pytest.mark.parametrize('role', ['parent','student'])
def test_prepared_routes_reject_non_admin(auth_client, role):
    client, _, _ = auth_client
    session=next(app.dependency_overrides[get_db]())
    username=f'prepared-{role}-{uuid.uuid4().hex}'
    session.add(User(username=username,display_name='Role test',role=role,password_hash=hash_password('role test password'),must_change_password=False))
    session.commit()
    login=client.post('/api/v1/auth/login',json={'username':username,'password':'role test password'}).json()
    headers={'X-CSRF-Token':login['csrfToken'],'Content-Type':'application/octet-stream'}
    path='/api/v1/admin/textbooks/book_test/topics/topic_test/prepared-packages'
    for action in ['preview','import']:
        assert client.post(path+'/'+action,headers=headers,content=archive()).status_code==403
    assert client.get(path+'/11111111-1111-1111-1111-111111111111/review').status_code==403
