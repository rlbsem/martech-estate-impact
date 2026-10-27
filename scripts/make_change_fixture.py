"""Explicit synthetic multi-company inputs; no sampled enterprise or vendor observations."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "fixtures/change-assurance"
NOW = "2026-10-27T00:00:00Z"


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    FOLDER.mkdir(exist_ok=True)
    identities, cross, records = set(), [], {"registry": [], "owner": [], "execution": []}

    def add(source, kind, subject, value):
        identities.add(subject)
        records[source].append(
            dict(
                kind=kind,
                subject=subject,
                value=value,
                location=f"record:{len(records[source]) + 1}",
            )
        )
        refs = []
        if kind == "integration":
            refs = [value[k] for k in ["source", "destination", "runtime"]]
        if kind == "dependency":
            refs = [value["consumer"], value["provider"].split(":", 1)[1]]
        for ref in refs:
            identities.add(ref)
            if subject.split("/")[0] != ref.split("/")[0]:
                cross.append([subject, ref])

    systems = [
        ("parent", "hub", "Shared integration fabric", "active", "Parent Platform"),
        ("atlas", "crm", "Atlas CRM", "active", "Atlas Revenue Operations"),
        ("boreal", "crm", "Boreal CRM", "active", "Boreal Operations"),
        ("cinder", "crm", "Cinder CRM", "active", "Cinder Operations"),
        ("atlas", "workbench", "Legacy campaign workbench", "active", "Atlas Marketing"),
        ("atlas", "modern", "Proposed campaign platform", "proposed", "Atlas Marketing"),
        ("cinder", "spare", "Cold standby exporter", "active", "Cinder Operations"),
    ]
    with (FOLDER / "cmdb.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["company", "local_id", "label", "lifecycle", "owner"])
        writer.writerows(systems)
    for co, local, *_ in systems:
        identities.add(co + "/" + local)
    contract = dict(
        events=["campaign.ready"], fields=["account_id", "permission"], keys=["campaign_id"]
    )
    add("registry", "interface", "atlas/workbench", contract)
    add("registry", "interface", "atlas/modern", dict(contract, fields=["account_id"]))
    for co in ["atlas", "boreal", "cinder"]:
        add(
            "registry",
            "integration",
            co + "/sync",
            dict(
                source=co + "/crm",
                destination="parent/hub",
                runtime="parent/hub",
                owner=co + " Operations",
                mode="data_flow",
            ),
        )
        add(
            "owner",
            "capability",
            co + "/revenue",
            dict(label="Revenue operations", owner=co + " Revenue", criticality="critical"),
        )
        add(
            "owner",
            "capability",
            co + "/operations",
            dict(label="Operational reporting", owner=co + " Operations", criticality="important"),
        )

    def req(subject, mode, providers):
        inputs = []
        for i, provider in enumerate(providers):
            edge = subject + f"-input{i}"
            inputs.append("dependency:" + edge)
            v = dict(consumer=subject, provider=provider, qualified=True, optional=False)
            if provider == "sys:atlas/workbench":
                v["contract"] = contract
            add("owner", "dependency", edge, v)
        add(
            "owner",
            "requirement",
            subject,
            dict(
                label={
                    "route": "Route qualified accounts",
                    "campaign": "Release governed campaigns",
                    "engage": "Keep an alternate engagement path",
                    "seasonal": "Annual partner launch",
                    "cycle-a": "Unanchored approval cycle A",
                    "cycle-b": "Unanchored approval cycle B",
                    "report": "Publish operating reports",
                }[subject.split("/")[1]],
                capability=subject.split("/")[0] + "/revenue",
                mode=mode,
                inputs=inputs,
            ),
        )

    req("atlas/route", "ALL", ["sys:atlas/crm", "int:atlas/sync"])
    req("atlas/campaign", "ALL", ["req:atlas/route", "sys:atlas/workbench"])
    req("atlas/engage", "ANY", ["req:atlas/route", "sys:atlas/workbench"])
    req("atlas/seasonal", "ALL", ["sys:atlas/workbench", "sys:atlas/seasonal-adapter"])
    req("atlas/cycle-a", "ALL", ["req:atlas/cycle-b"])
    req("atlas/cycle-b", "ALL", ["req:atlas/cycle-a"])
    req("boreal/report", "ALL", ["sys:boreal/crm", "int:boreal/sync"])
    req("cinder/report", "ALL", ["sys:cinder/crm", "int:cinder/sync"])
    add("owner", "ownership", "atlas/workbench", dict(team="Atlas Applications"))
    add(
        "execution",
        "execution",
        "atlas/seasonal",
        dict(count=0, start="2026-10-01T00:00:00Z", end="2026-10-27T00:00:00Z"),
    )
    for source, rs in records.items():
        save(FOLDER / f"{source}.json", dict(format="change-source/v1", records=rs))
    companies = dict(
        parent="Northstar Group",
        atlas="Atlas Industrial",
        boreal="Boreal Services",
        cinder="Cinder Software",
    )
    sources = [
        dict(
            source=s,
            artifact="cmdb.csv" if s == "cmdb" else f"{s}.json",
            revision=1,
            collected_at=NOW,
            scope=list(companies),
            status="partial" if s == "execution" else "complete",
        )
        for s in ["cmdb", "registry", "owner", "execution"]
    ]
    coverage = [
        dict(
            id="coverage:" + co + "/" + local,
            subjects=[co + "/" + local],
            reviewer="Synthetic architecture steward",
            reviewed_at=NOW,
            max_age_days=30,
            status="partial" if local == "workbench" else "complete",
            expected=["cmdb", "registry", "owner", "execution"],
            observed=["cmdb", "registry", "owner", "execution"],
            expected_start="2026-01-01T00:00:00Z" if local == "workbench" else NOW,
            observed_start="2026-10-01T00:00:00Z" if local == "workbench" else NOW,
            expected_end=NOW,
            observed_end=NOW,
            exclusions=["Annual launch not observed"] if local == "workbench" else [],
        )
        for co, local, *_ in systems
    ]
    save(
        FOLDER / "catalog.json",
        dict(
            format="change-catalog/v1",
            as_of=NOW,
            synthetic=True,
            companies=companies,
            identities=sorted(identities),
            cross_company=sorted(cross),
            sources=sources,
            coverage=coverage,
        ),
    )
    # Display proposals are bound to the actual persisted snapshot by the demo, not placeholders in evidence.
    save(
        FOLDER / "scenario.json",
        dict(
            title="Northstar portfolio consolidation review",
            boundary="All companies, people, records and consequences are synthetic. No external retirement.",
        ),
    )


if __name__ == "__main__":
    main()
