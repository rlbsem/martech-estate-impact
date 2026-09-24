"""Set containment is declared metadata compatibility, never runtime verification."""


def compare(required, offered):
    if offered is None:
        return {"state": "UNKNOWN", "missing": {}, "basis": "missing interface evidence"}
    missing = {
        kind: sorted(set(required.get(kind, [])) - set(offered.get(kind, [])))
        for kind in ("events", "fields", "keys")
    }
    return {
        "state": "UNSUPPORTED" if any(missing.values()) else "SUPPORTED",
        "missing": missing,
        "basis": "declared metadata only",
    }
