"""PostgreSQL descart?vel, exclusivamente em loopback; nunca aceita DSN remoto."""
from pathlib import Path
import os
import shutil
import socket
import subprocess
import tempfile
import time
import psycopg

ROOT = Path(__file__).resolve().parents[2]

class LocalPostgres:
    def __init__(self):
        self.root = (ROOT / "supabase/.temp/test-databases").resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="mvp-", dir=self.root)
        self.directory = Path(self.temporary.name).resolve()
        assert self.directory.is_relative_to(self.root)
        binary = ROOT / "node_modules/@embedded-postgres/windows-x64/native/bin"
        self.initdb = str(binary / "initdb.exe") if os.name == "nt" else shutil.which("initdb")
        self.postgres = str(binary / "postgres.exe") if os.name == "nt" else shutil.which("postgres")
        if not self.initdb or not Path(self.initdb).exists():
            raise RuntimeError("PostgreSQL local ausente. Execute npm ci na raiz; em Linux configure initdb/postgres no PATH.")
        flags = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        subprocess.run([self.initdb,"-D",str(self.directory / "data"),"-U","postgres","--auth=trust","--encoding=UTF8","--locale=C"], check=True, capture_output=True, **flags)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0)); self.port=sock.getsockname()[1]
        self.log = (self.directory / "server.log").open("wb")
        self.process = subprocess.Popen([self.postgres,"-D",str(self.directory / "data"),"-h","127.0.0.1","-p",str(self.port),"-F"], stdout=self.log, stderr=self.log, **flags)
        for attempt in range(150):
            try:
                with self.connect() as connection: connection.execute("SELECT 1")
                return
            except psycopg.OperationalError:
                if self.process.poll() is not None: raise RuntimeError("Servidor PostgreSQL de teste encerrou; confira o log local ignorado.")
                time.sleep(.05)
        raise RuntimeError("Timeout inicializando PostgreSQL local.")

    def connect(self, autocommit=True):
        return psycopg.connect(host="127.0.0.1",port=self.port,user="postgres",dbname="postgres",autocommit=autocommit,connect_timeout=2)

    def close(self):
        if hasattr(self,"process"):
            # pg_ctl envia shutdown limpo ao ?nico diret?rio gerado para esta execu??o.
            pg_ctl=str(Path(self.postgres).with_name("pg_ctl.exe" if os.name=="nt" else "pg_ctl"))
            subprocess.run([pg_ctl,"-D",str(self.directory / "data"),"stop","-m","fast","-w"],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0,timeout=15)
            self.process.wait(timeout=10)
            self.log.close()
        assert self.directory.resolve().is_relative_to(self.root)
        self.temporary.cleanup()
