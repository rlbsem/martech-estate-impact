from copy import deepcopy

import pytest

from estate_impact.coverage import review_coverage, execution_summary


def test_seasonal_zero_partial_never_means_unused(snapshot):
    coverage = review_coverage(snapshot["manifests"], "work-manager", snapshot["as_of"])
    result = execution_summary(snapshot["facts"]["execution:seasonal-launch"], coverage)
    assert result["observed_count"] == 0 and result["usage"] == "UNKNOWN"
    assert coverage["state"] == "UNKNOWN" and len(coverage["reasons"]) >= 3


def test_missing_export_unknown():
    coverage = review_coverage([], "missing", "2026-09-24T00:00:00Z")
    assert coverage["state"] == "UNKNOWN"
    assert execution_summary(None, coverage)["usage"] == "UNKNOWN"


@pytest.mark.parametrize(
    "mutation", ["partial", "failed", "missing-export", "stale", "partial-period", "exclusion"]
)
def test_coverage_degradation_cannot_improve_certainty(snapshot, mutation):
    manifests = deepcopy(snapshot["manifests"])
    m = next(m for m in manifests if "webinar" in m["subjects"])
    assert review_coverage(manifests, "webinar", snapshot["as_of"])["state"] == "SUPPORTED"
    if mutation in {"partial", "failed"}:
        m["status"] = mutation
    elif mutation == "missing-export":
        m["observed"] = []
    elif mutation == "stale":
        m["reviewed_at"] = "2020-01-01T00:00:00Z"
    elif mutation == "partial-period":
        m["expected_start"] = "2026-09-01T00:00:00Z"
    else:
        m["exclusions"] = ["unreviewed connector"]
    assert review_coverage(manifests, "webinar", snapshot["as_of"])["state"] == "UNKNOWN"
