"""Content-addressed publication includes evidence, policy, crosswalk, and review scope."""

from copy import deepcopy

from .assertions import reconcile
from .contracts import digest


def build(
    assertions, artifacts, manifests, policy, crosswalk, as_of, resolutions=(), quarantine=()
):
    facts = reconcile(assertions, policy, as_of, resolutions)
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
    snapshot = {
        "format": "estate-snapshot/v1",
        "as_of": as_of,
        "policy_hash": digest(policy),
        "policy": policy,
        "crosswalk": sorted(crosswalk, key=lambda x: (x["source"], x["external"])),
        "artifacts": sorted(artifacts, key=lambda x: x["id"]),
        "assertions": sorted(assertions, key=lambda x: x["id"]),
        "manifests": sorted(manifests, key=lambda x: x["id"]),
        "quarantine": sorted(quarantine, key=digest),
        "facts": facts,
    }
    # Detach every nested input. A caller reusing or editing an imported record must
    # not mutate an already constructed analytical version through shared objects.
    snapshot = deepcopy(snapshot)
    snapshot["id"] = digest(snapshot)
    return snapshot


def check_identity(snapshot):
    if snapshot["id"] != digest({k: v for k, v in snapshot.items() if k != "id"}):
        raise ValueError("snapshot content hash mismatch")
