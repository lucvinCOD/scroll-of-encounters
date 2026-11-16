"""Testes em PostgreSQL/WASM isolado; a fixture não representa o DDL remoto."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = ROOT / "supabase" / "migrations"
MIGRATION = MIGRATIONS / "20261111000100_make_match_end_time_optional.sql"
BRIDGE = Path(__file__).with_name("pglite_bridge.mjs")

# Tipos e dados adicionais abaixo são somente uma fixture descartável de teste.
# Não são baseline, seed da aplicação ou suposição sobre o esquema remoto.
FIXTURE = """
CREATE TABLE public.game_match (
    id integer PRIMARY KEY,
    match_date date NOT NULL,
    approximate_start_time time NULL,
    approximate_end_time time NOT NULL,
    status text NOT NULL
);
CREATE TABLE public.format (
    id integer PRIMARY KEY,
    daily_participation_limit integer,
    min_players integer,
    max_players integer
);
INSERT INTO public.game_match VALUES
    (1, '2026-09-15', NULL, '10:30', 'PENDING');
INSERT INTO public.format VALUES (1, 3, 2, 6);
"""


class MemoryPostgres:
    def __init__(self) -> None:
        node = shutil.which("node")
        if node is None:
            raise RuntimeError("Node.js é necessário. Instale as devDependencies com npm ci.")
        self.process = subprocess.Popen(
            [node, str(BRIDGE)],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        response = self.process.stdout.readline()
        if not response:
            _, error = self.process.communicate(timeout=10)
            raise RuntimeError(f"PGlite não iniciou; execute npm ci. {error}")
        if json.loads(response) != {"ready": True}:
            self.close()
            raise RuntimeError("Inicialização inesperada do PostgreSQL em memória.")

    def request(self, operation: str, sql: str) -> dict:
        self.process.stdin.write(json.dumps({"operation": operation, "sql": sql}) + "\n")
        self.process.stdin.flush()
        response = self.process.stdout.readline()
        if not response:
            raise RuntimeError("PostgreSQL em memória encerrou sem responder.")
        return json.loads(response)

    def execute(self, sql: str) -> None:
        result = self.request("exec", sql)
        if "error" in result:
            raise RuntimeError(result["error"])

    def query(self, sql: str) -> list[dict]:
        result = self.request("query", sql)
        if "error" in result:
            raise RuntimeError(result["error"])
        return result["rows"]

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.stdin.write('{"operation":"close"}\n')
            self.process.stdin.flush()
        try:
            self.process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.communicate()


class MigrationLayoutTests(unittest.TestCase):
    def test_single_cli_history_and_unique_timestamp(self) -> None:
        paths = sorted(MIGRATIONS.glob("*.sql"))
        self.assertTrue(paths)
        versions = []
        for path in paths:
            match = re.fullmatch(r"(\d{14})_[a-z0-9_]+\.sql", path.name)
            self.assertIsNotNone(match, path.name)
            versions.append(match.group(1))
        self.assertEqual(len(versions), len(set(versions)))
        for old_directory in ("versions", "rollbacks", "drafts"):
            self.assertFalse(list((ROOT / "backend/migrations" / old_directory).rglob("*.sql")))

    def test_cli_uses_migrations_without_seed_or_declarative_schema(self) -> None:
        config = tomllib.loads((ROOT / "supabase/config.toml").read_text(encoding="utf-8"))
        self.assertTrue(config["db"]["migrations"]["enabled"])
        self.assertEqual(config["db"]["migrations"]["schema_paths"], [])
        self.assertFalse(config["db"]["seed"]["enabled"])
        self.assertEqual(config["db"]["seed"]["sql_paths"], [])


class OptionalEndTimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = MemoryPostgres()
        self.addCleanup(self.database.close)
        self.database.execute(FIXTURE)
        self.migration = MIGRATION.read_text(encoding="utf-8")

    def snapshot(self) -> list[dict]:
        return self.database.query(
            "SELECT to_jsonb(m) AS record FROM public.game_match m ORDER BY id"
        )

    def end_is_required(self) -> bool:
        return self.database.query("""
            SELECT attnotnull AS required FROM pg_catalog.pg_attribute
            WHERE attrelid = 'public.game_match'::regclass
              AND attname = 'approximate_end_time'
              AND NOT attisdropped
        """)[0]["required"]

    def test_preserves_historical_row_and_all_format_values(self) -> None:
        matches = self.snapshot()
        formats = self.database.query("SELECT to_jsonb(f) AS record FROM public.format f")
        self.database.execute(self.migration)
        self.assertFalse(self.end_is_required())
        self.assertEqual(self.snapshot(), matches)
        self.assertEqual(
            self.database.query("SELECT to_jsonb(f) AS record FROM public.format f"), formats
        )
        self.assertIsNone(self.snapshot()[0]["record"]["approximate_start_time"])

    def test_reapplication_preserves_rows_including_new_null_end(self) -> None:
        self.database.execute(self.migration)
        self.database.execute("""
            INSERT INTO public.game_match VALUES
                (2, '2026-09-16', '11:00', NULL, 'PENDING')
        """)
        before = self.snapshot()
        self.database.execute(self.migration)
        self.database.execute(self.migration)
        self.assertFalse(self.end_is_required())
        self.assertEqual(self.snapshot(), before)

    def test_only_end_nullability_changes_in_column_definitions(self) -> None:
        sql = """
            SELECT attname, atttypid, atttypmod, attnotnull, attidentity,
                   attgenerated, atthasdef
            FROM pg_catalog.pg_attribute
            WHERE attrelid = 'public.game_match'::regclass
              AND attnum > 0 AND NOT attisdropped ORDER BY attnum
        """
        before = self.database.query(sql)
        self.database.execute(self.migration)
        expected = [dict(column) for column in before]
        for column in expected:
            if column["attname"] == "approximate_end_time":
                column["attnotnull"] = False
        self.assertEqual(self.database.query(sql), expected)

    def test_preserves_existing_defaults_and_precision(self) -> None:
        self.database.execute("""
            ALTER TABLE public.game_match
                ALTER COLUMN approximate_end_time TYPE time(0),
                ALTER COLUMN approximate_end_time SET DEFAULT '12:34'::time
        """)
        self.database.execute(self.migration)
        column = self.database.query("""
            SELECT data_type, datetime_precision, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'game_match'
              AND column_name = 'approximate_end_time'
        """)[0]
        self.assertEqual(column["datetime_precision"], 0)
        self.assertEqual(column["is_nullable"], "YES")
        self.assertIn("12:34", column["column_default"])

    def test_missing_start_fails_without_changing_end(self) -> None:
        self.database.execute("ALTER TABLE public.game_match DROP COLUMN approximate_start_time")
        with self.assertRaisesRegex(RuntimeError, "Pré-condição ausente"):
            self.database.execute(self.migration)
        self.assertTrue(self.end_is_required())

    def test_wrong_start_type_fails_without_changing_data(self) -> None:
        self.database.execute("""
            ALTER TABLE public.game_match ALTER COLUMN approximate_start_time
                TYPE text USING approximate_start_time::text
        """)
        before = self.snapshot()
        with self.assertRaisesRegex(RuntimeError, "Schema divergente"):
            self.database.execute(self.migration)
        self.assertTrue(self.end_is_required())
        self.assertEqual(self.snapshot(), before)

    def test_wrong_end_type_fails_without_changing_data(self) -> None:
        self.database.execute("""
            ALTER TABLE public.game_match ALTER COLUMN approximate_end_time
                TYPE text USING approximate_end_time::text
        """)
        before = self.snapshot()
        with self.assertRaisesRegex(RuntimeError, "Schema divergente"):
            self.database.execute(self.migration)
        self.assertTrue(self.end_is_required())
        self.assertEqual(self.snapshot(), before)

    def test_missing_end_is_not_recreated(self) -> None:
        self.database.execute("ALTER TABLE public.game_match DROP COLUMN approximate_end_time")
        before = self.snapshot()
        with self.assertRaisesRegex(RuntimeError, "Pré-condição ausente"):
            self.database.execute(self.migration)
        self.assertEqual(self.snapshot(), before)

    def test_missing_table_is_not_recreated(self) -> None:
        self.database.execute("ALTER TABLE public.game_match RENAME TO saved_game_match")
        with self.assertRaises(RuntimeError):
            self.database.execute(self.migration)
        self.assertIsNone(self.database.query(
            "SELECT to_regclass('public.game_match')::text AS relation"
        )[0]["relation"])

    def test_restores_lock_timeout(self) -> None:
        self.database.execute("SET lock_timeout = '2s'")
        self.database.execute(self.migration)
        self.assertEqual(self.database.query("SHOW lock_timeout")[0]["lock_timeout"], "2s")

    def test_caller_transaction_can_roll_back_the_schema_change(self) -> None:
        before = self.snapshot()
        self.database.execute("BEGIN")
        self.database.execute(self.migration)
        self.assertFalse(self.end_is_required())
        self.database.execute("ROLLBACK")
        self.assertTrue(self.end_is_required())
        self.assertEqual(self.snapshot(), before)

    def test_read_only_inspection_scripts_execute_without_changing_rows(self) -> None:
        before = self.snapshot()
        for path in sorted((ROOT / "backend/migrations/checks").glob("*.sql")):
            self.database.execute(path.read_text(encoding="utf-8"))
        self.assertEqual(self.snapshot(), before)
        self.assertTrue(self.end_is_required())


if __name__ == "__main__":
    unittest.main()
