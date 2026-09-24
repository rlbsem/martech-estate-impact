from copy import deepcopy

import pytest

from estate_impact.assertions import reconcile
from estate_impact.identity import index_crosswalk, resolve, IdentityError
from estate_impact.snapshots import build


def test_aliases_and_similar_distinct_systems(snapshot):
    index = index_crosswalk(snapshot["crosswalk"])
    assert (
        resolve("inventory", "campaign-desk", index)
        == resolve("inventory", "work-hub-legacy", index)
        == "work-manager"
    )
    assert resolve("inventory", "content-review", index) != resolve(
        "inventory", "work-manager", index
    )
    with pytest.raises(IdentityError):
        resolve("inventory", "campaign-work", index)
    with pytest.raises(IdentityError):
        resolve("inventory", "Campaign Work Managr", index)


def test_crosswalk_collision_rejected():
    row = dict(source="a", external="b", targets=["c"])
    with pytest.raises(IdentityError):
        index_crosswalk([row, dict(row, targets=["d"])])


def test_resolution_retains_rejected_assertion(inputs):
    _, kwargs, resolutions = inputs
    before, after = build(**kwargs), build(**kwargs, resolutions=resolutions)
    key = "dependency:product-insight:1"
    assert before["facts"][key]["state"] == "UNKNOWN"
    assert after["facts"][key]["state"] == "SUPPORTED"
    assert set(after["facts"][key]["dispositions"].values()) == {"accepted", "rejected"}
    assert len(after["facts"][key]["evidence"]) == 2
    assert before["id"] != after["id"]


def test_scoped_authority_stale_and_conflict(snapshot):
    assert snapshot["facts"]["ownership:work-manager"]["state"] == "UNKNOWN"
    assert snapshot["facts"]["dependency:seasonal:0"]["state"] == "UNKNOWN"
    stale = snapshot["facts"]["integration:legacy-personalization"]
    assert stale["state"] == "UNKNOWN" and set(stale["dispositions"].values()) == {"unresolved"}
    assert (
        snapshot["policy"]["types"]["ownership"]["sources"]
        != snapshot["policy"]["types"]["integration"]["sources"]
    )


def test_resolution_cannot_make_stale_evidence_current(snapshot):
    key = "integration:legacy-personalization"
    decision = dict(
        key=key, accept=snapshot["facts"][key]["evidence"], reviewer="Reviewer", reason="Trust it"
    )
    with pytest.raises(ValueError, match="stale"):
        reconcile(snapshot["assertions"], snapshot["policy"], snapshot["as_of"], [decision])


def test_import_order_invariance(inputs):
    _, kwargs, resolutions = inputs
    reversed_inputs = deepcopy(kwargs)
    reversed_inputs["assertions"].reverse()
    reversed_inputs["artifacts"].reverse()
    assert build(**kwargs, resolutions=resolutions) == build(
        **reversed_inputs, resolutions=resolutions
    )


def test_removing_support_cannot_resolve_disputed_evidence(snapshot):
    claims = [c for c in snapshot["assertions"] if c["key"] == "system:crm"]
    current = reconcile(claims, snapshot["policy"], snapshot["as_of"])
    empty = reconcile([], snapshot["policy"], snapshot["as_of"])
    assert current["system:crm"]["state"] == "SUPPORTED" and "system:crm" not in empty
