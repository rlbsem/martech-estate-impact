"""Bounded evidence paths. These are witness branches, not minimal cut sets."""


def witnesses(requirement, evaluation, max_paths=50, max_depth=30):
    paths = []
    truncated = False

    def walk(subject, path, visited):
        nonlocal truncated
        if len(paths) >= max_paths or len(path) >= max_depth:
            truncated = True
            return
        node = f"req:{subject}"
        if node in visited:
            paths.append(
                path
                + [{"node": node, "state": "UNKNOWN", "reason": "circular support", "evidence": []}]
            )
            return
        req = evaluation["requirements"][subject]
        head = {"node": node, "state": req["state"], "evidence": req["evidence"]}
        inputs = [(key, edge) for key, edge in req["inputs"].items() if not edge["optional"]]
        # Explain failures/unknowns using decisive branches, ALL support and ANY failure require all branches.
        selected = [
            (key, edge)
            for key, edge in inputs
            if (req["mode"] == "ALL" and req["state"] == "SUPPORTED")
            or (req["mode"] == "ANY" and req["state"] == "UNSUPPORTED")
            or edge["state"] == req["state"]
        ]
        if not selected:
            paths.append(path + [head])
        for key, edge in selected:
            if len(paths) >= max_paths:
                truncated = True
                break
            branch = path + [head, {"node": key, **edge}]
            provider = edge["provider"]
            if (
                provider
                and provider.startswith("req:")
                and provider[4:] in evaluation["requirements"]
            ):
                walk(provider[4:], branch, visited | {node})
            else:
                paths.append(
                    branch
                    + (
                        [
                            {
                                "node": provider,
                                "state": evaluation["states"].get(provider, "UNKNOWN"),
                                "evidence": evaluation["evidence"].get(provider, []),
                            }
                        ]
                        if provider
                        else []
                    )
                )

    walk(requirement, [], set())
    return {
        "paths": paths,
        "truncated": truncated,
        "limits": {"paths": max_paths, "depth": max_depth},
    }
