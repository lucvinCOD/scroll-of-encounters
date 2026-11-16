import sys
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.main import app
from app.auth import writing_user

ACTOR="00000000-0000-4000-8000-000000000001"
BODY={"community_id":1,"format_id":1,"match_date":"1998-01-01","approximate_start_time":"10:00","participant_ids":[1,2],"result":{"type":"winner","winner_player_id":1}}

class MatchApiTests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(app)
        self.addCleanup(self.client.close)
        self.addCleanup(app.dependency_overrides.clear)
    def test_health_and_docs(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertEqual(self.client.get('/docs').status_code,200)
        schema=self.client.get('/openapi.json').json()
        self.assertIn('/matches',schema['paths'])
    def test_anonymous_cannot_write(self):
        self.assertEqual(self.client.post('/matches',json=BODY,headers={'Origin':'http://127.0.0.1:5173'}).status_code,401)
    def test_author_comes_from_verified_auth_user_not_client(self):
        with patch('app.auth.auth_request',AsyncMock(return_value={'id':ACTOR})),patch('app.auth.rpc',AsyncMock(return_value={'id':ACTOR,'username':'Testador'})),patch('app.services.matches.rpc',AsyncMock(return_value={'id':2,'status':'PENDING','warnings':[]})) as save:
            response=self.client.post('/matches',json=BODY,headers={'Authorization':'Bearer test-session'})
            self.assertEqual(response.status_code,201)
            self.assertEqual(save.call_args.args[1]['p_actor'],ACTOR)
            response=self.client.post('/matches',json={**BODY,'created_by':'outro-autor'},headers={'Authorization':'Bearer test-session'})
            self.assertEqual(response.status_code,422)
            self.assertEqual(save.await_count,1)
    def test_invalid_result_duplicate_and_missing_players(self):
        app.dependency_overrides[writing_user]=lambda:{'id':ACTOR}
        for override in [{'participant_ids':[1,1]},{'participant_ids':[1]},{'result':{'type':'winner','winner_player_id':3}},{'result':{'type':'draw','winner_player_id':1}},{'approximate_start_time':'10:00+03:00'}]:
            with self.subTest(override=override): self.assertEqual(self.client.post('/matches',json={**BODY,**override}).status_code,422)
    def test_conflict_http_409_is_preserved(self):
        app.dependency_overrides[writing_user]=lambda:{'id':ACTOR}
        with patch('app.services.matches.rpc',AsyncMock(side_effect=HTTPException(409,'Conflito temporal'))):
            self.assertEqual(self.client.post('/matches',json=BODY).status_code,409)
    def test_draw_payload(self):
        app.dependency_overrides[writing_user]=lambda:{'id':ACTOR}
        with patch('app.services.matches.rpc',AsyncMock(return_value={'id':2,'status':'PENDING','warnings':[]})) as save:
            self.assertEqual(self.client.post('/matches',json={**BODY,'result':{'type':'draw'}}).status_code,201)
            self.assertTrue(save.call_args.args[1]['p_draw'])
            self.assertIsNone(save.call_args.args[1]['p_winner'])
    def test_invalid_session_is_rejected(self):
        with patch('app.auth.auth_request',AsyncMock(side_effect=HTTPException(401,'Sess?o inv?lida'))):
            self.assertEqual(self.client.post('/matches',json=BODY,headers={'Authorization':'Bearer invalid-session'}).status_code,401)
    def test_cookie_request_requires_trusted_origin(self):
        self.client.cookies.set('soe_access','test-session')
        with patch('app.auth.auth_request',AsyncMock(return_value={'id':ACTOR})) as verify:
            self.assertEqual(self.client.post('/matches',json=BODY,headers={'Origin':'https://untrusted.example'}).status_code,403)
            verify.assert_not_awaited()
    def test_login_tokens_remain_http_only(self):
        session={'access_token':'test-session','refresh_token':'test-refresh','expires_in':3600,'user':{'id':ACTOR}}
        with patch('app.routers.auth.auth_request',AsyncMock(return_value=session)),patch('app.routers.auth.rpc',AsyncMock(return_value={'id':ACTOR,'username':'Testador','player_id':1})):
            response=self.client.post('/auth/login',json={'email':'test@example.test','password':'local-fixture-only'},headers={'Origin':'http://127.0.0.1:5173'})
            self.assertEqual(response.status_code,200)
            self.assertNotIn('access_token',response.json())
            for cookie in response.headers.get_list('set-cookie'):
                self.assertIn('HttpOnly',cookie)
                self.assertIn('SameSite=lax',cookie)
    def test_catalog_routes_and_history_pagination(self):
        catalog={'communities':[],'players':[],'formats':[],'games':[]}
        with patch('app.routers.matches.catalog',AsyncMock(return_value=catalog)):
            for path in ['/catalog','/communities/','/formats/']: self.assertEqual(self.client.get(path).status_code,200)
        self.assertEqual(self.client.get('/matches/?limit=101').status_code,422)
    def test_signup_requires_email_confirmation_without_returning_tokens(self):
        with patch('app.routers.auth.auth_request',AsyncMock(return_value={'id':ACTOR})):
            response=self.client.post('/auth/signup',json={'email':'test@example.test','password':'fixture-only-password'},headers={'Origin':'http://127.0.0.1:5173'})
            self.assertEqual(response.status_code,201)
            self.assertEqual(response.json(),{'confirmation_required':True})
            self.assertFalse(response.headers.get_list('set-cookie'))
    def test_profile_actor_is_verified_and_unprovisioned_user_cannot_register(self):
        with patch('app.auth.auth_request',AsyncMock(return_value={'id':ACTOR})),patch('app.routers.auth.rpc',AsyncMock(return_value={'id':ACTOR})) as save:
            response=self.client.post('/auth/profile',json={'username':'Novo jogador','community_id':1},headers={'Authorization':'Bearer fixture-session'})
            self.assertEqual(response.status_code,200)
            self.assertEqual(save.call_args.args[1]['p_actor'],ACTOR)
            self.assertEqual(self.client.post('/auth/profile',json={'username':'Novo jogador','community_id':1,'actor':'forjado'},headers={'Authorization':'Bearer fixture-session'}).status_code,422)
        with patch('app.auth.auth_request',AsyncMock(return_value={'id':ACTOR})),patch('app.auth.rpc',AsyncMock(return_value={'id':ACTOR,'needs_profile':True})):
            self.assertEqual(self.client.post('/matches',json=BODY,headers={'Authorization':'Bearer fixture-session'}).status_code,403)
    def test_confirmation_session_checks_user_and_keeps_tokens_http_only(self):
        session={'access_token':'fixture-new-access','refresh_token':'fixture-new-refresh','user':{'id':ACTOR}}
        with patch('app.routers.auth.auth_request',AsyncMock(side_effect=[{'id':ACTOR},session])),patch('app.routers.auth.rpc',AsyncMock(return_value={'id':ACTOR,'needs_profile':True})):
            response=self.client.post('/auth/session',json={'access_token':'fixture-access','refresh_token':'fixture-refresh'},headers={'Origin':'http://127.0.0.1:5173'})
            self.assertEqual(response.status_code,200)
            self.assertNotIn('access_token',response.text)
            self.assertTrue(all('HttpOnly' in cookie for cookie in response.headers.get_list('set-cookie')))
        with patch('app.routers.auth.auth_request',AsyncMock(side_effect=[{'id':ACTOR},{**session,'user':{'id':'another-user'}}])):
            self.assertEqual(self.client.post('/auth/session',json={'access_token':'fixture-access','refresh_token':'fixture-refresh'},headers={'Origin':'http://127.0.0.1:5173'}).status_code,401)
    def test_recovery_is_generic_and_new_password_requires_valid_session(self):
        with patch('app.routers.auth.auth_request',AsyncMock(return_value={})):
            response=self.client.post('/auth/recover',json={'email':'test@example.test'},headers={'Origin':'http://127.0.0.1:5173'})
            self.assertEqual(response.status_code,202)
        self.assertEqual(self.client.post('/auth/password',json={'password':'fixture-new-password'},headers={'Origin':'http://127.0.0.1:5173'}).status_code,401)
        with patch('app.auth.auth_request',AsyncMock(return_value={'id':ACTOR})),patch('app.routers.auth.auth_request',AsyncMock(return_value={})) as change:
            self.assertEqual(self.client.post('/auth/password',json={'password':'fixture-new-password'},headers={'Authorization':'Bearer fixture-access'}).status_code,204)
            self.assertEqual(change.call_args.kwargs['method'],'PUT')
