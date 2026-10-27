"""Finite source adapters, scoped identities and immutable source revision selection."""

import csv
import io
import json
from pathlib import Path

from estate_impact.contracts import digest, timestamp, validate_claim
from estate_impact.snapshots import build

AUTHORITY = {
    "cmdb": {"system", "ownership"},
    "registry": {"integration", "interface", "dependency"},
    "owner": {"ownership", "requirement", "dependency", "capability"},
    "execution": {"execution"},
}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def references(kind, value):
    if kind == "integration":
        return [value[k] for k in ("source", "destination", "runtime")]
    if kind == "dependency":
        return [value["consumer"], value["provider"].split(":", 1)[1]]
    if kind == "requirement":
        return [value["capability"], *[x.split(":", 1)[1] for x in value["inputs"]]]
    return []


def validate_scope(claim, catalog):
    subject = claim["subject"]
    known = catalog["identities"]
    if subject not in known:
        raise ValueError("undeclared scoped identity")
    company = subject.split("/", 1)[0]
    for target in references(claim["kind"], claim["value"]):
        if target not in known:
            raise ValueError("unknown reference identity")
        other = target.split("/", 1)[0]
        if company != other and [subject, target] not in catalog["cross_company"]:
            raise ValueError("cross-company reference not authorized")


def prepare(text, meta, catalog):
    if meta["source"] not in AUTHORITY or meta["status"] not in {"complete", "partial", "failed"}:
        raise ValueError("unsupported source/status")
    timestamp(meta["collected_at"])
    if type(meta["revision"]) is not int or meta["revision"] < 1:
        raise ValueError("positive source revision required")
    aid = digest({"metadata": meta, "content": text})
    artifact = dict(meta, id=aid, checksum=digest(text), parser="change-evidence/v1")
    if meta["source"] == "cmdb":
        records = []
        for line, row in enumerate(csv.DictReader(io.StringIO(text)), 2):
            if set(row) != {"company", "local_id", "label", "lifecycle", "owner"}:
                raise ValueError("invalid CMDB columns")
            subject = row["company"] + "/" + row["local_id"]
            for kind, value in [
                (
                    "system",
                    dict(
                        label=row["label"],
                        lifecycle=row["lifecycle"],
                        operator=row["owner"],
                        environment="synthetic",
                    ),
                ),
                ("ownership", {"team": row["owner"]}),
            ]:
                records.append(
                    dict(kind=kind, subject=subject, value=value, location=f"row:{line}")
                )
    else:
        body = json.loads(text)
        if body.get("format") != "change-source/v1":
            raise ValueError("unsupported source format")
        records = body["records"]
    claims, seen = [], set()
    for record in records:
        c = dict(record, key=f"{record['kind']}:{record['subject']}")
        validate_claim(c)
        validate_scope(c, catalog)
        if c["kind"] not in AUTHORITY[meta["source"]]:
            raise ValueError("source lacks assertion-type authority")
        if c["subject"].split("/", 1)[0] not in meta["scope"]:
            raise ValueError("claim outside collection scope")
        marker = (c["key"], c["location"])
        if marker in seen:
            raise ValueError("duplicate source claim location")
        seen.add(marker)
        claims.append(
            dict(
                c,
                id=digest([aid, c]),
                artifact_id=aid,
                source=meta["source"],
                collected_at=meta["collected_at"],
                scope=meta["scope"],
                collection_status=meta["status"],
            )
        )
    # Failed collection cannot supply positive evidence, but its raw artifact is retained.
    return artifact, [] if meta["status"] == "failed" else claims, []


def load(folder, as_of=None):
    folder = Path(folder)
    catalog = read(folder / "catalog.json")
    prepared = [
        prepare((folder / m["artifact"]).read_text(encoding="utf-8"), m, catalog)
        for m in catalog["sources"]
    ]
    if len({a["source"] for a, _, _ in prepared}) != len(prepared):
        raise ValueError("select exactly one revision of each source per snapshot")
    policy = {
        "version": "change-authority/v1",
        "types": {
            kind: {
                "sources": [s for s, kinds in AUTHORITY.items() if kind in kinds],
                "max_age_days": 30 if kind == "execution" else 90,
            }
            for kind in set.union(*AUTHORITY.values())
        },
    }
    snapshot = build(
        assertions=[c for _, cs, _ in prepared for c in cs],
        artifacts=[a for a, _, _ in prepared],
        manifests=catalog["coverage"],
        policy=policy,
        crosswalk=[],
        as_of=as_of or catalog["as_of"],
    )
    return prepared, snapshot, catalog
