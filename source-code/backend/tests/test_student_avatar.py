"""Isolated HTTP persistence tests: never write the configured local/production DB."""
import json
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.v1.student_avatar import router
from app.database import get_db
from app.models import User, StudentProfile, AuditEvent, StudentProgression, StudentSubject
from app.schemas.student_avatar import CATALOGUE, StudentAvatarConfig, public_avatar
from app.security import Principal, digest, get_principal


@pytest.fixture
def avatar_client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    for table in (User.__table__, StudentProfile.__table__, AuditEvent.__table__, StudentProgression.__table__, StudentSubject.__table__):
        table.create(engine)
    with Session(engine, expire_on_commit=False) as db:
        users = {name: User(id=uuid.uuid4(), username=name, display_name=name, role=role, password_hash='unused-test-only', must_change_password=False) for name, role in [('parent','parent'),('admin','admin'),('one','student'),('two','student'),('missing','student'),('other-parent','parent'),('other','student')]}
        db.add_all(users.values()); db.flush()
        db.add_all([StudentProfile(student_id=users[name].id, parent_id=users['parent'].id) for name in ('one','two')]); db.add(StudentProfile(student_id=users['other'].id,parent_id=users['other-parent'].id)); db.commit()
        app = FastAPI(); app.include_router(router, prefix='/api/v1')
        def principal(request: Request):
            actor = request.headers.get('X-Test-Actor')
            if actor not in users: raise HTTPException(401)
            return Principal(users[actor], SimpleNamespace(csrf_hash=digest('test-csrf')))
        app.dependency_overrides[get_principal] = principal
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as client:
            yield client, db, users, engine
    engine.dispose()


def headers(actor='one', csrf=True):
    return {'X-Test-Actor': actor, **({'X-CSRF-Token':'test-csrf'} if csrf else {})}


def test_save_is_self_scoped_and_survives_a_new_database_session(avatar_client):
    client, db, users, engine = avatar_client
    assert client.get('/api/v1/student/avatar', headers=headers()).json() == {'avatar': None}
    payload = CATALOGUE['presets'][3]
    response = client.patch('/api/v1/student/avatar', json=payload, headers=headers())
    assert response.status_code == 200 and response.json()['avatar'] == payload
    assert response.headers['cache-control'] == 'no-store'
    assert client.get('/api/v1/student/avatar', headers=headers('two')).json() == {'avatar':None}
    with Session(engine) as fresh:
        assert fresh.get(StudentProfile, users['one'].id).avatar_config == payload
        assert fresh.get(StudentProfile, users['two'].id).avatar_config is None
    assert db.scalar(select(AuditEvent.action)) == 'student.avatar.saved'
    assert client.get('/api/v1/student/avatar', headers=headers()).json()['avatar'] == payload


def test_reset_only_clears_the_authenticated_student_avatar(avatar_client):
    client, db, users, _ = avatar_client
    for actor, preset in [('one',0),('two',1)]:
        assert client.patch('/api/v1/student/avatar',json=CATALOGUE['presets'][preset],headers=headers(actor)).status_code == 200
    assert client.delete('/api/v1/student/avatar', headers=headers()).json() == {'avatar':None}
    assert db.get(User,users['one'].id) is not None
    assert client.get('/api/v1/student/avatar',headers=headers('two')).json()['avatar'] == CATALOGUE['presets'][1]


@pytest.mark.parametrize('actor',['parent','admin'])
def test_non_students_cannot_read_or_modify_the_student_endpoint(avatar_client,actor):
    client, _, _, _ = avatar_client
    for method in ('get','patch','delete'):
        kwargs = {'json':CATALOGUE['presets'][0]} if method=='patch' else {}
        assert getattr(client,method)('/api/v1/student/avatar',headers=headers(actor),**kwargs).status_code == 403


def test_authentication_csrf_and_missing_profile_are_enforced(avatar_client):
    client, _, _, _ = avatar_client
    assert client.get('/api/v1/student/avatar').status_code == 401
    assert client.patch('/api/v1/student/avatar',json=CATALOGUE['presets'][0],headers=headers(csrf=False)).status_code == 403
    assert client.delete('/api/v1/student/avatar',headers=headers(csrf=False)).status_code == 403
    assert client.get('/api/v1/student/avatar',headers=headers('missing')).status_code == 404


@pytest.mark.parametrize('change',[{'studentId':'another-student'},{'skin':'<svg onload=alert(1)>'},{'hairColor':'url(https://example.com/x)'},{'glasses':'toString'},{'version':2},{'version':True},{'eyes':22},{'upload':'data:image/svg+xml,bad'}])
def test_unknown_fields_versions_and_unapproved_options_are_rejected(avatar_client,change):
    client, _, _, _ = avatar_client
    response = client.patch('/api/v1/student/avatar',json={**CATALOGUE['presets'][0],**change},headers=headers())
    assert response.status_code == 422
    assert client.get('/api/v1/student/avatar',headers=headers()).json()['avatar'] is None


def test_catalogues_match_and_each_supported_option_is_validated():
    frontend = Path(__file__).parents[2] / 'frontend/lib/avatar-catalogue.json'
    assert json.loads(frontend.read_text()) == CATALOGUE
    for field, options in CATALOGUE['options'].items():
        for option in options:
            StudentAvatarConfig.model_validate({**CATALOGUE['presets'][0],field:option})
    assert public_avatar({'version':999}) is None
    assert public_avatar(None) is None


def test_authorized_portal_rows_include_only_own_or_linked_avatars(avatar_client):
    from app.services.portal import student_rows
    client, db, users, _ = avatar_client
    payload = CATALOGUE['presets'][0]
    client.patch('/api/v1/student/avatar', json=payload, headers=headers())
    own = student_rows(db, Principal(users['one'], None))
    assert len(own) == 1 and own[0]['id'] == str(users['one'].id)
    assert own[0]['avatar'] == payload
    family = student_rows(db, Principal(users['parent'], None))
    assert {row['id'] for row in family} == {str(users['one'].id), str(users['two'].id)}
    assert next(row for row in family if row['id'] == str(users['one'].id))['avatar'] == payload
    other_family = student_rows(db, Principal(users['other-parent'], None))
    assert len(other_family) == 1 and other_family[0]['avatar'] is None


def test_full_app_allows_avatar_patch_preflight_from_configured_origin():
    from app.main import app
    from app.config import get_settings
    settings = get_settings()
    with TestClient(app, base_url='http://127.0.0.1') as client:
        response = client.options('/api/v1/student/avatar', headers={
            'Origin': settings.cors_origins[0],
            'Access-Control-Request-Method': 'PATCH',
            'Access-Control-Request-Headers': 'Content-Type, X-CSRF-Token',
        })
    assert response.status_code == 200
    assert 'PATCH' in response.headers['access-control-allow-methods']


def test_saved_avatar_survives_the_real_state_response_contract(avatar_client, monkeypatch):
    """Exercise the HTTP serialization boundary used by both profile and top bar."""
    from app.api.v1.accounts import router as accounts_router
    from app.schemas.portal import PortalStateResponse
    from app.services import portal
    client, db, users, _ = avatar_client
    client.app.include_router(accounts_router, prefix='/api/v1')

    def state_response(session, principal):
        return {
            'user': {'id':str(principal.user.id),'username':principal.user.username,
                'name':principal.user.display_name,'role':principal.user.role,'mustChangePassword':False},
            'catalog': {'courses':[],'activeCourses':[],'grades':[],'terms':[],'kinds':[],'progressionPairs':[]},
            'accounts':[], 'subjects':[], 'students':portal.student_rows(session,principal),
        }
    monkeypatch.setattr(portal, 'get_portal_state', state_response)
    config = CATALOGUE['presets'][3]
    assert client.patch('/api/v1/student/avatar',json=config,headers=headers()).status_code == 200
    for _ in range(2):
        response = client.get('/api/v1/state',headers=headers())
        assert response.status_code == 200
        own = response.json()['students']
        assert len(own) == 1
        assert own[0]['avatar'] == config
        assert PortalStateResponse.model_validate(response.json()).students[0].avatar.model_dump() == config
    family = client.get('/api/v1/state',headers=headers('parent')).json()['students']
    assert next(row for row in family if row['id']==str(users['one'].id))['avatar'] == config
    sibling = client.get('/api/v1/state',headers=headers('two')).json()['students']
    assert len(sibling) == 1 and sibling[0]['avatar'] is None
    other = client.get('/api/v1/state',headers=headers('other-parent')).json()['students']
    assert len(other) == 1 and other[0]['avatar'] is None
    assert client.delete('/api/v1/student/avatar',headers=headers()).status_code == 200
    assert client.get('/api/v1/state',headers=headers()).json()['students'][0]['avatar'] is None
