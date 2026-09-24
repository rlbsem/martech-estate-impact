"""Validate a whole artifact before writing; quarantine identity ambiguity per record."""

from estate_impact.contracts import digest, required, timestamp, validate_claim
from estate_impact.identity import IdentityError, resolve
from . import inventory_csv, orchestration_json, executions_csv, stewardship_json

PARSERS = {
    "inventory/csv-v1": inventory_csv.parse,
    "orchestration/json-v1": orchestration_json.parse,
    "executions/csv-v1": executions_csv.parse,
    "stewardship/json-v1": stewardship_json.parse,
}


def prepare(text, metadata, crosswalk):
    required(metadata, ["source", "artifact", "parser", "collected_at", "scope", "status"])
    timestamp(metadata["collected_at"])
    if metadata["parser"] not in PARSERS:
        raise ValueError("unsupported parser")
    if metadata["status"] not in {"complete", "partial", "failed"}:
        raise ValueError("invalid collection status")
    artifact_id = digest({"metadata": metadata, "content": text})
    artifact = dict(metadata, id=artifact_id, checksum=digest(text))
    records = [] if metadata["status"] == "failed" else PARSERS[metadata["parser"]](text)
    assertions, quarantine = [], []
    seen = set()
    for claim in records:
        try:
            if claim.pop("external_subject", False):
                claim["subject"] = resolve(metadata["source"], claim["subject"], crosswalk)
                claim["key"] = f"{claim['kind']}:{claim['subject']}"
            validate_claim(claim)
            identity = (claim["key"], claim["location"])
            if identity in seen:
                raise ValueError("duplicate claim location")
            seen.add(identity)
            assertions.append(
                dict(
                    claim,
                    id=digest([artifact_id, claim]),
                    artifact_id=artifact_id,
                    source=metadata["source"],
                    collected_at=metadata["collected_at"],
                    scope=metadata["scope"],
                    collection_status=metadata["status"],
                )
            )
        except IdentityError as error:
            quarantine.append({"claim": claim, "reason": str(error)})
    return artifact, assertions, quarantine
