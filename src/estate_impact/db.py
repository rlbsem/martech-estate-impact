"""PostgreSQL only. Transactions are the publication boundary."""

import os
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

DEFAULT_DSN = "postgresql://estate:estate@127.0.0.1:55439/estate"


def connect():
    return psycopg.connect(os.environ.get("ESTATE_DATABASE_URL", DEFAULT_DSN), connect_timeout=10)


def migrate(root):
    with connect() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(4187051)")
        conn.execute((Path(root) / "migrations/001_estate_model.sql").read_text())


def store_artifact(prepared):
    artifact, assertions, quarantine = prepared
    with connect() as conn:
        inserted = conn.execute(
            "INSERT INTO source_artifact VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id",
            (
                artifact["id"],
                artifact["source"],
                artifact["checksum"],
                artifact["parser"],
                artifact["collected_at"],
                Jsonb(artifact["scope"]),
                artifact["status"],
                Jsonb(artifact),
            ),
        ).fetchone()
        if not inserted:
            return False
        for claim in assertions:
            conn.execute(
                "INSERT INTO assertion VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    claim["id"],
                    artifact["id"],
                    claim["key"],
                    claim["kind"],
                    claim["subject"],
                    claim["location"],
                    Jsonb(claim["value"]),
                    Jsonb(claim),
                ),
            )
        for i, item in enumerate(quarantine):
            conn.execute(
                "INSERT INTO identity_quarantine VALUES (%s,%s,%s)",
                (artifact["id"], i, Jsonb(item)),
            )
    return True


def load_assertions(artifact_ids):
    with connect() as conn:
        return [
            r[0]
            for r in conn.execute(
                "SELECT payload FROM assertion WHERE artifact_id = ANY(%s) ORDER BY id",
                (artifact_ids,),
            )
        ]


def publish(snapshot):
    from .snapshots import check_identity

    check_identity(snapshot)
    with connect() as conn:
        inserted = conn.execute(
            "INSERT INTO estate_snapshot(id,as_of,policy_hash,payload) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING id",
            (snapshot["id"], snapshot["as_of"], snapshot["policy_hash"], Jsonb(snapshot)),
        ).fetchone()
        if not inserted:
            return False
        for key, fact in snapshot["facts"].items():
            conn.execute(
                "INSERT INTO snapshot_fact VALUES (%s,%s,%s,%s,%s,%s)",
                (
                    snapshot["id"],
                    key,
                    fact["kind"],
                    fact["subject"],
                    fact["state"],
                    Jsonb(fact["value"]),
                ),
            )
            for assertion_id, disposition in fact["dispositions"].items():
                conn.execute(
                    "INSERT INTO snapshot_assertion VALUES (%s,%s,%s)",
                    (snapshot["id"], assertion_id, disposition),
                )
    return True


def load_snapshot(identity):
    with connect() as conn:
        row = conn.execute(
            "SELECT payload FROM estate_snapshot WHERE id=%s", (identity,)
        ).fetchone()
        if row is None:
            raise ValueError("snapshot not found")
        return row[0]


def save_assessment(result):
    with connect() as conn:
        conn.execute(
            "INSERT INTO assessment VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            (
                result["id"],
                result["snapshot_id"],
                result["proposal_hash"],
                result["implementation"],
                Jsonb(result),
            ),
        )
