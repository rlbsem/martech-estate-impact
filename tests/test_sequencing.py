from estate_impact.sequencing import sequence


def activity(identity, prerequisites=(), evidence=(), completed=False):
    return dict(
        id=identity,
        prerequisites=list(prerequisites),
        requires_evidence=list(evidence),
        completed=completed,
    )


def test_valid_order_and_acceptance_gate():
    activities = [
        activity("handoff", ["accept"], completed=True),
        activity("accept", ["validate"], ["runtime-proof"], True),
        activity("validate", completed=True),
    ]
    blocked = sequence(activities, [])
    assert blocked["order"] == ["validate", "accept", "handoff"]
    assert blocked["invalid_completed"] == ["accept", "handoff"]
    assert blocked["completed"] == ["validate"]
    ready = sequence(activities, ["runtime-proof"])
    assert len(ready["completed"]) == 3
    assert not ready["missing_acceptance"]


def test_cycles_distinguished_from_blocked_descendants():
    result = sequence(
        [activity("a", ["b"]), activity("b", ["a"]), activity("c", ["b"]), activity("independent")],
        [],
    )
    assert result["cycle_members"] == ["a", "b"]
    assert result["blocked"] == ["a", "b", "c"]
    assert result["order"] == result["ready_now"] == ["independent"]


def test_missing_prerequisite_is_not_a_cycle():
    result = sequence([activity("a", ["absent"])], [])
    assert result["missing_prerequisites"] == {"a": ["absent"]}
    assert not result["cycle_members"] and not result["ready_now"]
