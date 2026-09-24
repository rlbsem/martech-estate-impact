"""Small, explicit input contracts. Reject malformed evidence before publication."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

KINDS = {
    "system",
    "ownership",
    "integration",
    "interface",
    "requirement",
    "dependency",
    "capability",
    "team",
    "authority",
    "execution",
}
STATES = {"SUPPORTED", "UNSUPPORTED", "UNKNOWN"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def implementation_hash():
    root = Path(__file__).parent
    return digest(
        {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*.py"))
        }
    )


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps require an explicit timezone")
    return parsed


def required(record, fields):
    if not isinstance(record, dict):
        raise ValueError("record must be an object")
    for field in fields:
        if field not in record or record[field] is None or record[field] == "":
            raise ValueError(f"missing {field}")


def validate_claim(claim):
    required(claim, ["key", "kind", "subject", "value", "location"])
    kind, value = claim["kind"], claim["value"]
    if kind not in KINDS:
        raise ValueError(f"unsupported assertion kind: {kind}")
    if claim["key"] != f"{kind}:{claim['subject']}":
        raise ValueError("fact key must match its typed subject")
    required(
        value,
        {
            "system": ["label", "lifecycle", "operator", "environment"],
            "integration": ["source", "destination", "runtime", "owner", "mode"],
            "dependency": ["consumer", "provider", "qualified", "optional"],
            "requirement": ["label", "capability", "mode", "inputs"],
            "interface": ["events", "fields", "keys"],
            "ownership": ["team"],
            "team": ["label"],
            "capability": ["label", "owner", "criticality"],
            "authority": ["domain", "field_group", "role", "scope"],
            "execution": ["count", "start", "end"],
        }[kind],
    )
    if kind == "system" and value["lifecycle"] not in {"active", "proposed", "retired"}:
        raise ValueError("invalid lifecycle")
    if kind == "requirement" and (
        value["mode"] not in {"ALL", "ANY"}
        or not isinstance(value["inputs"], list)
        or len(value["inputs"]) != len(set(value["inputs"]))
    ):
        raise ValueError("invalid requirement group")
    if kind == "dependency":
        if any(type(value[x]) is not bool for x in ("qualified", "optional")):
            raise ValueError("dependency flags must be booleans")
        if not isinstance(value["provider"], str) or not value["provider"].startswith(
            ("sys:", "req:", "int:")
        ):
            raise ValueError("provider must have typed identity")
    if kind == "integration" and value["mode"] != "data_flow":
        raise ValueError(
            "integration topology must be a data_flow; operational requirements are separate"
        )
    if kind == "interface" and any(not isinstance(value[x], list) for x in value):
        raise ValueError("interface dimensions must be lists")
    if kind == "execution":
        if type(value["count"]) is not int or value["count"] < 0:
            raise ValueError("execution count must be nonnegative")
        if timestamp(value["start"]) >= timestamp(value["end"]):
            raise ValueError("invalid observation interval")
    return claim
