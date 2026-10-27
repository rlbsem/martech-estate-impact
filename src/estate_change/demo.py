"""Six change classes and preserved revision history, computed by the original engine."""

from copy import deepcopy

from estate_impact import db

from . import service
from .evidence import load


def proposals(snapshot):
    def proposal(title, kind, systems, requirements, actions, companies):
        return dict(
            format="estate-proposal/v1",
            base_snapshot=snapshot["id"],
            title=title,
            change_kind=kind,
            systems=systems,
            requirements=requirements,
            companies=companies,
            actions=actions,
            activities=[],
            acceptance_evidence=[],
        )

    atlas = ["atlas/campaign", "atlas/engage", "atlas/seasonal"]
    retire = proposal(
        "Retire legacy campaign workbench",
        "retirement",
        ["atlas/workbench"],
        atlas,
        [dict(op="retire", system="atlas/workbench")],
        ["atlas"],
    )
    replacement = deepcopy(retire)
    replacement.update(
        title="Replace campaign workbench",
        change_kind="replacement",
        systems=["atlas/workbench", "atlas/modern"],
    )
    replacement["actions"] += [dict(op="activate", system="atlas/modern")]
    for key, f in snapshot["facts"].items():
        if (
            f["kind"] == "dependency"
            and f["value"]
            and f["value"]["provider"] == "sys:atlas/workbench"
        ):
            replacement["actions"].append(
                dict(
                    op="set",
                    claim=dict(
                        key=key,
                        kind=f["kind"],
                        subject=f["subject"],
                        value=dict(f["value"], provider="sys:atlas/modern"),
                    ),
                )
            )
    revised = deepcopy(replacement)
    revised["actions"].append(
        dict(
            op="set",
            claim=dict(
                key="interface:atlas/modern",
                kind="interface",
                subject="atlas/modern",
                value=snapshot["facts"]["interface:atlas/workbench"]["value"],
            ),
        )
    )
    integration = proposal(
        "Remove Atlas shared-fabric route",
        "integration-removal",
        ["parent/hub", "atlas/crm"],
        ["atlas/route", *atlas],
        [dict(op="remove", key="integration:atlas/sync")],
        ["atlas", "parent"],
    )
    fact = snapshot["facts"]["requirement:boreal/report"]
    reassign = proposal(
        "Assign Boreal reporting to operations",
        "capability-reassignment",
        ["boreal/crm"],
        ["boreal/report"],
        [
            dict(
                op="set",
                claim=dict(
                    key="requirement:boreal/report",
                    kind="requirement",
                    subject="boreal/report",
                    value=dict(fact["value"], capability="boreal/operations"),
                ),
            )
        ],
        ["boreal"],
    )
    consolidation = proposal(
        "Consolidate local CRMs onto the parent platform",
        "consolidation",
        ["atlas/crm", "boreal/crm", "parent/hub"],
        ["atlas/route", *atlas, "boreal/report", "cinder/report"],
        [dict(op="retire", system="atlas/crm"), dict(op="retire", system="boreal/crm")],
        ["atlas", "boreal", "cinder", "parent"],
    )
    outage = proposal(
        "Model a shared fabric outage",
        "temporary-outage",
        ["parent/hub"],
        ["atlas/route", *atlas, "boreal/report", "cinder/report"],
        [dict(op="retire", system="parent/hub")],
        ["atlas", "boreal", "cinder", "parent"],
    )
    return dict(
        retirement=[retire],
        replacement=[replacement, revised],
        integration=[integration],
        reassignment=[reassign],
        consolidation=[consolidation],
        outage=[outage],
    )


def execute(root):
    service.migrate(root)
    prepared, snapshot, catalog = load(root / "fixtures/change-assurance")
    service.publish(prepared, snapshot, catalog)
    for pid, versions in proposals(snapshot).items():
        for i, proposal in enumerate(versions):
            service.submit(pid, i, proposal)
    for f in snapshot["facts"].values():
        if f["kind"] != "system" or not f["value"] or f["value"]["lifecycle"] != "active":
            continue
        p = dict(
            format="estate-proposal/v1",
            base_snapshot=snapshot["id"],
            title="Retirement impact: " + f["value"]["label"],
            change_kind="retirement",
            systems=[f["subject"]],
            companies=sorted(catalog["companies"]),
            requirements=sorted(
                x["subject"] for x in snapshot["facts"].values() if x["kind"] == "requirement"
            ),
            actions=[dict(op="retire", system=f["subject"])],
            activities=[],
            acceptance_evidence=[],
        )
        changed, _ = service.affected(snapshot, p)
        p["companies"] = sorted(
            {x.split("/", 1)[0] for x in changed | set(p["systems"]) | set(p["requirements"])}
        )
        service.submit("explore:" + f["subject"], 0, p)
    with db.connect() as c:
        return c.execute("SELECT count(*) FROM ca_version").fetchone()[0]
