import os
from pathlib import Path
import uuid

import psycopg
from psycopg import sql
import pytest

from estate_impact import db
from estate_change import service
from estate_change.evidence import load

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def estate():
    original = os.environ["ESTATE_DATABASE_URL"]
    schema = "change_test_" + uuid.uuid4().hex
    with psycopg.connect(original) as c:
        c.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    os.environ["ESTATE_DATABASE_URL"] = psycopg.conninfo.make_conninfo(
        original, options=f"-c search_path={schema}"
    )
    try:
        service.migrate(ROOT)
        prepared, snapshot, catalog = load(ROOT / "fixtures/change-assurance")
        service.publish(prepared, snapshot, catalog)
        yield prepared, snapshot, catalog, schema
    finally:
        os.environ["ESTATE_DATABASE_URL"] = original
        with psycopg.connect(original) as c:
            c.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


@pytest.fixture
def identity(estate):
    roles = []

    def create(companies):
        role = "test_review_" + uuid.uuid4().hex
        password = uuid.uuid4().hex
        roles.append(role)
        with db.connect() as c:
            c.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(role), sql.Literal(password)
                )
            )
            c.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(estate[3]), sql.Identifier(role)
                )
            )
            c.execute(
                sql.SQL("GRANT EXECUTE ON FUNCTION ca_decide(text,integer,text,text) TO {}").format(
                    sql.Identifier(role)
                )
            )
            c.execute("INSERT INTO ca_reviewer VALUES(%s,%s,true)", (role, companies))
        return psycopg.conninfo.make_conninfo(
            os.environ["ESTATE_DATABASE_URL"], user=role, password=password
        )

    yield create
    with db.connect() as c:
        for role in roles:
            c.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            c.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
