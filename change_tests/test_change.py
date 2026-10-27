from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import os

import psycopg
from psycopg.types.json import Jsonb
import pytest

from estate_impact import db
from estate_impact.contracts import digest
from estate_impact.requirements import evaluate as engine
from estate_change import service
from estate_change.demo import proposals
from estate_change.evidence import load, prepare, read
from conftest import ROOT


def selected(estate, name="reassignment", index=0):
    return deepcopy(proposals(estate[1])[name][index])


def test_scoped_identities_and_real_provenance(estate):
    s = db.load_snapshot(estate[1]["id"])
    assert {
        s["facts"][f"system:{co}/crm"]["value"]["label"] for co in ["atlas", "boreal", "cinder"]
    } == {"Atlas CRM", "Boreal CRM", "Cinder CRM"}
    with db.connect() as c:
        assert c.execute(
            "SELECT count(*) FROM evidence_trace WHERE snapshot_id=%s", (s["id"],)
        ).fetchone()[0] == len(s["assertions"])
    assert all(a["revision"] == 1 and a["checksum"] for a in s["artifacts"])


@pytest.mark.parametrize(
    "name,index",
    [
        ("retirement", 0),
        ("replacement", 0),
        ("replacement", 1),
        ("integration", 0),
        ("reassignment", 0),
        ("consolidation", 0),
        ("outage", 0),
    ],
)
def test_six_change_classes_isolate_snapshot(estate, name, index):
    before = digest(db.load_snapshot(estate[1]["id"]))
    p = selected(estate, name, index)
    rev, _, gates = service.submit(name, 0, p)
    assert rev == 1
    assert gates["ready"] == (name == "reassignment")
    assert before == digest(db.load_snapshot(estate[1]["id"]))


def test_unknown_and_conflict_never_become_clean(estate):
    s = estate[1]
    assert s["facts"]["ownership:atlas/workbench"]["state"] == "UNKNOWN"
    values = engine(s["facts"])["requirements"]
    assert values["atlas/seasonal"]["state"] == "UNKNOWN"
    assert values["atlas/cycle-a"]["state"] == values["atlas/cycle-b"]["state"] == "UNKNOWN"
    assert "system:atlas/seasonal-adapter" not in s["facts"]
    assert s["facts"]["execution:atlas/seasonal"]["value"]["count"] == 0


def test_interface_revision_improves_results_but_stays_blocked(estate):
    first = service.evaluate(estate[1], estate[2], selected(estate, "replacement"))[0]
    second, gates, _ = service.evaluate(estate[1], estate[2], selected(estate, "replacement", 1))
    assert first["requirements"]["atlas/campaign"]["state"] == "UNSUPPORTED"
    assert second["requirements"]["atlas/campaign"]["state"] == "SUPPORTED"
    assert second["requirements"]["atlas/seasonal"]["state"] == "UNKNOWN"
    assert not gates["ready"]  # disputed owner and partial seasonal coverage survive the repair
    assert second["requirements"]["atlas/campaign"]["witness"]


def test_scope_omission_blocks_even_unchanged_alternative(estate):
    p = selected(estate, "retirement")
    p["requirements"] = ["atlas/campaign"]
    _, gates, _ = service.evaluate(estate[1], estate[2], p)
    assert "atlas/engage" in gates["omitted_requirements"]
    assert not gates["ready"]


def test_cross_company_proposed_dependency_rejected(estate):
    p = selected(estate)
    p["actions"] = [
        dict(
            op="set",
            claim=dict(
                key="dependency:boreal/report-input0",
                kind="dependency",
                subject="boreal/report-input0",
                value=dict(
                    consumer="boreal/report",
                    provider="sys:atlas/crm",
                    qualified=True,
                    optional=False,
                ),
            ),
        )
    ]
    with pytest.raises(ValueError, match="cross-company"):
        service.submit("leak", 0, p)


def test_company_scope_cannot_be_omitted(estate):
    p = selected(estate, "outage")
    p["companies"].remove("cinder")
    with pytest.raises(ValueError, match="company scope"):
        service.submit("scope", 0, p)


def test_wrong_dependency_direction_rejected(estate):
    p = selected(estate)
    p["actions"][0]["claim"]["value"]["inputs"] = ["dependency:atlas/route-input0"]
    with pytest.raises(ValueError, match="different requirement"):
        service.submit("wrong", 0, p)


def test_concurrent_revision_compare_and_swap(estate):
    p = selected(estate)

    def attempt(_):
        try:
            return service.submit("race", 0, p)[0]
        except ValueError:
            return "conflict"

    with ThreadPoolExecutor(2) as pool:
        assert sorted(map(str, pool.map(attempt, range(2)))) == ["1", "conflict"]


def test_interrupted_revision_recovery_exact_retry(estate):
    p = selected(estate)
    with pytest.raises(RuntimeError, match="interruption"):
        service.submit("interrupted", 0, p, fail=True)
    with db.connect() as c:
        assert (
            c.execute("SELECT count(*) FROM ca_proposal WHERE id='interrupted'").fetchone()[0] == 0
        )
    assert service.submit("interrupted", 0, p)[0] == 1


def test_snapshot_publication_rollback_and_recovery(estate):
    prepared, snapshot, catalog = load(ROOT / "fixtures/change-assurance", "2026-10-28T00:00:00Z")
    with pytest.raises(RuntimeError, match="interruption"):
        service.publish(prepared, snapshot, catalog, expected=estate[1]["id"], fail=True)
    assert service.view()["snapshot"]["id"] == estate[1]["id"]
    assert service.publish(prepared, snapshot, catalog, expected=estate[1]["id"])
    assert not service.publish(prepared, snapshot, catalog)
    with pytest.raises(ValueError, match="conflict"):
        service.publish(*load(ROOT / "fixtures/change-assurance", "2026-10-29T00:00:00Z"))


def decision(dsn, pid, rev=1, value="ACCEPT"):
    with psycopg.connect(dsn) as c:
        return c.execute(
            "SELECT ca_decide(%s,%s,%s,'Synthetic architecture review')", (pid, rev, value)
        ).fetchone()[0]


def test_authenticated_scoped_review_and_no_table_write(identity, estate):
    service.submit("review", 0, selected(estate))
    wrong = identity(["atlas"])
    with pytest.raises(psycopg.Error, match="scope denied"):
        decision(wrong, "review")
    right = identity(["boreal"])
    assert decision(right, "review") > 0
    assert service.view()["versions"][0]["state"] == "ACCEPTED"
    with psycopg.connect(right) as c, pytest.raises(psycopg.errors.InsufficientPrivilege):
        c.execute(
            "INSERT INTO ca_decision(proposal_id,revision,principal,decision,reason,snapshot_id) "
            "VALUES('review',1,current_user,'ACCEPT','bypass','wrong')"
        )
    with pytest.raises(psycopg.errors.UniqueViolation):
        decision(right, "review")


def test_critical_gates_block_accept_but_allow_rejection(identity, estate):
    service.submit("blocked", 0, selected(estate, "retirement"))
    principal = identity(["atlas"])
    with pytest.raises(psycopg.Error, match="gates blocked"):
        decision(principal, "blocked")
    assert decision(principal, "blocked", value="REJECT") > 0


def test_new_evidence_invalidates_decision(identity, estate):
    service.submit("review", 0, selected(estate))
    principal = identity(["boreal"])
    decision(principal, "review")
    service.publish(
        *load(ROOT / "fixtures/change-assurance", "2026-10-28T00:00:00Z"), expected=estate[1]["id"]
    )
    assert service.view()["versions"][0]["state"] == "STALE"
    with pytest.raises(psycopg.Error, match="stale"):
        decision(identity(["boreal"]), "review")


def test_new_revision_keeps_old_decision_stale(identity, estate):
    p = selected(estate)
    service.submit("review", 0, p)
    principal = identity(["boreal"])
    decision(principal, "review")
    p["title"] += " revised"
    service.submit("review", 1, p)
    assert [v["state"] for v in service.view()["versions"]] == ["STALE", "AWAITING_REVIEW"]
    with pytest.raises(psycopg.Error, match="stale"):
        decision(principal, "review")


def test_expired_evidence_denies_acceptance(identity, estate):
    service.submit("expired", 0, selected(estate))
    with db.connect() as c:
        c.execute("UPDATE ca_head SET expires_at=now()-interval '1 second'")
    assert service.view()["versions"][0]["state"] == "STALE"
    with pytest.raises(psycopg.Error, match="stale"):
        decision(identity(["boreal"]), "expired")


def test_revoked_reviewer_invalidates_prior_acceptance(identity, estate):
    service.submit("revoked", 0, selected(estate))
    principal = identity(["boreal"])
    decision(principal, "revoked")
    with db.connect() as c:
        c.execute("UPDATE ca_reviewer SET enabled=false")
    v = service.view()["versions"][0]
    assert v["state"] == "STALE" and not v["decisions"][0]["authority_current"]
    with pytest.raises(psycopg.Error, match="scope denied"):
        decision(principal, "revoked")


@pytest.mark.parametrize("table,key", [("estate_snapshot", "id"), ("ca_catalog", "snapshot_id")])
def test_historical_database_bytes_append_only(estate, table, key):
    with db.connect() as c, pytest.raises(psycopg.Error, match="append-only"):
        c.execute(f"DELETE FROM {table} WHERE {key}=%s", (estate[1]["id"],))


def test_old_and_failed_sources_are_unknown_not_truth(estate):
    a, s, catalog = estate[:3]
    stale = load(ROOT / "fixtures/change-assurance", "2027-03-01T00:00:00Z")[1]
    assert all(f["state"] == "UNKNOWN" for f in stale["facts"].values())
    meta = dict(catalog["sources"][0], status="failed", revision=2)
    artifact, claims, _ = prepare(
        (ROOT / "fixtures/change-assurance/cmdb.csv").read_text(), meta, catalog
    )
    assert not claims and artifact["revision"] == 2
    assert len(a) == 4 and s["id"]


def test_source_scope_and_authority_rejected(estate):
    catalog = estate[2]
    meta = dict(catalog["sources"][0], scope=["boreal"])
    with pytest.raises(ValueError, match="collection scope"):
        prepare((ROOT / "fixtures/change-assurance/cmdb.csv").read_text(), meta, catalog)
    body = read(ROOT / "fixtures/change-assurance/owner.json")
    import json

    with pytest.raises(ValueError, match="authority"):
        prepare(json.dumps(body), dict(catalog["sources"][2], source="registry"), catalog)


def test_database_snapshot_corruption_is_rejected(estate):
    s = deepcopy(estate[1])
    s["as_of"] = "2026-10-29T00:00:00Z"
    with pytest.raises(ValueError, match="hash mismatch"):
        service.publish(estate[0], s, estate[2])


def test_unknown_review_identity_denied(estate):
    service.submit("review", 0, selected(estate))
    # Even the trusted DB operator is not implicitly an authorized business reviewer.
    with pytest.raises(psycopg.Error, match="scope denied"):
        service.decide("review", 1, "ACCEPT", "not authorized")


def test_db_payload_is_actual_computed_result(estate):
    p = selected(estate)
    service.submit("view", 0, p)
    with db.connect() as c:
        assert (
            c.execute("SELECT payload FROM ca_version WHERE proposal_id='view'").fetchone()[0] == p
        )
    v = service.view()["versions"][0]
    assert v["assessment"] == service.evaluate(estate[1], estate[2], p)[0]
    assert isinstance(Jsonb(v["gates"]), Jsonb)
    assert os.environ["ESTATE_DATABASE_URL"]
