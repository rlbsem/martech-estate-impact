import os
from pathlib import Path
import uuid

import psycopg
from psycopg import sql
import pytest

from estate_impact import db
from estate_impact.demo import load_inputs, read
from estate_impact.snapshots import build

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def inputs():
    return load_inputs(ROOT)


@pytest.fixture
def snapshot(inputs):
    _, kwargs, resolutions = inputs
    return build(**kwargs, resolutions=resolutions)


@pytest.fixture
def proposal(snapshot):
    def load(name="retire-work-manager"):
        p = read(ROOT / f"fixtures/synthetic-estate/proposals/{name}.json")
        p["base_snapshot"] = snapshot["id"]
        return p

    return load


@pytest.fixture(scope="session")
def database():
    original = os.environ.get("ESTATE_DATABASE_URL")
    dsn = original or db.DEFAULT_DSN
    schema = "estate_test_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True, connect_timeout=10) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    os.environ["ESTATE_DATABASE_URL"] = psycopg.conninfo.make_conninfo(
        dsn, options=f"-c search_path={schema}"
    )
    db.migrate(ROOT)
    try:
        yield schema
    finally:
        if original is None:
            os.environ.pop("ESTATE_DATABASE_URL", None)
        else:
            os.environ["ESTATE_DATABASE_URL"] = original
        with psycopg.connect(dsn, autocommit=True, connect_timeout=10) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def fact(kind, subject, value, state="SUPPORTED"):
    return dict(
        kind=kind,
        subject=subject,
        value=value,
        state=state,
        evidence=[f"evidence:{kind}:{subject}"],
        dispositions={},
        candidates=[value],
    )


def graph(definitions, systems):
    facts = {
        f"system:{key}": fact("system", key, dict(label=key, lifecycle=value))
        for key, value in systems.items()
    }
    for key, (mode, providers) in definitions.items():
        inputs = []
        for i, provider in enumerate(providers):
            edge_key = f"dependency:{key}:{i}"
            inputs.append(edge_key)
            facts[edge_key] = fact(
                "dependency",
                f"{key}:{i}",
                dict(consumer=key, provider=provider, optional=False, qualified=True),
            )
        facts[f"requirement:{key}"] = fact(
            "requirement", key, dict(label=key, capability="test", mode=mode, inputs=inputs)
        )
    return facts
