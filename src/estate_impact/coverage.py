"""Coverage qualifies negative claims; zero observed executions never proves disuse."""

from .contracts import timestamp


def review_coverage(manifests, subject, as_of):
    relevant = [m for m in manifests if subject in m["subjects"]]
    if not relevant:
        return {"state": "UNKNOWN", "reasons": ["No reviewed collection scope"], "evidence": []}
    reasons = []
    for manifest in relevant:
        if manifest["status"] != "complete":
            reasons.append(f"{manifest['id']}: {manifest['status']} collection")
        if not manifest.get("reviewer") or manifest.get("exclusions"):
            reasons.append(f"{manifest['id']}: exclusions or missing reviewer")
        if set(manifest["expected"]) - set(manifest["observed"]):
            reasons.append(f"{manifest['id']}: expected export missing")
        if timestamp(manifest["observed_start"]) > timestamp(manifest["expected_start"]):
            reasons.append(f"{manifest['id']}: partial observation period")
        if timestamp(manifest["observed_end"]) < timestamp(manifest["expected_end"]):
            reasons.append(f"{manifest['id']}: partial observation period")
        age = (timestamp(as_of) - timestamp(manifest["reviewed_at"])).days
        if age < 0 or age > manifest["max_age_days"]:
            reasons.append(f"{manifest['id']}: stale review")
    return {
        "state": "UNKNOWN" if reasons else "SUPPORTED",
        "reasons": sorted(set(reasons)),
        "evidence": sorted(m["id"] for m in relevant),
    }


def execution_summary(fact, coverage):
    if fact is None or fact["state"] != "SUPPORTED":
        return {"observed_count": None, "usage": "UNKNOWN", "coverage": coverage}
    return {
        "observed_count": fact["value"]["count"],
        "usage": "OBSERVED" if fact["value"]["count"] else "UNKNOWN",
        "coverage": coverage,
    }
