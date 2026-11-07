import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from sqlmodel import Session, select
from app.database import engine
from app.models import AuthToken, User
from app.security import issue, digest

def register(client):
    client.headers.pop('Authorization', None)
    email = uuid.uuid4().hex + '@example.com'
    data = client.post('/auth/register', json={'name':'Learner','email':email,'password':'Password123','accepted_terms':True}).json()
    return data

def test_authentication_and_ownership(client, new_user, make_story):
    owner = new_user()
    story = make_story(owner['id'])
    sid = story['story']['id']
    vid = story['vocabulary'][0]['id']
    client.headers.pop('Authorization', None)
    assert client.get(f'/dashboard/{owner["id"]}').status_code == 401
    assert client.get(f'/quiz/story/{sid}').status_code == 401
    other = new_user()
    assert client.get(f'/dashboard/{owner["id"]}').status_code == 403
    assert client.get(f'/quiz/story/{sid}').status_code == 404
    assert client.post('/vocabulary/save', json={'user_id':other['id'],'vocabulary_id':vid}).status_code == 404
    assert client.post('/quiz/submit', json={'user_id':other['id'],'vocabulary_id':vid,'answer':'x'}).status_code == 404
    assert client.get('/admin/overview').status_code == 403
    assert client.get(f'/stories/{sid}', params={'user_id':owner['id']}).status_code == 403

def test_password_terms_normalization_logout_and_expiry(client):
    assert client.post('/auth/register', json={'name':'Test','email':'x@example.com','password':'Password123'}).status_code == 400
    for password in ['short1','onlyletters','12345678','a1'+'界'*24]:
        assert client.post('/auth/register', json={'name':'Test','email':uuid.uuid4().hex+'@example.com','password':password,'accepted_terms':True}).status_code == 400
    assert client.post('/auth/register', json={'name':'Test','email':'a@b','password':'Password123','accepted_terms':True}).status_code == 422
    data = register(client)
    token = data['access_token']
    client.headers['Authorization'] = 'Bearer '+token
    assert client.get('/auth/me').json()['user']['id'] == data['user']['id']
    assert client.post('/auth/logout').status_code == 200
    assert client.get('/auth/me').status_code == 401
    with Session(engine) as db:
        token = issue(db, data['user']['id'], minutes=-1)
    client.headers['Authorization'] = 'Bearer '+token
    assert client.get('/auth/me').status_code == 401
    assert client.post('/auth/login', json={'email':' '+data['user']['email'].upper()+' ','password':'Password123'}).status_code == 200

def test_admin_and_pagination(client, new_user, make_story):
    owner = new_user()
    for _ in range(3): make_story(owner['id'])
    first = client.get(f'/dashboard/{owner["id"]}?page_size=2').json()
    second = client.get(f'/dashboard/{owner["id"]}?page_size=2&stories_page=2').json()
    assert len(first['stories']) == 2 and len(second['stories']) == 1
    assert first['statistics']['total_stories'] == second['statistics']['total_stories'] == 3
    assert not {x['id'] for x in first['stories']} & {x['id'] for x in second['stories']}
    assert client.get(f'/dashboard/{owner["id"]}?page_size=1000').status_code == 422
    with Session(engine) as db:
        user = db.get(User, owner['id']); user.role='admin'; db.add(user); db.commit()
    assert client.get('/admin/overview').status_code == 200
    assert len(client.get('/admin/users?page_size=2').json()['data']) == 2
    assert client.get('/admin/users?page=0').status_code == 422

def test_reset_email_single_use_revokes_sessions(client, monkeypatch):
    data = register(client)
    monkeypatch.setenv('SMTP_HOST','smtp.example.com')
    monkeypatch.setenv('FRONTEND_URL','http://localhost:5500')
    from urllib.parse import urlparse, parse_qs
    with patch('app.routes.auth.smtplib.SMTP') as smtp:
        response = client.post('/auth/forgot-password', json={'email':data['user']['email']})
        assert response.status_code == 200 and 'token' not in response.json()
        message = smtp.return_value.__enter__.return_value.send_message.call_args.args[0]
        link = message.get_content().split('minutes: ')[1].split()[0]
        token = parse_qs(urlparse(link).query)['reset_token'][0]
    assert client.post('/auth/reset-password', json={'token':token,'password':'NewPassword456'}).status_code == 200
    assert client.post('/auth/reset-password', json={'token':token,'password':'NewPassword789'}).status_code == 401
    client.headers['Authorization']='Bearer '+data['access_token']
    assert client.get('/auth/me').status_code == 401
    assert client.post('/auth/login', json={'email':data['user']['email'],'password':'Password123'}).status_code == 401
    assert client.post('/auth/login', json={'email':data['user']['email'],'password':'NewPassword456'}).status_code == 200
    with patch('app.routes.auth.smtplib.SMTP') as smtp:
        unknown = client.post('/auth/forgot-password', json={'email':'unknown@example.com'})
        assert unknown.json() == response.json()
        smtp.assert_not_called()

def test_google_verification_nonce_and_account_collision(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID','test-client-id')
    email = uuid.uuid4().hex+'@gmail.com'
    nonce = client.get('/auth/google/nonce').json()['nonce']
    claims={'sub':uuid.uuid4().hex,'email':email,'name':'Google Learner','email_verified':True,'nonce':nonce}
    with patch('google.oauth2.id_token.verify_oauth2_token', return_value=claims) as verify:
        body={'credential':'signed-token','nonce':nonce,'accepted_terms':True}
        r=client.post('/auth/google',json=body)
        assert r.status_code == 200, r.text
        verify.assert_called_once()
        assert verify.call_args.args[2]=='test-client-id'
        assert client.post('/auth/google',json=body).status_code == 401
    existing=register(client)
    nonce=client.get('/auth/google/nonce').json()['nonce']
    claims.update(sub=uuid.uuid4().hex,email=existing['user']['email'],nonce=nonce)
    with patch('google.oauth2.id_token.verify_oauth2_token',return_value=claims):
        assert client.post('/auth/google',json={'credential':'x','nonce':nonce,'accepted_terms':True}).status_code == 409
    nonce=client.get('/auth/google/nonce').json()['nonce']
    with patch('google.oauth2.id_token.verify_oauth2_token',side_effect=ValueError('forged')):
        assert client.post('/auth/google',json={'credential':'forged','nonce':nonce}).status_code == 401

def test_login_rate_limit(client):
    for i in range(10):
        assert client.post('/auth/login',json={'email':'none@example.com','password':'Wrong123'}).status_code == 401
    assert client.post('/auth/login',json={'email':'none@example.com','password':'Wrong123'}).status_code == 429

def test_invalid_json_does_not_crash(client, new_user):
    new_user()
    assert client.post('/stories/generate', content='[]', headers={'Content-Type':'application/json'}).status_code == 422
    assert client.post('/stories/generate', content='{', headers={'Content-Type':'application/json'}).status_code == 422

def test_migrate_existing_database(tmp_path):
    from sqlalchemy import text, inspect
    from sqlmodel import create_engine
    from app.database import ensure_columns
    target=create_engine('sqlite:///'+str(tmp_path/'legacy.db'))
    with target.begin() as conn:
        conn.execute(text('CREATE TABLE users (id VARCHAR PRIMARY KEY, name VARCHAR, email VARCHAR, password_hash VARCHAR, created_at TIMESTAMP)'))
        conn.execute(text("INSERT INTO users VALUES ('old','Old learner','old@example.com','hash',CURRENT_TIMESTAMP)"))
    assert set(ensure_columns(target))=={'users.role','users.google_sub'}
    assert ensure_columns(target)==[]
    with target.connect() as conn:
        assert conn.execute(text("SELECT role FROM users WHERE id='old'")).scalar()=='user'
    assert any(i['unique'] for i in inspect(target).get_indexes('users'))
    target.dispose()

def test_google_rejects_unverified_email_and_wrong_nonce(client, monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID','test-client-id')
    nonce=client.get('/auth/google/nonce').json()['nonce']
    claims={'sub':'google-sub','email':'test@gmail.com','email_verified':False,'nonce':nonce}
    with patch('google.oauth2.id_token.verify_oauth2_token',return_value=claims):
        assert client.post('/auth/google',json={'credential':'x','nonce':nonce,'accepted_terms':True}).status_code == 401
        claims.update(email_verified=True,nonce='wrong')
        assert client.post('/auth/google',json={'credential':'x','nonce':nonce,'accepted_terms':True}).status_code == 401
