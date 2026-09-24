from copy import deepcopy

import pytest

from estate_impact.compatibility import compare
from estate_impact.contracts import digest
from estate_impact.impact import assess, scenario
from estate_impact.explanations import witnesses
from estate_impact.requirements import evaluate
from conftest import fact, graph


def rehash(snapshot):
    snapshot["id"] = digest({k: v for k, v in snapshot.items() if k != "id"})


def test_retirement_failure_unaffected_and_unknown(snapshot, proposal):
    before = deepcopy(snapshot)
    result = assess(snapshot, proposal())
    assert set(result["failed_requirements"]) == {
        "campaign-creation",
        "webinar-identifiers",
        "follow-up",
        "attribution",
    }
    assert result["unknown_requirements"] == ["seasonal"]
    assert {"registration", "reporting", "website"} <= set(result["unaffected_requirements"])
    assert result["residual_references"]
    assert snapshot == before


def test_scoped_unrelated_system_invariant(snapshot, proposal):
    import json

    p = proposal()
    baseline = assess(snapshot, p)
    snapshot["facts"]["system:unrelated"] = fact(
        "system", "unrelated", dict(label="Independent", lifecycle="active")
    )
    rehash(snapshot)
    p["base_snapshot"] = snapshot["id"]
    changed = assess(snapshot, p)
    # Rebinding the proposal to a new snapshot changes its content-addressed evidence IDs,
    # while every requirement state, witness topology and source assertion remains identical.
    baseline_semantics = json.dumps(baseline["requirements"], sort_keys=True).replace(
        baseline["proposal_hash"], "PROPOSAL"
    )
    changed_semantics = json.dumps(changed["requirements"], sort_keys=True).replace(
        changed["proposal_hash"], "PROPOSAL"
    )
    assert baseline_semantics == changed_semantics
    assert baseline["disposition"] == changed["disposition"]


def test_replacement_isolated_and_revised_within_scope(snapshot, proposal):
    before = digest(snapshot)
    incomplete = assess(snapshot, proposal("replace-webinar-incomplete"))
    revised = assess(snapshot, proposal("replace-webinar-revised"))
    assert incomplete["requirements"]["registration"]["state"] == "SUPPORTED"
    assert incomplete["requirements"]["follow-up"]["state"] == "UNSUPPORTED"
    assert revised["disposition"] == "NO_IDENTIFIED_BLOCKERS_WITHIN_REVIEWED_SCOPE"
    assert not revised["residual_references"]
    assert revised["sequence"]["missing_acceptance"]
    assert digest(snapshot) == before


@pytest.mark.parametrize("dimension", ["events", "fields", "keys"])
def test_interface_dimensions_independently_required(dimension):
    required = {"events": ["completed"], "fields": ["id"], "keys": ["campaign_id"]}
    offered = deepcopy(required)
    offered[dimension] = []
    result = compare(required, offered)
    assert result["state"] == "UNSUPPORTED"
    assert result["missing"][dimension] == required[dimension]
    assert compare(required, None)["state"] == "UNKNOWN"


def test_incomplete_coverage_prevents_clean_conclusion(snapshot, proposal):
    p = proposal("replace-webinar-revised")
    next(m for m in snapshot["manifests"] if "webinar" in m["subjects"])["status"] = "partial"
    rehash(snapshot)
    p["base_snapshot"] = snapshot["id"]
    assert assess(snapshot, p)["disposition"] == "UNRESOLVED_EVIDENCE"


def test_witness_chain_and_source_references(snapshot, proposal):
    result = assess(snapshot, proposal())
    paths = result["requirements"]["follow-up"]["witness"]["paths"]
    assert any(
        [p["node"] for p in path if p["node"].startswith("req:")]
        == ["req:follow-up", "req:webinar-identifiers", "req:campaign-creation"]
        for path in paths
    )
    valid = {c["id"] for c in snapshot["assertions"]}
    for path in paths:
        for step in path:
            assert all(e in valid or e.startswith("proposal:") for e in step["evidence"])
    unresolved = result["requirements"]["seasonal"]["witness"]["paths"]
    assert any(
        step.get("reason") == "dependency unresolved" for path in unresolved for step in path
    )


def test_witness_limits_and_cycles():
    evaluation = evaluate(graph({"a": ("ALL", ["req:b"]), "b": ("ALL", ["req:a"])}, {}))
    result = witnesses("a", evaluation)
    assert result["paths"][0][-1]["reason"] == "circular support"
    assert witnesses("a", evaluation, max_depth=1)["truncated"]


def test_relationship_removal_does_not_turn_missing_input_into_support(snapshot, proposal):
    p = proposal("replace-webinar-revised")
    p["actions"].append(dict(op="remove", key="dependency:registration:0"))
    result = assess(snapshot, p)
    assert result["requirements"]["registration"]["state"] == "UNKNOWN"


def test_foreign_dependency_rebinding_rejected(snapshot, proposal):
    p = proposal()
    dep = deepcopy(snapshot["facts"]["dependency:registration:0"])
    dep["value"]["consumer"] = "follow-up"
    p["actions"].append(
        dict(
            op="set",
            claim=dict(
                key="dependency:registration:0",
                kind=dep["kind"],
                subject=dep["subject"],
                value=dep["value"],
            ),
        )
    )
    with pytest.raises(ValueError, match="different requirement"):
        scenario(snapshot, p)


def test_renamed_topology_derived_not_hardcoded(snapshot, proposal):
    import json

    # Rename all structured identities consistently, including scope and artifacts.
    p = proposal()
    renamed = json.loads(json.dumps(snapshot).replace("work-manager", "brief-source-zeta"))
    rehash(renamed)
    p = json.loads(json.dumps(p).replace("work-manager", "brief-source-zeta"))
    p["base_snapshot"] = renamed["id"]
    result = assess(renamed, p)
    assert result["requirements"]["follow-up"]["state"] == "UNSUPPORTED"
    assert any(
        "brief-source-zeta" in step["node"]
        for path in result["requirements"]["follow-up"]["witness"]["paths"]
        for step in path
    )


def test_wrong_snapshot_and_tampering_rejected(snapshot, proposal):
    p = proposal()
    p["base_snapshot"] = "other"
    with pytest.raises(ValueError, match="base snapshot"):
        assess(snapshot, p)
    snapshot["as_of"] = "2020-01-01T00:00:00Z"
    with pytest.raises(ValueError, match="hash mismatch"):
        assess(snapshot, proposal())
