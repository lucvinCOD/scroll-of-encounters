from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import time
import unittest
import psycopg
from local_postgres import LocalPostgres, ROOT

ACTOR="00000000-0000-4000-8000-000000000001"
SQL=(ROOT / "supabase/migrations/20261111000200_mvp_match_registration.sql").read_text(encoding="utf-8")
ONBOARDING=(ROOT / "supabase/migrations/20261111000300_verified_account_onboarding.sql").read_text(encoding="utf-8")
FIXTURE=(Path(__file__).parent / "fixtures/mvp_schema.sql").read_text(encoding="utf-8")

class MatchDatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=LocalPostgres()
        with cls.server.connect() as connection:
            connection.execute("CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role;")
    @classmethod
    def tearDownClass(cls): cls.server.close()
    def setUp(self):
        self.connection=self.server.connect()
        self.addCleanup(self.connection.close)
        self.connection.execute("DROP SCHEMA IF EXISTS soe_private CASCADE; DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT USAGE ON SCHEMA public TO anon,authenticated,service_role;")
        self.connection.execute(FIXTURE)
        self.before=self.connection.execute("SELECT to_jsonb(m) FROM public.game_match m WHERE id=1").fetchone()[0]
        self.connection.execute(SQL)
        self.connection.execute(ONBOARDING)
    def register(self, start="10:00", date="2001-01-01", players=None, winner=1, draw=False, community=1, format=1, actor=ACTOR, connection=None):
        return (connection or self.connection).execute("SELECT public.soe_register_match(%s,%s,%s,%s::date,%s::time,%s::bigint[],%s,%s)",(actor,community,format,date,start,players if players is not None else [1,2],winner,draw)).fetchone()[0]
    def test_preserves_historical_data_and_reapplication(self):
        self.connection.execute(SQL)
        self.assertEqual(self.connection.execute("SELECT to_jsonb(m) FROM public.game_match m WHERE id=1").fetchone()[0],self.before)
    def test_winner_and_pending(self):
        match=self.register()
        self.assertEqual(match['status'],'PENDING')
        self.assertEqual(self.connection.execute("SELECT player_id,result FROM public.match_participant WHERE match_id=%s ORDER BY player_id",(match['id'],)).fetchall(),[(1,'WIN'),(2,'LOSS')])
        self.assertEqual(self.connection.execute("SELECT created_by::text FROM public.game_match WHERE id=%s",(match['id'],)).fetchone()[0],ACTOR)
    def test_account_onboarding_is_atomic_and_idempotent(self):
        actor='00000000-0000-4000-8000-000000000003'
        self.connection.execute('INSERT INTO auth.users VALUES(%s)',(actor,))
        self.assertTrue(self.connection.execute('SELECT public.soe_identity(%s)',(actor,)).fetchone()[0]['needs_profile'])
        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            self.connection.execute('SELECT public.soe_complete_profile(%s,%s,%s)',(actor,'Novo jogador',999))
        self.assertIsNone(self.connection.execute('SELECT id FROM public.profile WHERE id=%s',(actor,)).fetchone())
        profile=self.connection.execute('SELECT public.soe_complete_profile(%s,%s,%s)',(actor,'Novo jogador',1)).fetchone()[0]
        self.assertFalse(profile['needs_profile'])
        self.assertIsNotNone(profile['player_id'])
        self.connection.execute(ONBOARDING)
        same=self.connection.execute('SELECT public.soe_complete_profile(%s,%s,%s)',(actor,'Outro nome',2)).fetchone()[0]
        self.assertEqual(profile,same)
        self.assertEqual(self.connection.execute('SELECT count(*) FROM public.player WHERE profile_id=%s',(actor,)).fetchone()[0],1)
    def test_onboarding_rejects_unknown_actor_taken_name_and_suspended_profile(self):
        actor='00000000-0000-4000-8000-000000000003'
        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            self.connection.execute('SELECT public.soe_complete_profile(%s,%s,1)',(actor,'Nao autenticado'))
        self.connection.execute('INSERT INTO auth.users VALUES(%s)',(actor,))
        with self.assertRaises(psycopg.errors.UniqueViolation):
            self.connection.execute('SELECT public.soe_complete_profile(%s,%s,1)',(actor,'testador'))
        self.connection.execute("UPDATE public.profile SET status='SUSPENDED' WHERE id=%s",(ACTOR,))
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            self.connection.execute('SELECT public.soe_complete_profile(%s,%s,1)',(ACTOR,'Reativar'))
        self.assertEqual(self.connection.execute('SELECT status FROM public.profile WHERE id=%s',(ACTOR,)).fetchone()[0],'SUSPENDED')
    def test_onboarding_is_not_executable_by_browser_roles(self):
        for role in ['anon','authenticated']:
            self.connection.execute(f'SET ROLE {role}')
            try:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    self.connection.execute('SELECT public.soe_complete_profile(%s,%s,1)',(ACTOR,'Alterado'))
            finally: self.connection.execute('RESET ROLE')
    def test_table_draw(self):
        match=self.register(winner=None,draw=True)
        self.assertEqual(self.connection.execute("SELECT DISTINCT result FROM public.match_participant WHERE match_id=%s",(match['id'],)).fetchall(),[('DRAW',)])
    def test_invalid_winner_and_duplicate_players_and_missing_identity(self):
        for params in [{'winner':8},{'players':[1,1]},{'players':[1,999]},{'draw':True},{'players':[1]},{'players':[1,2,3,4,5]}]:
            with self.subTest(params=params),self.assertRaises(psycopg.Error): self.register(**params)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM public.game_match").fetchone()[0],1)
    def test_atomic_failure_no_orphans(self):
        with self.assertRaises(psycopg.errors.ForeignKeyViolation): self.register(community=999)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM public.game_match").fetchone()[0],1)
        self.assertEqual(self.connection.execute("SELECT count(*) FROM public.match_participant").fetchone()[0],2)
    def test_less_than_ten_minutes_and_exact_boundary(self):
        self.register()
        with self.assertRaises(psycopg.errors.ExclusionViolation): self.register(start='10:09:59')
        with self.assertRaises(psycopg.errors.ExclusionViolation): self.register(start='09:50:01')
        self.register(start='10:10')
        self.register(start='09:50')
    def test_cross_midnight(self):
        self.register(start='23:56')
        with self.assertRaises(psycopg.errors.ExclusionViolation): self.register(date='2001-01-02',start='00:05')
        self.register(date='2001-01-02',start='00:06')
    def test_relevant_statuses_and_cancelled(self):
        for day,status in [(2,'PENDING'),(3,'VERIFIED'),(4,'DISPUTED')]:
            date=f'2001-01-0{day}'
            match=self.register(date=date)
            self.connection.execute("UPDATE public.game_match SET status=%s WHERE id=%s",(status,match['id']))
            with self.assertRaises(psycopg.errors.ExclusionViolation): self.register(date=date,start='10:05')
        match=self.register(date='2001-01-05')
        self.connection.execute("UPDATE public.game_match SET status='CANCELLED' WHERE id=%s",(match['id'],))
        self.register(date='2001-01-05',start='10:00')
    def test_guests_other_authors_and_other_communities(self):
        self.register()
        with self.assertRaises(psycopg.errors.ExclusionViolation): self.register(start='10:05',players=[2,3],winner=3,community=2,format=2,actor='00000000-0000-4000-8000-000000000002')
        self.register(players=[3,4],winner=3)
    def test_no_daily_or_retroactive_limit(self):
        for number in range(20): self.register(date='1998-06-01',start=f'{number//6:02}:{(number%6)*10:02}')
        self.assertEqual(self.connection.execute("SELECT count(*) FROM public.game_match WHERE match_date='1998-06-01'").fetchone()[0],20)
    def test_duplicates_warn_without_blocking(self):
        self.register()
        match=self.register(start='11:00')
        self.assertIn('possible_duplicate',[warning['code'] for warning in match['warnings']])
    def test_unknown_historical_start_warns_without_fabricating(self):
        match=self.register(date='2026-09-15')
        self.assertIn('unknown_historical_start',[warning['code'] for warning in match['warnings']])
        self.assertIsNone(self.connection.execute("SELECT approximate_start_time FROM public.game_match WHERE id=1").fetchone()[0])
    def test_edit_time_and_participants_rechecks(self):
        self.register()
        match=self.register(start='11:00')
        with self.assertRaises(psycopg.errors.ExclusionViolation): self.connection.execute("UPDATE public.game_match SET approximate_start_time='10:05' WHERE id=%s",(match['id'],))
        other=self.register(players=[3,4],winner=3)
        with self.assertRaises(psycopg.errors.ExclusionViolation): self.connection.execute("UPDATE public.match_participant SET player_id=1 WHERE match_id=%s AND player_id=3",(other['id'],))
    def test_concurrent_participant_addition_and_time_edit_are_serialized(self):
        self.register()
        other=self.register(start='11:00',players=[3,4],winner=3)
        added=threading.Event()
        def add_participant():
            with self.server.connect(autocommit=False) as connection:
                connection.execute("INSERT INTO public.match_participant(match_id,player_id,result) VALUES(%s,2,'LOSS')",(other['id'],))
                added.set()
                time.sleep(.25)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pending=pool.submit(add_participant)
            self.assertTrue(added.wait(timeout=5))
            with self.assertRaises(psycopg.errors.ExclusionViolation):
                self.connection.execute("UPDATE public.game_match SET approximate_start_time='10:05' WHERE id=%s",(other['id'],))
            pending.result(timeout=5)
        self.assertEqual(str(self.connection.execute('SELECT approximate_start_time FROM public.game_match WHERE id=%s',(other['id'],)).fetchone()[0]),'11:00:00')
    def test_fixed_snapshot_transactions_are_rejected(self):
        with self.server.connect(autocommit=False) as connection:
            connection.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            with self.assertRaises(psycopg.errors.SerializationFailure): self.register(connection=connection)
            connection.rollback()
    def test_database_rejects_invalid_results_and_participant_deletion(self):
        match=self.register()
        with self.assertRaises(psycopg.errors.CheckViolation): self.connection.execute("UPDATE public.match_participant SET result='WIN' WHERE match_id=%s",(match['id'],))
        with self.assertRaises(psycopg.errors.CheckViolation): self.connection.execute("DELETE FROM public.match_participant WHERE match_id=%s AND player_id=1",(match['id'],))
    def test_only_service_role_can_call_public_capabilities(self):
        for role in ['anon','authenticated']:
            self.connection.execute(f'SET ROLE {role}')
            try:
                with self.assertRaises(psycopg.errors.InsufficientPrivilege): self.connection.execute("SELECT public.soe_catalog()")
            finally: self.connection.execute('RESET ROLE')
        self.connection.execute('SET ROLE service_role')
        try:
            self.assertEqual(self.connection.execute('SELECT public.soe_catalog()').fetchone()[0]['verified_matches'],0)
            self.register()
        finally: self.connection.execute('RESET ROLE')
    def test_two_concurrent_sessions_cannot_register_conflicting_matches(self):
        barrier=threading.Barrier(2)
        def attempt():
            try:
                with self.server.connect(autocommit=False) as connection:
                    barrier.wait(timeout=5)
                    self.register(connection=connection)
                    time.sleep(.15)
                return 'committed'
            except psycopg.errors.ExclusionViolation: return 'conflict'
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(lambda _:attempt(),range(2)))
        self.assertEqual(sorted(results),['committed','conflict'])
        self.assertEqual(self.connection.execute("SELECT count(*) FROM public.game_match WHERE match_date='2001-01-01'").fetchone()[0],1)
