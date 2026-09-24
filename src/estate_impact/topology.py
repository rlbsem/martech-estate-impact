"""Reachability locates candidates; requirement logic decides consequences."""


def data_flows(facts):
    result = []
    for fact in facts.values():
        if fact["kind"] != "integration":
            continue
        values = [fact["value"]] if fact["value"] else fact["candidates"]
        unique = set()
        for value in values:
            identity = tuple(value[k] for k in ("source", "destination", "runtime"))
            if identity in unique:
                continue
            unique.add(identity)
            result.append(
                {
                    "id": fact["subject"],
                    **value,
                    "state": fact["state"],
                    "evidence": fact["evidence"],
                    "proposed": fact.get("proposed", False),
                }
            )
    return sorted(result, key=lambda e: (e["id"], e["source"], e["destination"]))


def reachable(edges, start):
    visited, queue = set(), [start]
    while queue:
        current = queue.pop()
        for edge in edges:
            if edge["source"] == current and edge["destination"] not in visited:
                visited.add(edge["destination"])
                queue.append(edge["destination"])
    return sorted(visited)
