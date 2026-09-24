from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import uuid

import psycopg
import pytest

from estate_impact import db
from estate_impact.contracts import digest
from estate_impact.importers import prepare
from estate_impact.identity import index_crosswalk
from estate_impact.snapshots import build, check_identity


def test_actual_postgres_and_idempotent_migration(database):
    from conftest import ROOT

    db.migrate(ROOT)
    with db.connect() as conn:
        assert "PostgreSQL" in conn.execute("SELECT version()").fetchone()[0]


def test_snapshot_detaches_all_mutable_caller_inputs(inputs):
    _, kwargs, resolutions = deepcopy(inputs)
    published = build(**kwargs, resolutions=resolutions)
    before = deepcopy(published)
    kwargs["assertions"][0]["value"]["label"] = "edited after snapshot construction"
    kwargs["manifests"][0]["status"] = "failed"
    kwargs["policy"]["types"]["system"]["sources"].clear()
    resolutions[0]["reason"] = "changed review"
    assert published == before
    check_identity(published)


def test_concurrent_identical_import_commits_once(database, inputs):
    prepared, kwargs, _ = inputs
    artifact = deepcopy(prepared[0][0])
    artifact["artifact"] = f"concurrent-{uuid.uuid4().hex}.csv"
    artifact.pop("checksum")
    artifact.pop("id")
    text = "external_id,label,lifecycle,owner,operator,environment\ncrm,Sales CRM,active,Revenue Operations,Central Technology,production-model\n"
    item = prepare(text, artifact, index_crosswalk(kwargs["crosswalk"]))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: db.store_artifact(item), range(4)))
    assert results.count(True) == 1
    assert results.count(False) == 3
    assert len(db.load_assertions([item[0]["id"]])) == 2


def test_atomic_publication_immutability_and_roundtrip(database, inputs, snapshot):
    for item in inputs[0]:
        db.store_artifact(item)
    db.publish(snapshot)
    assert db.load_snapshot(snapshot["id"]) == snapshot
    assert db.publish(snapshot) is False
    with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
        with db.connect() as conn:
            conn.execute(
                "UPDATE estate_snapshot SET policy_hash='tampered' WHERE id=%s", (snapshot["id"],)
            )
    with db.connect() as conn:
        count = conn.execute(
            "SELECT count(*) FROM evidence_trace WHERE snapshot_id=%s", (snapshot["id"],)
        ).fetchone()[0]
        assert count == len(snapshot["assertions"])


def test_failed_publication_rolls_back_parent_and_children(database, inputs, snapshot):
    for item in inputs[0]:
        db.store_artifact(item)
    fact = snapshot["facts"]["system:crm"]
    fact["dispositions"]["nonexistent-assertion"] = "accepted"
    snapshot["id"] = digest({k: v for k, v in snapshot.items() if k != "id"})
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db.publish(snapshot)
    with db.connect() as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM estate_snapshot WHERE id=%s", (snapshot["id"],)
            ).fetchone()[0]
            == 0
        )
        assert (
            conn.execute(
                "SELECT count(*) FROM snapshot_fact WHERE snapshot_id=%s", (snapshot["id"],)
            ).fetchone()[0]
            == 0
        )


def test_failed_import_rolls_back_artifact(database, inputs):
    item = deepcopy(inputs[0][0])
    item[0]["id"] = uuid.uuid4().hex
    item[1][0]["kind"] = "untyped"
    with pytest.raises(psycopg.Error):
        db.store_artifact(item)
    with db.connect() as conn:
        assert (
            conn.execute(
                "SELECT count(*) FROM source_artifact WHERE id=%s", (item[0]["id"],)
            ).fetchone()[0]
            == 0
        )
