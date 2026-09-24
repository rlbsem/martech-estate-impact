"""Identity is a reviewed mapping, never a name similarity heuristic."""


class IdentityError(ValueError):
    pass


def index_crosswalk(entries):
    result = {}
    for entry in entries:
        key = (entry["source"], entry["external"])
        targets = tuple(sorted(set(entry["targets"])))
        if not targets or key in result:
            raise IdentityError(f"empty or duplicate crosswalk entry: {key}")
        result[key] = targets
    return result


def resolve(source, external, crosswalk):
    targets = crosswalk.get((source, external), ())
    if len(targets) != 1:
        raise IdentityError(f"unmapped or ambiguous identity: {source}/{external}")
    return targets[0]
