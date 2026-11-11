from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import time
import unittest
import sys

import psycopg

from local_postgres import LocalPostgres, ROOT
sys.path.insert(0, str(ROOT / "backend"))
from scripts.admin_operation import operation_sql

USER = "00000000-0000-4000-8000-000000000001"
MOD = "00000000-0000-4000-8000-000000000002"
ADMIN = "00000000-0000-4000-8000-000000000003"
OTHER = "00000000-0000-4000-8000-000000000004"
MIGRATION = ROOT / "supabase/migrations/20261111000400_account_permissions_and_moderation.sql"
REASON = "Revisado pelo operador local de testes."


class PermissionsDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LocalPostgres()
        with cls.server.connect() as connection:
            connection.execute("CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role;")

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def setUp(self):
        self.db = self.server.connect()
        self.addCleanup(self.db.close)
        self.db.execute("DROP SCHEMA IF EXISTS soe_private CASCADE; DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT USAGE ON SCHEMA public TO anon,authenticated,service_role;")
        self.db.execute((Path(__file__).parent / "fixtures/mvp_schema.sql").read_text(encoding="utf-8"))
        for name in ["20261111000200_mvp_match_registration.sql", "20261111000300_verified_account_onboarding.sql", MIGRATION.name]:
            self.db.execute((MIGRATION.parent / name).read_text(encoding="utf-8"))
        self.db.execute("INSERT INTO auth.users VALUES(%s),(%s)", (ADMIN, OTHER))
        self.db.execute("INSERT INTO public.profile(id,username) VALUES(%s,'Administrador de teste'),(%s,'Outro usuario')", (ADMIN, OTHER))

    def bootstrap(self):
        return self.db.execute("SELECT soe_private.manage_admin(%s,true,%s,true)", (ADMIN, REASON)).fetchone()[0]

    def assign(self, target=MOD, community=1, enabled=True, actor=ADMIN, connection=None):
        return (connection or self.db).execute("SELECT public.soe_set_moderator(%s,%s,%s,%s,%s)", (actor, target, community, enabled, REASON)).fetchone()[0]

    def prepare_mod(self):
        self.bootstrap()
        self.assign()
        self.db.execute("UPDATE public.game_match SET status='DISPUTED' WHERE id=1")

    def resolve(self, actor=MOD, decision="VERIFY", match_id=1, reason=REASON, connection=None):
        return (connection or self.db).execute("SELECT public.soe_resolve_dispute(%s,%s,%s,%s)", (actor, match_id, decision, reason)).fetchone()[0]

    def identity(self, actor):
        return self.db.execute("SELECT public.soe_identity(%s)", (actor,)).fetchone()[0]

    def test_new_and_existing_accounts_default_to_user_without_promotions(self):
        self.assertEqual(self.db.execute("SELECT count(*) FROM soe_private.platform_admin").fetchone()[0], 0)
        self.assertEqual(self.identity(USER)["role"], "USER")
        newcomer = "00000000-0000-4000-8000-000000000005"
        self.db.execute("INSERT INTO auth.users VALUES(%s)", (newcomer,))
        self.assertEqual(self.identity(newcomer)["role"], "USER")
        result = self.db.execute("SELECT public.soe_complete_profile(%s,'Novo usuario',1)", (newcomer,)).fetchone()[0]
        self.assertEqual(result["role"], "USER")
        self.assertEqual(result["moderated_community_ids"], [])

    def test_user_cannot_access_governance_or_assign_permissions(self):
        self.bootstrap()
        for sql, args in [
            ("SELECT public.soe_admin_users(%s)", (USER,)),
            ("SELECT public.soe_moderation_matches(%s)", (USER,)),
            ("SELECT public.soe_moderation_match(%s,1)", (USER,)),
            ("SELECT public.soe_admin_audit(%s)", (USER,)),
        ]:
            with self.subTest(sql=sql), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                self.db.execute(sql, args)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.assign(target=USER, actor=USER)
        self.assertEqual(self.identity(USER)["role"], "USER")

    def test_admin_grants_and_revokes_multiple_community_assignments_immediately(self):
        self.bootstrap()
        self.assign()
        self.assign(community=2)
        self.assertEqual(self.identity(MOD)["moderated_community_ids"], [1, 2])
        self.assign(enabled=False)
        self.assertEqual(self.identity(MOD)["moderated_community_ids"], [2])
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.db.execute("SELECT public.soe_moderation_matches(%s,1)", (MOD,))
        self.assign(community=2, enabled=False)
        self.assertEqual(self.identity(MOD)["role"], "USER")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.db.execute("SELECT public.soe_moderation_matches(%s)", (MOD,))

    def test_scope_limits_list_and_direct_detail_and_decision(self):
        self.prepare_mod()
        match = self.db.execute("SELECT public.soe_register_match(%s,2,1,'2001-01-01','10:00',ARRAY[3,4]::bigint[],3,false)", (USER,)).fetchone()[0]
        self.db.execute("UPDATE public.game_match SET status='DISPUTED' WHERE id=%s", (match["id"],))
        items = self.db.execute("SELECT public.soe_moderation_matches(%s)", (MOD,)).fetchone()[0]
        self.assertEqual([m["id"] for m in items["items"]], [1])
        for sql in ["SELECT public.soe_moderation_match(%s,%s)", "SELECT public.soe_resolve_dispute(%s,%s,'CANCEL','Justificativa de testes')"]:
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                self.db.execute(sql, (MOD, match["id"]))
        all_matches = self.db.execute("SELECT public.soe_moderation_matches(%s)", (ADMIN,)).fetchone()[0]
        self.assertEqual(all_matches["total"], 2)

    def test_moderator_and_admin_cannot_review_participation_or_own_publication(self):
        self.prepare_mod()
        self.assign(target=USER)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege): self.resolve(actor=USER)
        self.db.execute("UPDATE public.player SET profile_id=%s WHERE id=2", (MOD,))
        with self.assertRaises(psycopg.errors.InsufficientPrivilege): self.resolve()
        self.db.execute("UPDATE public.player SET profile_id=%s WHERE id=2", (ADMIN,))
        with self.assertRaises(psycopg.errors.InsufficientPrivilege): self.resolve(actor=ADMIN)

    def test_verified_decision_and_audit_are_atomic_and_readable_to_authorized_reviewer(self):
        self.prepare_mod()
        result = self.resolve()
        self.assertEqual(result["status"], "VERIFIED")
        event = result["resolution_history"][0]
        self.assertEqual(event["actor_id"], MOD)
        self.assertEqual(event["reason"], REASON)
        self.assertIsNotNone(event["occurred_at"])
        self.assertEqual(event["previous"]["status"], "DISPUTED")
        self.assertEqual(event["next"]["status"], "VERIFIED")
        self.assertEqual(self.db.execute("SELECT public.soe_catalog()").fetchone()[0]["verified_matches"], 1)
        with self.assertRaises(psycopg.errors.SerializationFailure): self.resolve()
        self.assertEqual(self.db.execute("SELECT count(*) FROM soe_private.security_audit WHERE match_id=1").fetchone()[0], 1)

    def test_cancel_preserves_participants_and_requires_a_reason(self):
        self.prepare_mod()
        before = self.db.execute("SELECT to_jsonb(p) FROM public.match_participant p ORDER BY id").fetchall()
        with self.assertRaises(psycopg.errors.InvalidParameterValue): self.resolve(reason="curta")
        self.assertEqual(self.resolve(decision="CANCEL")["status"], "CANCELLED")
        self.assertEqual(self.db.execute("SELECT to_jsonb(p) FROM public.match_participant p ORDER BY id").fetchall(), before)

    def test_audit_write_failure_rolls_back_resolution(self):
        self.prepare_mod()
        self.db.execute("ALTER TABLE soe_private.security_audit ADD CONSTRAINT local_fail CHECK(action<>'DISPUTE_RESOLVED')")
        with self.assertRaises(psycopg.errors.CheckViolation): self.resolve()
        self.assertEqual(self.db.execute("SELECT status FROM public.game_match WHERE id=1").fetchone()[0], "DISPUTED")

    def test_rls_default_deny_even_if_table_privilege_is_accidentally_granted(self):
        self.bootstrap()
        self.assign()
        tables = "soe_private.platform_admin,soe_private.community_moderator,soe_private.security_audit"
        self.db.execute("GRANT USAGE ON SCHEMA soe_private TO anon,authenticated")
        self.db.execute(f"GRANT SELECT,INSERT,UPDATE,DELETE ON {tables} TO anon,authenticated")
        for role in ["anon", "authenticated"]:
            self.db.execute(f"SET ROLE {role}")
            try:
                for table in tables.split(","):
                    self.assertEqual(self.db.execute(f"SELECT count(*) FROM {table}").fetchone()[0], 0)
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    self.db.execute("INSERT INTO soe_private.platform_admin(profile_id) VALUES(%s)", (USER,))
                self.assertEqual(self.db.execute("DELETE FROM soe_private.community_moderator RETURNING profile_id").fetchall(), [])
            finally: self.db.execute("RESET ROLE")
        self.assertEqual(self.identity(MOD)["role"], "MODERATOR")

    def test_rpc_and_bootstrap_grants_do_not_allow_direct_client_escalation(self):
        for role in ["anon", "authenticated", "service_role"]:
            self.db.execute(f"SET ROLE {role}")
            try:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    self.db.execute("SELECT soe_private.manage_admin(%s,true,%s,true)", (USER, REASON))
                if role != "service_role":
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                        self.db.execute("SELECT public.soe_admin_users(%s)", (USER,))
            finally: self.db.execute("RESET ROLE")
        self.bootstrap()
        self.db.execute("SET ROLE service_role")
        try:
            self.assertEqual(self.db.execute("SELECT public.soe_admin_users(%s)", (ADMIN,)).fetchone()[0]["total"], 4)
            with self.assertRaises(psycopg.errors.InsufficientPrivilege): self.assign(actor=USER)
        finally: self.db.execute("RESET ROLE")

    def test_bootstrap_explicit_once_last_admin_protected_and_subsequent_operator_flow_audited(self):
        self.bootstrap()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.db.execute("SELECT soe_private.manage_admin(%s,true,%s,true)", (OTHER, REASON))
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.db.execute("SELECT soe_private.manage_admin(%s,false,%s)", (ADMIN, REASON))
        self.db.execute("SELECT soe_private.manage_admin(%s,true,%s)", (OTHER, REASON))
        self.db.execute("SELECT soe_private.manage_admin(%s,false,%s)", (ADMIN, REASON))
        self.assertEqual(self.identity(ADMIN)["role"], "USER")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.db.execute("SELECT public.soe_admin_users(%s)", (ADMIN,))
        self.assertEqual(self.db.execute("SELECT public.soe_admin_audit(%s)", (OTHER,)).fetchone()[0]["total"], 3)

    def test_operator_sql_generator_quotes_reason_and_never_selects_first_user(self):
        reason = "Revisao O'Brian \\ teste'); DELETE FROM public.profile; --"
        sql = operation_sql(ADMIN, "bootstrap", reason)
        self.db.execute(sql)
        self.assertEqual(self.identity(ADMIN)["role"], "ADMIN")
        self.assertEqual(self.identity(USER)["role"], "USER")
        self.assertEqual(self.db.execute("SELECT reason FROM soe_private.security_audit").fetchone()[0], reason)
        for target in ["invalid", "00000000-0000-0000-0000-000000000000"]:
            with self.assertRaises(ValueError): operation_sql(target, "bootstrap", REASON)

    def test_audit_is_append_only_and_reapplication_preserves_data(self):
        self.bootstrap()
        self.assign()
        before = self.db.execute("SELECT to_jsonb(a) FROM soe_private.security_audit a ORDER BY id").fetchall()
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.db.execute("UPDATE soe_private.security_audit SET reason='Outra justificativa longa'")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege): self.db.execute("DELETE FROM soe_private.security_audit")
        self.db.execute(MIGRATION.read_text(encoding="utf-8"))
        self.assertEqual(self.db.execute("SELECT to_jsonb(a) FROM soe_private.security_audit a ORDER BY id").fetchall(), before)
        self.assertEqual(self.identity(ADMIN)["role"], "ADMIN")
        self.assertEqual(str(self.db.execute("SELECT approximate_end_time FROM public.game_match WHERE id=1").fetchone()[0]), "10:30:00")

    def test_concurrent_resolution_commits_only_one_decision(self):
        self.prepare_mod()
        self.assign(target=OTHER)
        barrier = threading.Barrier(2)
        def decide(actor):
            try:
                with self.server.connect(autocommit=False) as connection:
                    barrier.wait(timeout=5)
                    self.resolve(actor=actor, connection=connection)
                    time.sleep(.1)
                return "committed"
            except psycopg.errors.SerializationFailure: return "already_resolved"
        with ThreadPoolExecutor(max_workers=2) as pool: outcomes = list(pool.map(decide, [MOD, OTHER]))
        self.assertEqual(sorted(outcomes), ["already_resolved", "committed"])
        self.assertEqual(self.db.execute("SELECT count(*) FROM soe_private.security_audit WHERE match_id=1").fetchone()[0], 1)

    def test_revocation_is_serialized_and_subsequent_authorization_denied(self):
        self.prepare_mod()
        locked = threading.Event()
        def revoke():
            with self.server.connect(autocommit=False) as connection:
                self.assign(enabled=False, connection=connection)
                locked.set()
                time.sleep(.2)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(revoke)
            self.assertTrue(locked.wait(timeout=5))
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                self.db.execute("SELECT public.soe_moderation_matches(%s)", (MOD,))
            pending.result(timeout=5)
