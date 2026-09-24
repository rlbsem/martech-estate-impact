"""Issues found while reviewing the implementation against the architecture contract."""

from estate_impact.impact import assess
from estate_impact.topology import data_flows
import pytest


def test_narrow_scope_does_not_hide_new_failure(snapshot, proposal):
    p = proposal()
    p["requirements"] = ["registration"]
    result = assess(snapshot, p)
    assert result["requirements"]["registration"]["state"] == "SUPPORTED"
    assert result["out_of_scope_changes"]["follow-up"] == {
        "before": "SUPPORTED",
        "after": "UNSUPPORTED",
    }
    assert result["disposition"] == "ESTABLISHED_BLOCKERS"


def test_unresolved_flow_included_without_becoming_established(snapshot):
    flows = data_flows(snapshot["facts"])
    assert len(flows) == 40
    stale = next(f for f in flows if f["id"] == "legacy-personalization")
    assert stale["state"] == "UNKNOWN"


def test_retirement_witness_links_to_actual_proposal_action(snapshot, proposal):
    result = assess(snapshot, proposal())
    leaf_refs = [
        e
        for path in result["requirements"]["follow-up"]["witness"]["paths"]
        for step in path
        if step["node"] == "sys:work-manager"
        for e in step["evidence"]
    ]
    assert leaf_refs == [f"proposal:{result['proposal_hash']}:0"]


def test_snapshot_review_does_not_claim_full_execution_window(snapshot):
    for manifest in snapshot["manifests"]:
        if manifest["status"] == "complete":
            assert manifest["scope"] == "declared architecture"
            assert "executions" not in manifest["expected"]
    assert (
        next(a for a in snapshot["artifacts"] if a["source"] == "executions")["status"] == "partial"
    )


def test_conflicting_lifecycle_actions_rejected(snapshot, proposal):
    p = proposal()
    p["actions"].append({"op": "activate", "system": "work-manager"})
    with pytest.raises(ValueError, match="one final lifecycle"):
        assess(snapshot, p)


def test_new_unbound_dependency_is_not_silently_ignored(snapshot, proposal):
    p = proposal("replace-webinar-revised")
    p["actions"].append(
        {
            "op": "set",
            "claim": {
                "key": "dependency:registration:extra",
                "kind": "dependency",
                "subject": "registration:extra",
                "value": {
                    "consumer": "registration",
                    "provider": "sys:missing",
                    "qualified": True,
                    "optional": False,
                },
            },
        }
    )
    result = assess(snapshot, p)
    assert result["disposition"] == "UNRESOLVED_EVIDENCE"
    assert result["proposed_relationship_findings"][0]["state"] == "UNKNOWN"


def test_new_integration_unknown_endpoint_requires_resolution(snapshot, proposal):
    p = proposal("replace-webinar-revised")
    p["actions"].append(
        {
            "op": "set",
            "claim": {
                "key": "integration:new-flow",
                "kind": "integration",
                "subject": "new-flow",
                "value": {
                    "source": "webinar",
                    "destination": "absent",
                    "runtime": "hub",
                    "owner": "Central Technology",
                    "mode": "data_flow",
                },
            },
        }
    )
    result = assess(snapshot, p)
    assert result["disposition"] == "ESTABLISHED_BLOCKERS"
    assert result["proposed_relationship_findings"][0]["state"] == "UNSUPPORTED"
