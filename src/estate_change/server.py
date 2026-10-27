"""Loopback read-only console. No SQL, review, import or execution endpoint."""

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from estate_impact import db
from .service import view

WEB = Path(__file__).with_name("web")


def verify_role():
    with db.connect() as c:
        row = c.execute(
            "SELECT rolsuper,rolcreaterole,rolcreatedb FROM pg_roles WHERE rolname=current_user"
        ).fetchone()
        if any(row):
            raise ValueError("console requires restricted database identity")
        for table in [
            "ca_head",
            "ca_proposal",
            "ca_version",
            "ca_decision",
            "estate_snapshot",
            "assertion",
        ]:
            if c.execute(
                "SELECT has_table_privilege(current_user,%s,'INSERT,UPDATE,DELETE,TRUNCATE')",
                (table,),
            ).fetchone()[0]:
                raise ValueError("console identity has write privileges")
        if c.execute(
            "SELECT has_function_privilege(current_user,'ca_decide(text,integer,text,text)','EXECUTE')"
        ).fetchone()[0]:
            raise ValueError("console must not have review authority")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, body, mime):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        assets = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/style.css": ("style.css", "text/css; charset=utf-8"),
        }
        if path in assets:
            file, mime = assets[path]
            self.reply(200, (WEB / file).read_bytes(), mime)
        elif path == "/api/estate":
            try:
                self.reply(200, json.dumps(view()).encode(), "application/json")
            except Exception:
                self.reply(
                    503, b'{"error":"Evidence unavailable; no readiness claim"}', "application/json"
                )
        else:
            self.reply(404, b"Not found", "text/plain")

    def do_POST(self):
        self.reply(405, b"Read-only console", "text/plain")

    do_PUT = do_POST
    do_DELETE = do_POST
    do_PATCH = do_POST


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--port", type=int, default=8594)
    p.add_argument("--container", action="store_true")
    a = p.parse_args()
    os.environ["ESTATE_DATABASE_URL"] = json.loads(a.config.read_text())["dsn"]
    verify_role()
    ThreadingHTTPServer(
        ("0.0.0.0" if a.container else "127.0.0.1", a.port), Handler
    ).serve_forever()


if __name__ == "__main__":
    main()
