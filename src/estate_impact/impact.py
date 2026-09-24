"""Isolated counterfactuals with declared scope and retained residual references."""

from copy import deepcopy

from . import __version__
from .contracts import digest, implementation_hash, validate_claim
from .coverage import review_coverage
from .explanations import witnesses
from .requirements import evaluate
from .sequencing import sequence
from .snapshots import check_identity
from .topology import data_flows, reachable


def scenario(snapshot, proposal):
    check_identity(snapshot)
    if proposal.get("format") != "estate-proposal/v1":
        raise ValueError("unsupported proposal format")
    if proposal.get("base_snapshot") != snapshot["id"]:
        raise ValueError("proposal must bind the exact base snapshot")
    facts = deepcopy(snapshot["facts"])
    changes, retired = [], set()
    lifecycle_actions = set()
    proposal_id = digest(proposal)

    def set_fact(key, value, action_no):
        fact = facts[key]
        validate_claim(
            {
                "key": key,
                "kind": fact["kind"],
                "subject": fact["subject"],
                "value": value,
                "location": "proposal",
            }
        )
        facts[key] = dict(
            fact,
            value=value,
            state="SUPPORTED",
            proposed=True,
            evidence=[f"proposal:{proposal_id}:{action_no}"],
            base_evidence=fact["evidence"],
        )

    for i, action in enumerate(proposal["actions"]):
        op = action["op"]
        if op in {"retire", "activate"}:
            if action["system"] in lifecycle_actions:
                raise ValueError("one final lifecycle declaration per system is required")
            lifecycle_actions.add(action["system"])
        if op == "retire":
            key = f"system:{action['system']}"
            if key not in facts or not facts[key]["value"]:
                raise ValueError("retirement requires a resolved system")
            retired.add(action["system"])
            set_fact(key, dict(facts[key]["value"], lifecycle="retired"), i)
        elif op == "activate":
            key = f"system:{action['system']}"
            if key not in facts or not facts[key]["value"]:
                raise ValueError("activation requires a resolved system")
            set_fact(key, dict(facts[key]["value"], lifecycle="active"), i)
        elif op == "rewire":
            key = f"integration:{action['integration']}"
            if key not in facts or facts[key]["state"] != "SUPPORTED":
                raise ValueError("rewire requires resolved integration")
            value = dict(facts[key]["value"])
            for field, target in action["endpoints"].items():
                if (
                    field not in {"source", "destination", "runtime"}
                    or f"system:{target}" not in facts
                ):
                    raise ValueError("invalid rewire endpoint")
                value[field] = target
            set_fact(key, value, i)
        elif op == "set":
            claim = action["claim"]
            validate_claim(dict(claim, location="proposal"))
            if claim["kind"] not in {"dependency", "requirement", "interface", "integration"}:
                raise ValueError("proposal cannot rewrite source identity or ownership")
            key = claim["key"]
            if key not in facts:
                facts[key] = dict(claim, evidence=[], dispositions={}, resolution=None)
            if (facts[key]["kind"], facts[key]["subject"]) != (claim["kind"], claim["subject"]):
                raise ValueError("proposal fact identity mismatch")
            set_fact(key, deepcopy(claim["value"]), i)
        elif op == "remove":
            key = action["key"]
            if key not in facts or facts[key]["kind"] not in {"dependency", "integration"}:
                raise ValueError("only declared relationships can be removed")
            del facts[key]
        else:
            raise ValueError(f"unknown action: {op}")
        changes.append({"index": i, **deepcopy(action)})
    # Missing references are evidence gaps, but foreign consumer bindings are invalid input.
    for fact in facts.values():
        if fact["kind"] == "requirement" and fact["value"]:
            for key in fact["value"]["inputs"]:
                edge = facts.get(key)
                if (
                    edge
                    and edge["value"]
                    and (
                        edge["kind"] != "dependency" or edge["value"]["consumer"] != fact["subject"]
                    )
                ):
                    raise ValueError("dependency belongs to a different requirement")
    return facts, changes, retired


def assess(snapshot, proposal):
    facts, changes, retired = scenario(snapshot, proposal)
    current, target = evaluate(snapshot["facts"]), evaluate(facts)
    scope = sorted(set(proposal["requirements"]))
    if not scope or set(scope) - target["requirements"].keys():
        raise ValueError("nonempty, known requirement scope required")
    systems = set(proposal["systems"])
    action_systems = {a["system"] for a in proposal["actions"] if "system" in a}
    if not action_systems <= systems:
        raise ValueError("changed systems missing from reviewed scope")
    flows = data_flows(facts)
    residual = []
    for key, fact in facts.items():
        values = [fact["value"]] if fact["value"] else fact["candidates"]
        for value in values:
            refs = (
                {value.get(k) for k in ("source", "destination", "runtime")}
                if fact["kind"] == "integration"
                else {value.get("provider", "").removeprefix("sys:")}
                if fact["kind"] == "dependency"
                else set()
            )
            if refs & retired:
                residual.append(
                    {
                        "key": key,
                        "retired_systems": sorted(refs & retired),
                        "state": fact["state"],
                        "evidence": fact["evidence"],
                    }
                )
    coverage = {
        system: review_coverage(snapshot["manifests"], system, snapshot["as_of"])
        for system in sorted(systems)
    }
    residual = list(
        {(r["key"], tuple(r["retired_systems"]), r["state"]): r for r in residual}.values()
    )
    proposed_relationship_findings = []
    for key, fact in facts.items():
        if not fact.get("proposed"):
            continue
        if fact["kind"] == "integration":
            state = target["states"].get(f"int:{fact['subject']}", "UNKNOWN")
            if state != "SUPPORTED":
                proposed_relationship_findings.append(
                    {
                        "key": key,
                        "state": state,
                        "reason": "proposed integration has unavailable or unestablished endpoints/runtime",
                    }
                )
        elif fact["kind"] == "dependency":
            consumer = target["requirements"].get(fact["value"]["consumer"])
            if consumer is None or key not in consumer["inputs"]:
                proposed_relationship_findings.append(
                    {
                        "key": key,
                        "state": "UNKNOWN",
                        "reason": "proposed dependency is not bound to its consumer group",
                    }
                )
    results = {
        key: {
            **target["requirements"][key],
            "before": current["requirements"].get(key, {}).get("state", "UNKNOWN"),
            "witness": witnesses(key, target),
        }
        for key in scope
    }
    failed = [key for key, result in results.items() if result["state"] == "UNSUPPORTED"]
    unknown = [key for key, result in results.items() if result["state"] == "UNKNOWN"]
    outside_changes = {
        key: {
            "before": current["requirements"].get(key, {}).get("state", "UNKNOWN"),
            "after": value["state"],
        }
        for key, value in target["requirements"].items()
        if key not in scope
        and value["state"] != current["requirements"].get(key, {}).get("state", "UNKNOWN")
    }
    unresolved_facts = sorted(key for key, fact in facts.items() if fact["state"] == "UNKNOWN")
    sequence_result = sequence(
        proposal.get("activities", []), proposal.get("acceptance_evidence", [])
    )
    blockers = bool(
        failed
        or any(r["state"] == "SUPPORTED" for r in residual)
        or any(c["after"] == "UNSUPPORTED" for c in outside_changes.values())
        or any(c["state"] == "UNSUPPORTED" for c in proposed_relationship_findings)
    )
    gaps = bool(
        unknown
        or any(v["state"] == "UNKNOWN" for v in coverage.values())
        or any(r["state"] == "UNKNOWN" for r in residual)
        or snapshot["quarantine"]
        or any(c["after"] == "UNKNOWN" for c in outside_changes.values())
        or any(c["state"] == "UNKNOWN" for c in proposed_relationship_findings)
    )
    disposition = (
        "ESTABLISHED_BLOCKERS"
        if blockers
        else "UNRESOLVED_EVIDENCE"
        if gaps
        else "NO_IDENTIFIED_BLOCKERS_WITHIN_REVIEWED_SCOPE"
    )
    result = {
        "format": "estate-assessment/v1",
        "snapshot_id": snapshot["id"],
        "proposal_hash": digest(proposal),
        "proposal": proposal,
        "policy_hash": snapshot["policy_hash"],
        "implementation": __version__,
        "synthetic": True,
        "disposition": disposition,
        "implementation_hash": implementation_hash(),
        "requirements": results,
        "node_labels": {
            f"{prefix}:{f['subject']}": (
                f["value"].get("label") or f["value"].get("purpose") or f["subject"]
            )
            for f in facts.values()
            if f["value"]
            for kind, prefix in [("system", "sys"), ("requirement", "req"), ("integration", "int")]
            if f["kind"] == kind
        },
        "failed_requirements": failed,
        "unknown_requirements": unknown,
        "unaffected_requirements": [
            key for key, r in results.items() if r["state"] == r["before"] == "SUPPORTED"
        ],
        "residual_references": sorted(residual, key=lambda x: (x["key"], x["retired_systems"])),
        "coverage": coverage,
        "unresolved_estate_facts": unresolved_facts,
        "out_of_scope_changes": outside_changes,
        "proposed_relationship_findings": proposed_relationship_findings,
        "sequence": sequence_result,
        "changes": changes,
        "candidate_reachability": {system: reachable(flows, system) for system in sorted(systems)},
        "claim_boundary": "Modeled consequence of declared architecture. Metadata compatibility is not operational verification; this result does not authorize cutover.",
    }
    result["id"] = digest(result)
    return result
