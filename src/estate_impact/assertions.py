"""Assertion-type authority and recorded decisions; no global source ranking."""

from collections import defaultdict

from .contracts import canonical, timestamp


def reconcile(assertions, policy, as_of, resolutions=()):
    now = timestamp(as_of)
    grouped = defaultdict(list)
    for claim in assertions:
        grouped[claim["key"]].append(claim)
    decisions = {}
    for decision in resolutions:
        if (
            decision["key"] in decisions
            or not decision.get("reviewer")
            or not decision.get("reason")
        ):
            raise ValueError("invalid/duplicate resolution")
        decisions[decision["key"]] = decision
    if set(decisions) - set(grouped):
        raise ValueError("resolution references unknown fact")
    facts = {}
    for key, candidates in sorted(grouped.items()):
        candidates.sort(key=lambda c: c["id"])
        kind = candidates[0]["kind"]
        if len({(c["kind"], c["subject"]) for c in candidates}) != 1:
            raise ValueError("fact key reused across identities")
        rule = policy["types"][kind]
        dispositions, eligible = {}, []
        for c in candidates:
            age = (now - timestamp(c["collected_at"])).total_seconds() / 86400
            valid = c["source"] in rule["sources"] and 0 <= age <= rule["max_age_days"]
            valid = valid and c["collection_status"] != "failed"
            dispositions[c["id"]] = "unresolved" if not valid else "disputed"
            if valid:
                eligible.append(c)
        decision = decisions.get(key)
        if decision:
            selected = set(decision["accept"])
            if not selected or not selected <= {c["id"] for c in eligible}:
                raise ValueError(
                    "resolution cannot accept absent, stale, or inadmissible assertions"
                )
            chosen = [c for c in eligible if c["id"] in selected]
            if len({canonical(c["value"]) for c in chosen}) != 1:
                raise ValueError("resolution accepts contradictory values")
            for c in candidates:
                dispositions[c["id"]] = "accepted" if c in chosen else "rejected"
        else:
            chosen = eligible if len({canonical(c["value"]) for c in eligible}) == 1 else []
            for c in chosen:
                dispositions[c["id"]] = "accepted"
        facts[key] = {
            "kind": kind,
            "subject": candidates[0]["subject"],
            "state": "SUPPORTED" if chosen else "UNKNOWN",
            "value": chosen[0]["value"] if chosen else None,
            "candidates": [c["value"] for c in candidates],
            "evidence": [c["id"] for c in candidates],
            "dispositions": dispositions,
            "resolution": decision,
        }
    return facts
