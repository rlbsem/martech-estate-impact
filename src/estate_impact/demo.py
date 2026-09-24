"""Reproducible fixture workflow, using the same public boundaries as other inputs."""

import json
from pathlib import Path

from . import db
from .contracts import digest
from .coverage import execution_summary, review_coverage
from .identity import index_crosswalk
from .impact import assess, scenario
from .importers import prepare
from .reporting import markdown, mermaid
from .snapshots import build


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_inputs(root):
    root = Path(root)
    fixture = root / "fixtures/synthetic-estate"
    crosswalk = read(root / "config/crosswalk.json")
    prepared = [
        prepare(
            (fixture / source["artifact"]).read_text(encoding="utf-8"),
            source,
            index_crosswalk(crosswalk),
        )
        for source in read(root / "config/sources.json")
    ]
    assertions = [c for _, claims, _ in prepared for c in claims]
    resolutions = []
    for review in read(fixture / "resolutions.json"):
        accepted = [
            c["id"]
            for c in assertions
            if c["key"] == review["key"] and c["source"] == review["accept_source"]
        ]
        resolutions.append(
            {k: v for k, v in review.items() if k != "accept_source"} | {"accept": accepted}
        )
    kwargs = dict(
        assertions=assertions,
        artifacts=[a for a, _, _ in prepared],
        manifests=read(fixture / "collection-manifests.json"),
        policy=read(root / "config/evidence-policy.json"),
        crosswalk=crosswalk,
        as_of="2026-09-24T00:00:00Z",
        quarantine=[q for _, _, qs in prepared for q in qs],
    )
    return prepared, kwargs, resolutions


def run(root, output=None):
    root = Path(root).resolve()
    output = Path(output) if output else root / "examples/generated"
    output.mkdir(parents=True, exist_ok=True)
    db.migrate(root)
    prepared, kwargs, resolutions = load_inputs(root)
    for item in prepared:
        db.store_artifact(item)
    kwargs["assertions"] = db.load_assertions([a["id"] for a, _, _ in prepared])
    unresolved = build(**kwargs)
    db.publish(unresolved)
    snapshot = build(**kwargs, resolutions=resolutions)
    db.publish(snapshot)
    snapshot = db.load_snapshot(snapshot["id"])
    initial_hash = digest(snapshot)
    facts = snapshot["facts"]
    write_json(output / "snapshot.json", snapshot)
    write_json(output / "evidence-index.json", {c["id"]: c for c in snapshot["assertions"]})
    current = {
        "systems": sum(
            f["kind"] == "system" and f["value"]["lifecycle"] == "active"
            for f in facts.values()
            if f["value"]
        ),
        "proposed_systems": sum(
            f["kind"] == "system" and f["value"]["lifecycle"] == "proposed"
            for f in facts.values()
            if f["value"]
        ),
        "integrations": sum(f["kind"] == "integration" for f in facts.values()),
        "capabilities": sum(f["kind"] == "capability" for f in facts.values()),
        "unresolved": [k for k, f in facts.items() if f["state"] == "UNKNOWN"],
    }
    seasonal = execution_summary(
        facts.get("execution:seasonal-launch"),
        review_coverage(snapshot["manifests"], "work-manager", snapshot["as_of"]),
    )
    current["seasonal_execution"] = seasonal
    current["resolution_example"] = {
        "key": resolutions[0]["key"],
        "before": unresolved["facts"][resolutions[0]["key"]]["state"],
        "after": facts[resolutions[0]["key"]]["state"],
        "record": resolutions[0],
    }
    current["capabilities"] = {
        f["subject"]: f["value"] for f in facts.values() if f["kind"] == "capability" and f["value"]
    }
    write_json(output / "estate-overview.json", current)
    (output / "estate-overview.md").write_text(
        "# Synthetic enterprise Marketing estate\n\nAll enterprise details, evidence and results are synthetic.\n\n"
        f"{current['systems']} current systems; {current['proposed_systems']} proposed systems; {current['integrations']} integration claims; {len(current['capabilities'])} business capabilities.\n\n"
        f"Snapshot: `{snapshot['id']}`\n\n"
        "## Unresolved evidence\n\n"
        + "\n".join(f"- {markdown.escape(k)}: UNKNOWN" for k in current["unresolved"])
        + "\n\n## Recorded review\n\n"
        + markdown.escape(current["resolution_example"])
        + "\n\n## Seasonal execution\n\n"
        + markdown.escape(seasonal)
        + "\n\nZero recent executions cannot establish that the annual integration is unused. The sampled period and incomplete collection remain explicit.\n\n"
        "Business accountability and technical operator are separate claims. The work-manager owner remains disputed.\n\n"
        "## Business capabilities\n\n| Capability | Accountable team |\n|---|---|\n"
        + "\n".join(
            f"| {markdown.escape(v['label'])} | {markdown.escape(v['owner'])} |"
            for v in current["capabilities"].values()
        )
        + "\n\n"
        + "[Estate data flows](estate-overview.mmd) · [Campaign workflow](campaign-workflow.mmd) · [Evidence](evidence-index.json)\n",
        encoding="utf-8",
    )
    (output / "estate-overview.mmd").write_text(
        mermaid.topology(facts, "Estate overview"), encoding="utf-8"
    )
    focus = {"work-manager", "hub", "automation", "webinar", "registration", "warehouse", "email"}
    (output / "campaign-workflow.mmd").write_text(
        mermaid.topology(facts, "Campaign data-flow context", focus), encoding="utf-8"
    )
    results = {}
    target_facts = None
    for name in ["retire-work-manager", "replace-webinar-incomplete", "replace-webinar-revised"]:
        proposal = read(root / f"fixtures/synthetic-estate/proposals/{name}.json")
        proposal["base_snapshot"] = snapshot["id"]
        result = assess(snapshot, proposal)
        db.save_assessment(result)
        results[name] = result
        write_json(output / f"{name}-assessment.json", result)
        (output / f"{name}-assessment.md").write_text(markdown.assessment(result), encoding="utf-8")
        if name == "retire-work-manager":
            (output / "retire-work-manager-impact.mmd").write_text(
                mermaid.impact(result), encoding="utf-8"
            )
        if name == "replace-webinar-revised":
            target_facts, _, _ = scenario(snapshot, proposal)
            (output / "webinar-target-state.mmd").write_text(
                mermaid.topology(
                    target_facts, "Proposed webinar target; metadata only", focus | {"new-webinar"}
                ),
                encoding="utf-8",
            )
    (output / "webinar-replacement-assessment.md").write_text(
        markdown.assessment(results["replace-webinar-incomplete"]), encoding="utf-8"
    )
    diff = [
        {
            "key": key,
            "before": facts.get(key, {}).get("value"),
            "after": target_facts.get(key, {}).get("value"),
        }
        for key in sorted(set(facts) | set(target_facts))
        if facts.get(key, {}).get("value") != target_facts.get(key, {}).get("value")
    ]
    write_json(output / "target-state-diff.json", diff)
    (output / "target-state-diff.md").write_text(
        "# Declared target-state changes\n\nSynthetic proposal; current snapshot unchanged.\n\n"
        + "\n".join(
            f"- **{markdown.escape(d['key'])}**: {markdown.escape(d['before'])} → {markdown.escape(d['after'])}"
            for d in diff
        )
        + "\n",
        encoding="utf-8",
    )
    if digest(db.load_snapshot(snapshot["id"])) != initial_hash:
        raise RuntimeError("counterfactual changed the current snapshot")
    summary = {
        "snapshot_id": snapshot["id"],
        "unresolved_snapshot_id": unresolved["id"],
        "counts": current,
        "results": {
            k: {
                "assessment_id": v["id"],
                "disposition": v["disposition"],
                "failed": v["failed_requirements"],
                "unknown": v["unknown_requirements"],
            }
            for k, v in results.items()
        },
        "snapshot_unchanged": True,
    }
    write_json(output / "demo-summary.json", summary)
    evidence_index = {c["id"]: c for c in snapshot["assertions"]}
    for result in results.values():
        for action in result["changes"]:
            evidence_index[f"proposal:{result['proposal_hash']}:{action['index']}"] = {
                "classification": "proposed future state",
                "proposal": result["proposal"]["title"],
                "action": action,
            }
    write_json(output / "evidence-index.json", evidence_index)
    for name in [
        "estate-overview",
        "campaign-workflow",
        "retire-work-manager-impact",
        "webinar-target-state",
    ]:
        diagram = (output / f"{name}.mmd").read_text(encoding="utf-8")
        (output / f"{name}-diagram.md").write_text(
            f"# {name.replace('-', ' ').title()}\n\nGenerated from snapshot `{snapshot['id']}`. Synthetic evidence.\n\n```mermaid\n{diagram}```\n",
            encoding="utf-8",
        )
    return summary
