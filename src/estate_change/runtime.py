"""Task-owned loopback PostgreSQL cluster; credentials remain under ignored work/."""

import json
import os
import secrets
import shutil
import socket
import subprocess
from pathlib import Path

import psycopg
from psycopg import sql


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Runtime:
    def __init__(self, directory):
        self.path = Path(directory).resolve()
        self.owned = False
        self.old = os.environ.get("ESTATE_DATABASE_URL")

    def __enter__(self):
        if self.path.exists():
            raise ValueError("fresh private runtime directory required")
        self.path.mkdir(parents=True)
        try:
            self.dsn = os.environ.get("CHANGE_TEST_DATABASE_URL")
            if not self.dsn:
                prefix = Path(os.environ.get("PG_BIN", ""))
                init = prefix / ("initdb.exe" if os.name == "nt" else "initdb")
                if not init.is_file():
                    found = shutil.which("initdb")
                    if not found:
                        raise RuntimeError("PG_BIN or dedicated CHANGE_TEST_DATABASE_URL required")
                    prefix = Path(found).parent
                    init = Path(found)
                self.ctl = str(prefix / ("pg_ctl.exe" if os.name == "nt" else "pg_ctl"))
                password = secrets.token_urlsafe(32)
                pw = self.path / "password"
                pw.write_text(password, encoding="utf-8")
                port = free_port()
                with (self.path / "postgres-private.log").open("w") as log:
                    subprocess.run(
                        [
                            str(init),
                            "-D",
                            str(self.path / "data"),
                            "-U",
                            "estate",
                            "--auth=scram-sha-256",
                            "--pwfile",
                            str(pw),
                        ],
                        stdout=log,
                        stderr=log,
                        check=True,
                        timeout=60,
                    )
                    self.owned = True
                    subprocess.run(
                        [
                            self.ctl,
                            "-D",
                            str(self.path / "data"),
                            "-l",
                            str(self.path / "server-private.log"),
                            "-o",
                            f"-h 127.0.0.1 -p {port}",
                            "-w",
                            "start",
                        ],
                        stdout=log,
                        stderr=log,
                        check=True,
                        timeout=60,
                    )
                self.dsn = psycopg.conninfo.make_conninfo(
                    host="127.0.0.1", port=port, dbname="postgres", user="estate", password=password
                )
            # A supplied DSN must designate a dedicated empty test DB, never a remote system.
            info = psycopg.conninfo.conninfo_to_dict(self.dsn)
            if info.get("host") not in {"127.0.0.1", "localhost", "postgres"}:
                raise ValueError("local dedicated database required")
            with psycopg.connect(self.dsn) as c:
                if c.execute("SELECT to_regclass('public.ca_head')").fetchone()[0]:
                    raise ValueError("supplied database is not fresh")
            os.environ["ESTATE_DATABASE_URL"] = self.dsn
            (self.path / "admin.json").write_text(json.dumps({"dsn": self.dsn}), encoding="utf-8")
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def identity(self, name, companies=None, console=False, write=True):
        from estate_impact import db

        password = secrets.token_urlsafe(32)
        with db.connect() as c:
            c.execute(
                sql.SQL(
                    "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE"
                ).format(sql.Identifier(name), sql.Literal(password))
            )
            c.execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(name)))
            if console:
                c.execute(
                    sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA public TO {}").format(
                        sql.Identifier(name)
                    )
                )
                c.execute(
                    sql.SQL("ALTER ROLE {} SET default_transaction_read_only=on").format(
                        sql.Identifier(name)
                    )
                )
            else:
                c.execute("INSERT INTO ca_reviewer VALUES(%s,%s,true)", (name, companies))
                c.execute(
                    sql.SQL(
                        "GRANT EXECUTE ON FUNCTION ca_decide(text,integer,text,text) TO {}"
                    ).format(sql.Identifier(name))
                )
        dsn = psycopg.conninfo.make_conninfo(self.dsn, user=name, password=password)
        path = self.path / (name + ".json")
        if write:
            path.write_text(json.dumps({"dsn": dsn}), encoding="utf-8")
        return dsn

    def __exit__(self, *args):
        if self.old is None:
            os.environ.pop("ESTATE_DATABASE_URL", None)
        else:
            os.environ["ESTATE_DATABASE_URL"] = self.old
        if self.owned:
            with (self.path / "stop-private.log").open("w") as log:
                subprocess.run(
                    [self.ctl, "-D", str(self.path / "data"), "-m", "fast", "-w", "stop"],
                    stdout=log,
                    stderr=log,
                    check=True,
                    timeout=60,
                )
            self.owned = False
