import sys
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app

ACTOR = "00000000-0000-4000-8000-000000000001"
TARGET = "00000000-0000-4000-8000-000000000002"
ORIGIN = {"Origin": "http://127.0.0.1:5173"}
HEADERS = {"Authorization": "Bearer fixture-only-session"}
ASSIGNMENT = {"profile_id": TARGET, "community_id": 1, "enabled": True, "reason": "Responsavel pela comunidade de testes."}


class PermissionsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.identity = {"id": ACTOR, "username": "Testador", "player_id": 1, "role": "USER", "moderated_community_ids": []}
        self.auth = self.enterContext(patch("app.auth.auth_request", AsyncMock(return_value={"id": ACTOR})))
        self.account = self.enterContext(patch("app.auth.rpc", AsyncMock(side_effect=lambda *args: dict(self.identity))))
        self.rpc = self.enterContext(patch("app.services.governance.rpc", AsyncMock(return_value={"items": [], "total": 0})))

    def test_missing_and_invalid_tokens_are_401(self):
        self.assertEqual(self.client.get("/admin/users").status_code, 401)
        self.auth.side_effect = HTTPException(401, "Sessao invalida")
        self.assertEqual(self.client.get("/moderation/matches", headers=HEADERS).status_code, 401)
        self.rpc.assert_not_awaited()

    def test_user_cannot_enter_protected_areas_or_assign_self(self):
        for path in ["/admin/users", "/admin/audit", "/moderation/matches", "/moderation/matches/1"]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, headers=HEADERS).status_code, 403)
        self.assertEqual(self.client.post("/admin/moderators", headers=HEADERS, json={**ASSIGNMENT, "profile_id": ACTOR}).status_code, 403)
        self.assertEqual(self.client.post("/moderation/matches/1/resolution", headers=HEADERS, json={"decision": "VERIFY", "reason": ASSIGNMENT["reason"]}).status_code, 403)
        self.rpc.assert_not_awaited()

    def test_public_signup_rejects_privilege_selection(self):
        with patch("app.routers.auth.auth_request", AsyncMock()) as signup:
            for extra in [{"role": "ADMIN"}, {"role": "MODERATOR"}, {"moderated_community_ids": [1]}]:
                response = self.client.post("/auth/signup", json={"email": "fixture@example.test", "password": "fixture-only-password", **extra}, headers=ORIGIN)
                self.assertEqual(response.status_code, 422)
            signup.assert_not_awaited()

    def test_token_metadata_never_overrides_database_permissions(self):
        self.auth.return_value = {"id": ACTOR, "user_metadata": {"role": "ADMIN"}, "app_metadata": {"role": "ADMIN"}}
        self.assertEqual(self.client.get("/admin/users", headers=HEADERS).status_code, 403)
        self.assertEqual(self.client.get("/auth/permissions", headers=HEADERS).json(), {"role": "USER", "moderated_community_ids": []})

    def test_moderator_scopes_are_forwarded_and_database_denial_preserved(self):
        self.identity.update(role="MODERATOR", moderated_community_ids=[1])
        self.assertEqual(self.client.get("/moderation/matches?community_id=1", headers=HEADERS).status_code, 200)
        self.assertEqual(self.rpc.call_args.args[1]["p_actor"], ACTOR)
        self.assertEqual(self.rpc.call_args.args[1]["p_community"], 1)
        self.rpc.side_effect = HTTPException(403, "Fora da comunidade autorizada")
        self.assertEqual(self.client.get("/moderation/matches?community_id=2", headers=HEADERS).status_code, 403)
        self.assertEqual(self.client.get("/moderation/matches/99", headers=HEADERS).status_code, 403)
        self.assertEqual(self.client.get("/admin/users", headers=HEADERS).status_code, 403)

    def test_admin_assigns_and_revokes_with_verified_actor_and_no_client_actor_override(self):
        self.identity.update(role="ADMIN")
        for enabled in [True, False]:
            response = self.client.post("/admin/moderators", json={**ASSIGNMENT, "enabled": enabled}, headers=HEADERS)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.rpc.call_args.args[1]["p_actor"], ACTOR)
            self.assertEqual(self.rpc.call_args.args[1]["p_enabled"], enabled)
        self.assertEqual(self.client.post("/admin/moderators", json={**ASSIGNMENT, "actor": TARGET}, headers=HEADERS).status_code, 422)
        self.assertEqual(self.client.post("/admin/moderators", json={**ASSIGNMENT, "role": "ADMIN"}, headers=HEADERS).status_code, 422)
        schema = self.client.get("/openapi.json").json()["paths"]
        self.assertFalse(any("bootstrap" in path or "admin/grant" in path for path in schema))

    def test_next_request_observes_revoked_permissions_without_new_token(self):
        self.identity.update(role="MODERATOR", moderated_community_ids=[1])
        self.assertEqual(self.client.get("/moderation/matches", headers=HEADERS).status_code, 200)
        self.identity.update(role="USER", moderated_community_ids=[])
        self.assertEqual(self.client.get("/moderation/matches", headers=HEADERS).status_code, 403)
        self.assertEqual(self.rpc.await_count, 1)

    def test_cookie_admin_write_requires_trusted_origin(self):
        self.identity.update(role="ADMIN")
        self.client.cookies.set("soe_access", "fixture-only-session")
        self.assertEqual(self.client.post("/admin/moderators", json=ASSIGNMENT, headers={"Origin": "https://untrusted.example"}).status_code, 403)
        self.rpc.assert_not_awaited()

    def test_self_review_and_stale_dispute_errors_are_preserved(self):
        self.identity.update(role="MODERATOR", moderated_community_ids=[1])
        for status in [403, 409]:
            self.rpc.side_effect = HTTPException(status, "Decisao bloqueada")
            response = self.client.post("/moderation/matches/1/resolution", headers=HEADERS, json={"decision": "VERIFY", "reason": ASSIGNMENT["reason"]})
            self.assertEqual(response.status_code, status)
        for body in [{"decision": "VERIFIED", "reason": ASSIGNMENT["reason"]}, {"decision": "VERIFY", "reason": "curta"}, {"decision": "VERIFY", "reason": ASSIGNMENT["reason"], "participant_ids": [1, 2]}]:
            self.assertEqual(self.client.post("/moderation/matches/1/resolution", headers=HEADERS, json=body).status_code, 422)

    def test_sensitive_read_is_no_store_and_pagination_is_validated(self):
        self.identity.update(role="ADMIN")
        response = self.client.get("/admin/users?q=Teste&limit=20&offset=0", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(self.client.get("/admin/users?limit=101", headers=HEADERS).status_code, 422)
        self.assertEqual(self.client.get("/moderation/matches?community_id=-1", headers=HEADERS).status_code, 422)
