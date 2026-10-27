from copy import deepcopy
import importlib.util
import json
import subprocess
import sys

import pytest

from estate_impact import db
from estate_impact.impact import scenario
from estate_impact.requirements import evaluate
from estate_change import service
from estate_change.demo import proposals
from estate_change.evidence import load
from conftest import ROOT

spec = importlib.util.spec_from_file_location("change_oracle", ROOT / "scripts/change_oracle.py")
oracle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oracle)


def test_typed_scoped_proposals_against_independent_recursive_oracle(estate):
    snapshots = [estate[1]["facts"]]
    snapshots += [
        scenario(estate[1], p)[0] for versions in proposals(estate[1]).values() for p in versions
    ]
    checked = 0
    for facts in snapshots:
        actual = {k: v["state"] for k, v in evaluate(facts)["requirements"].items()}
        assert actual == oracle.reference(facts)
        checked += len(actual)
    assert checked == 64


@pytest.mark.parametrize("boundary", ["proposal", "snapshot"])
def test_actual_process_death_before_commit_recovers(estate, tmp_path, boundary):
    p = proposals(estate[1])["reassignment"][0]
    file = tmp_path / "proposal.json"
    file.write_text(json.dumps(p))
    if boundary == "proposal":
        code = (
            "import json;from estate_change.service import submit;"
            f"submit('killed',0,json.load(open({str(file)!r})),fail='process')"
        )
    else:
        code = (
            "from pathlib import Path;from estate_change.evidence import load;"
            "from estate_change.service import publish;"
            f"publish(*load(Path({str(ROOT / 'fixtures/change-assurance')!r}),"
            f"'2026-10-28T00:00:00Z'),expected={estate[1]['id']!r},fail='process')"
        )
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, timeout=30)
    assert result.returncode == 77
    assert service.view()["snapshot"]["id"] == estate[1]["id"]
    if boundary == "proposal":
        with db.connect() as c:
            assert (
                c.execute("SELECT count(*) FROM ca_proposal WHERE id='killed'").fetchone()[0] == 0
            )
        assert service.submit("killed", 0, p)[0] == 1
    else:
        assert service.publish(
            *load(ROOT / "fixtures/change-assurance", "2026-10-28T00:00:00Z"),
            expected=estate[1]["id"],
        )


def test_rewire_requires_endpoint_system_scope(estate):
    p = deepcopy(proposals(estate[1])["integration"][0])
    p["systems"] = ["atlas/crm"]
    p["actions"] = [
        dict(op="rewire", integration="atlas/sync", endpoints={"runtime": "parent/hub"})
    ]
    p["companies"] = ["atlas"]
    # Endpoints must be included for owner/coverage checks even if modeled outcomes do not change.
    _, gates, _ = service.evaluate(estate[1], estate[2], p)
    assert gates["omitted_systems"] == ["parent/hub"] and not gates["ready"]


def test_activity_cycle_prevents_ready_reassignment(estate):
    p = deepcopy(proposals(estate[1])["reassignment"][0])
    p["activities"] = [
        dict(id="a", prerequisites=["b"], requires_evidence=[], completed=False),
        dict(id="b", prerequisites=["a"], requires_evidence=[], completed=False),
    ]
    result, gates, _ = service.evaluate(estate[1], estate[2], p)
    assert result["sequence"]["cycle_members"] == ["a", "b"]
    assert not gates["ready"]


def test_missing_acceptance_evidence_prevents_ready(estate):
    p = deepcopy(proposals(estate[1])["reassignment"][0])
    p["activities"] = [
        dict(id="review", prerequisites=[], requires_evidence=["not-present"], completed=False)
    ]
    assert not service.evaluate(estate[1], estate[2], p)[1]["ready"]


def test_unknown_source_and_duplicate_claim_fail_closed(estate):
    from estate_change.evidence import prepare

    catalog = estate[2]
    meta = dict(catalog["sources"][2], source="untrusted")
    text = (ROOT / "fixtures/change-assurance/owner.json").read_text()
    with pytest.raises(ValueError, match="unsupported source"):
        prepare(text, meta, catalog)
    body = json.loads(text)
    body["records"].append(body["records"][0])
    with pytest.raises(ValueError, match="duplicate"):
        prepare(json.dumps(body), catalog["sources"][2], catalog)


def test_revision_history_database_is_append_only(estate):
    service.submit("history", 0, proposals(estate[1])["reassignment"][0])
    import psycopg

    with db.connect() as c, pytest.raises(psycopg.Error, match="append-only"):
        c.execute("UPDATE ca_version SET revision=9 WHERE proposal_id='history'")
