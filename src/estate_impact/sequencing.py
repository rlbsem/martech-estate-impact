"""Activity prerequisites and acceptance gates, not resource scheduling."""


def sequence(activities, evidence):
    indexed = {a["id"]: a for a in activities}
    if len(indexed) != len(activities):
        raise ValueError("duplicate activity id")
    missing = {key: sorted(set(a["prerequisites"]) - indexed.keys()) for key, a in indexed.items()}
    missing = {key: value for key, value in missing.items() if value}
    remaining = set(indexed)
    order = []
    while remaining:
        ready = sorted(key for key in remaining if set(indexed[key]["prerequisites"]) <= set(order))
        if not ready:
            break
        order.extend(ready)
        remaining.difference_update(ready)
    # Distinguish actual cycle members from activities merely downstream of a cycle.
    cyclic = []
    for origin in sorted(remaining):
        todo = list(indexed[origin]["prerequisites"])
        seen = set()
        while todo:
            node = todo.pop()
            if node == origin:
                cyclic.append(origin)
                break
            if node in indexed and node not in seen:
                seen.add(node)
                todo.extend(indexed[node]["prerequisites"])
    invalid_completed = sorted(key for key in remaining if indexed[key].get("completed"))
    completed = set()
    for key in order:
        a = indexed[key]
        if a.get("completed"):
            if set(a["prerequisites"]) <= completed and set(a["requires_evidence"]) <= set(
                evidence
            ):
                completed.add(key)
            else:
                invalid_completed.append(key)
    ready_now = sorted(
        key
        for key in order
        if key not in completed
        and set(indexed[key]["prerequisites"]) <= completed
        and set(indexed[key]["requires_evidence"]) <= set(evidence)
    )
    return {
        "order": order,
        "cycle_members": cyclic,
        "blocked": sorted(remaining),
        "missing_prerequisites": missing,
        "invalid_completed": invalid_completed,
        "ready_now": ready_now,
        "completed": sorted(completed),
        "missing_acceptance": {
            key: sorted(set(a["requires_evidence"]) - set(evidence))
            for key, a in indexed.items()
            if set(a["requires_evidence"]) - set(evidence)
        },
    }
