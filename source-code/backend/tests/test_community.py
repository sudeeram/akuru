"""Community HTTP privacy and lifecycle coverage on an isolated database."""
import uuid
import os
from datetime import timedelta
from types import SimpleNamespace
import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.api.v1.community import router
from app.database import get_db
from app.models import (User, StudentProfile, StudentProgression, StudentSubject, Course, Subject,
    CommunityProfile, CommunityFollow, CommunityNotification, CommunityBlock, CommunityReport, AuditEvent)
from app.security import Principal, digest, get_principal
from app.services.community import now

MODELS=(User,StudentProfile,Course,Subject,StudentProgression,StudentSubject,CommunityProfile,CommunityFollow,CommunityNotification,CommunityBlock,CommunityReport,AuditEvent)
BASE='/api/v1/community'


def headers(actor='one',csrf=True):
    return {'X-Test-Actor':actor,**({'X-CSRF-Token':'test-csrf'} if csrf else {})}


@pytest.fixture
def community():
    postgres = os.environ.get('AKURU_COMMUNITY_TEST_POSTGRES') == '1'
    schema = 'community_test_' + uuid.uuid4().hex
    maintenance = None
    if postgres:
        from app.config import get_settings
        maintenance = create_engine(get_settings().database_url)
        with maintenance.begin() as connection:
            connection.execute(text('CREATE SCHEMA ' + schema))
        engine = create_engine(get_settings().database_url, connect_args={'options':'-csearch_path='+schema})
    else:
        engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    for model in MODELS: model.__table__.create(engine)
    with Session(engine,expire_on_commit=False) as db:
        users={name:User(username='private-'+name,display_name='Private identity '+name,role=role,password_hash='unused',must_change_password=False) for name,role in [('admin','admin'),('parent','parent'),('one','student'),('two','student'),('three','student'),('hidden','student'),('inactive','student'),('unconfigured','student')]}
        db.add_all(users.values());db.flush()
        db.add_all([Course(id='igcse',name='iGCSE'),Course(id='other',name='Other course'),Subject(id='science',name='Science'),Subject(id='maths',name='Mathematics')]);db.flush()
        for name in ['one','two','three','hidden','inactive','unconfigured']:
            db.add(StudentProfile(student_id=users[name].id,parent_id=users['parent'].id));db.flush()
            if name!='unconfigured':
                db.add(StudentProgression(student_id=users[name].id,course_id='other' if name=='three' else 'igcse',grade=10,term=1,is_current=True))
                db.add(StudentSubject(student_id=users[name].id,subject_id='science' if name=='one' else 'maths'))
                db.add(CommunityProfile(student_id=users[name].id,public_name='Nova'+name,name_key=('Nova'+name).casefold(),enabled=name!='hidden',visible_subject_ids=['science' if name=='one' else 'maths']))
        users['inactive'].is_active=False
        db.commit()
        app=FastAPI();app.include_router(router,prefix='/api/v1')
        def principal(request:Request):
            actor=request.headers.get('X-Test-Actor')
            if actor not in users or not users[actor].is_active:raise HTTPException(401)
            return Principal(users[actor],SimpleNamespace(csrf_hash=digest('test-csrf')))
        app.dependency_overrides[get_principal]=principal
        app.dependency_overrides[get_db]=lambda:db
        with TestClient(app) as client:yield client,db,users
    engine.dispose()
    if maintenance:
        with maintenance.begin() as connection:
            connection.execute(text('DROP SCHEMA ' + schema + ' CASCADE'))
        maintenance.dispose()


def ref(db,users,name):return db.get(CommunityProfile,users[name].id).public_ref


def members(client,actor='one',**params):
    return client.get(BASE+'/members',params={'course':'igcse',**params},headers=headers(actor))


def follow(client,db,users,actor='one',target='two'):
    return client.post(BASE+f'/members/{ref(db,users,target)}/follow',headers=headers(actor))


def test_course_discovery_subject_filters_and_minimal_identity(community):
    client,db,users=community
    result=members(client)
    assert result.status_code==200
    assert result.headers['cache-control']=='no-store'
    assert [m['publicName'] for m in result.json()['members']]==['Novatwo']
    learner=result.json()['members'][0]
    assert set(learner)=={'ref','publicName','avatar','subjects','following','followsYou'}
    assert 'Private identity' not in result.text and 'private-' not in result.text
    assert str(users['two'].id) not in result.text
    assert members(client,subject='science').json()['members']==[]
    assert len(members(client,subject='maths').json()['members'])==1
    assert members(client,q='NOVA').json()['members']
    assert not members(client,q='%').json()['members']
    assert members(client,course='other').status_code==403
    hidden=db.get(CommunityProfile,users['two'].id);hidden.visible_subject_ids=[];db.commit()
    assert members(client,subject='maths').json()['members']==[]
    assert members(client).json()['members'][0]['subjects']==[]


def test_follow_back_state_persistence_and_cooldown(community):
    client,db,users=community
    assert follow(client,db,users).status_code==200
    assert follow(client,db,users).status_code==200
    assert db.scalar(select(func.count()).select_from(CommunityFollow))==1
    feed=client.get(BASE+'/feed',headers=headers('two')).json()
    assert feed['unreadCount']==1 and len(feed['notifications'])==1
    notification=feed['notifications'][0]
    assert notification['actor']['followsYou'] and not notification['actor']['following']
    assert follow(client,db,users,actor='two',target='one').json()['followsYou']
    assert members(client,kind='following').json()['members'][0]['followsYou']
    assert client.patch(BASE+'/notifications/'+notification['ref'],json={'read':True},headers=headers('two')).status_code==200
    assert client.get(BASE+'/feed',headers=headers('two')).json()['unreadCount']==0
    assert client.patch(BASE+'/notifications/'+notification['ref'],json={'read':False},headers=headers()).status_code==404
    path=BASE+f'/members/{ref(db,users,"two")}/follow'
    assert client.delete(path,headers=headers()).status_code==200
    assert follow(client,db,users).status_code==200
    assert client.get(BASE+'/feed',headers=headers('two')).json()['unreadCount']==0
    n=db.scalar(select(CommunityNotification).where(CommunityNotification.recipient_id==users['two'].id));n.created_at=now()-timedelta(days=2);db.commit()
    client.delete(path,headers=headers());follow(client,db,users)
    assert client.get(BASE+'/feed',headers=headers('two')).json()['unreadCount']==1
    assert db.scalar(select(func.count()).select_from(CommunityNotification))==2


def test_course_change_keeps_connections_and_allows_follow_back(community):
    client,db,users=community
    assert follow(client,db,users).status_code==200
    progression=db.scalar(select(StudentProgression).where(StudentProgression.student_id==users['two'].id));progression.course_id='other';db.commit()
    assert members(client).json()['members']==[]
    assert len(members(client,kind='following').json()['members'])==1
    assert follow(client,db,users,actor='two',target='one').status_code==200
    assert follow(client,db,users,target='three').status_code==403
    assert client.get(BASE+'/members/'+ref(db,users,'three'),headers=headers()).status_code==404


def test_hide_block_unblock_and_inactive_suppress_all_surfaces(community):
    client,db,users=community
    follow(client,db,users);follow(client,db,users,actor='two',target='one')
    p=db.get(CommunityProfile,users['two'].id);p.enabled=False;db.commit()
    for kind in ['discover','following','followers']:assert members(client,kind=kind).json()['members']==[]
    assert client.get(BASE+'/feed',headers=headers()).json()['unreadCount']==0
    assert client.get(BASE+'/members/'+p.public_ref,headers=headers()).status_code==404
    assert follow(client,db,users).status_code==404
    p.enabled=True;db.commit()
    assert members(client,kind='following').json()['members']
    path=BASE+'/members/'+p.public_ref+'/block'
    assert client.post(path,headers=headers()).status_code==200
    assert db.scalar(select(func.count()).select_from(CommunityFollow))==0
    assert db.scalar(select(func.count()).select_from(CommunityNotification))==0
    assert members(client).json()['members']==[]
    assert members(client,'two').json()['members']==[]
    assert follow(client,db,users,actor='two',target='one').status_code==404
    assert client.delete(path,headers=headers()).status_code==200
    assert not members(client).json()['members'][0]['following']
    follow(client,db,users);users['two'].is_active=False;db.commit()
    assert members(client,kind='following').json()['members']==[]
    assert client.get(BASE+'/feed',headers=headers('two')).status_code==401


def test_settings_opt_in_validation_uniqueness_and_no_subject_leakage(community):
    client,db,users=community
    assert client.get(BASE+'/settings',headers=headers('unconfigured')).json()['enabled'] is False
    assert members(client,'unconfigured').status_code==403
    good={'publicName':'Orbit Nova','enabled':True,'visibleSubjectIds':['science']}
    response=client.patch(BASE+'/settings',json=good,headers=headers())
    assert response.status_code==200 and response.json()['publicName']=='Orbit Nova'
    assert client.patch(BASE+'/settings',json={**good,'publicName':'Ｏｒｂｉｔ　Ｎｏｖａ','visibleSubjectIds':['maths']},headers=headers('two')).status_code==409
    for payload in [{**good,'visibleSubjectIds':['maths']},{**good,'publicName':'AKURU Admin'}, {**good,'publicName':'<script>'},{**good,'studentId':str(users['two'].id)},{**good,'enabled':'true'}]:
        assert client.patch(BASE+'/settings',json=payload,headers=headers()).status_code==422
    assert client.patch(BASE+'/settings',json={'publicName':'Comet One','enabled':True,'visibleSubjectIds':[]},headers=headers('unconfigured')).status_code==200
    assert members(client,'unconfigured').status_code==403
    assert client.get(BASE+'/settings',headers=headers('unconfigured')).json()['courses']==[]


def test_report_confidentiality_and_admin_name_change_workflow(community):
    client,db,users=community
    path=BASE+'/members/'+ref(db,users,'two')+'/report'
    assert client.post(path,json={'reason':'inappropriate_name'},headers=headers()).status_code==200
    assert client.post(path,json={'reason':'inappropriate_name'},headers=headers()).status_code==200
    assert client.get(BASE+'/reports',headers=headers()).status_code==403
    queue=client.get(BASE+'/reports',headers=headers('admin')).json()
    assert len(queue['reports'])==1
    assert set(queue['reports'][0])=={'ref','publicName','reason','status','createdAt'}
    assert 'reporter' not in str(queue).lower() and 'Private identity' not in str(queue)
    report=queue['reports'][0]['ref']
    assert client.patch(BASE+'/reports/'+report,json={'action':'name_change_required'},headers=headers('admin')).status_code==200
    assert members(client).json()['members']==[]
    draft={'publicName':'Novatwo','enabled':True,'visibleSubjectIds':['maths']}
    assert client.patch(BASE+'/settings',json=draft,headers=headers('two')).status_code==422
    assert client.patch(BASE+'/settings',json={**draft,'publicName':'New Comet'},headers=headers('two')).status_code==200
    assert members(client).json()['members'][0]['publicName']=='New Comet'
    assert db.scalar(select(func.count()).select_from(AuditEvent))>=3


@pytest.mark.parametrize('actor',['parent','admin'])
def test_role_and_csrf_boundaries(community,actor):
    client,db,users=community
    for path in ['/settings','/members?course=igcse','/feed','/blocks']:
        assert client.get(BASE+path,headers=headers(actor)).status_code==403
    assert client.get(BASE+'/settings').status_code==401
    assert client.post(BASE+'/members/'+ref(db,users,'two')+'/follow',headers=headers(csrf=False)).status_code==403
    assert client.patch(BASE+'/reports/report_'+'a'*32,json={'action':'dismissed'},headers=headers('admin',False)).status_code==403
    assert follow(client,db,users,target='one').status_code==404


def test_rate_limits_and_pagination_bounds(community):
    client,db,users=community
    p=db.get(CommunityProfile,users['one'].id);p.action_window=now();p.action_count=30;db.commit()
    assert follow(client,db,users).status_code==429
    for page in ['0','10001','bad']:
        assert members(client,page=page).status_code==422


def test_subject_filter_choices_respect_hidden_and_other_course_enrolments(community):
    client,db,users=community
    assert {s['id'] for s in client.get(BASE+'/subjects?course=igcse',headers=headers()).json()['subjects']}=={'science','maths'}
    db.get(CommunityProfile,users['two'].id).visible_subject_ids=[];db.commit()
    assert client.get(BASE+'/subjects?course=igcse',headers=headers()).json()['subjects']==[{'id':'science','name':'Science'}]
    assert client.get(BASE+'/subjects?course=other',headers=headers()).status_code==403


def test_postgres_serializes_duplicate_follow_and_block_races(community):
    client,db,users=community
    if db.bind.dialect.name!='postgresql':pytest.skip('Row-lock concurrency requires PostgreSQL')
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from app.services import community as service
    engine=db.bind
    actor,other=users['one'].id,users['two'].id
    target_ref=ref(db,users,'two')
    db.commit()
    barrier=Barrier(2)
    def operation(block=False):
        with Session(engine,expire_on_commit=False) as session:
            barrier.wait(timeout=10)
            try:
                return service.block(session,actor,target_ref) if block else service.follow(session,actor,target_ref)
            except HTTPException as error:
                session.rollback()
                return error.status_code
    with ThreadPoolExecutor(2) as pool:
        results=[pool.submit(operation) for _ in range(2)]
        assert all(isinstance(result.result(timeout=15),dict) for result in results)
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(CommunityFollow))==1
    assert db.scalar(select(func.count()).select_from(CommunityNotification))==1
    db.commit()
    barrier=Barrier(2)
    with ThreadPoolExecutor(2) as pool:
        results=[pool.submit(operation,block) for block in (False,True)]
        for result in results:result.result(timeout=15)
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(CommunityFollow))==0
    assert db.scalar(select(func.count()).select_from(CommunityNotification))==0
