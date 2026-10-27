# Enterprise Technology Estate Change Assurance

Technology consolidation needs a defensible account of what could stop working. The console combines an immutable evidence snapshot with isolated proposed changes, requirement-level witness chains and an authenticated review ledger.

This is an additive application around the original PostgreSQL analysis engine. The original 24-system Marketing estate, CLI, fixtures, reports and independent evaluator remain available. The new scenario is a separate synthetic group: Northstar's parent platform, Atlas Industrial, Boreal Services and Cinder Software.

## What can be investigated

| Console area | Implemented behavior |
|---|---|
| Estate impact | Select any collected active platform; inspect its persisted retirement counterfactual, before/after requirements and keyboard-accessible dependency graph |
| Change reviews | Inspect retirement, replacement, integration removal, capability reassignment, consolidation and temporary-outage proposals; compare immutable replacement revisions |
| Evidence ledger | Inspect collection time, source revision, artifact identity, authority by assertion type, disputed ownership and incomplete seasonal observations; download the exact published record |
| Review history | Inspect actual PostgreSQL decisions, readiness gates and scope; an accepted Boreal reassignment, a rejected retirement and blocked replacement remain distinguishable |

The temporary-outage proposal uses the core unavailable-system counterfactual. It does not model time-to-recovery, capacity, service latency or an external shutdown.

## Architecture and invariants

1. The finite adapters in `estate_change/evidence.py` validate CMDB CSV and versioned registry, owner-attestation and execution JSON. Every claim retains source location and artifact identity. The raw input files are versioned under `fixtures/change-assurance/`.
2. The original reconciliation policy applies source authority by claim type. Different source revisions are selected explicitly for a snapshot; an old revision never overwrites an artifact. Publication rejects revision rollback and same-revision content collisions.
3. Company-qualified identities such as `atlas/crm` and `boreal/crm` remain distinct. Cross-company references must appear in the explicit catalog allowlist. The parent integration fabric has its own scope.
4. The original three-state fixed-point engine evaluates typed requirements and declared interface compatibility. Inventory presence and data-flow connectivity alone do not establish a business dependency. Empty groups, unresolved claims and unanchored cycles cannot prove support.
5. A proposal binds one exact content-addressed snapshot. Its proposed facts are detached from the current facts. PostgreSQL persists the original assessment and immutable proposal revision; changing a proposal advances its head through compare-and-swap.
6. Readiness combines the core assessment, conservative impact-scope closure, declared system scope, accountable owners and sequencing checks. It is stronger than counting broken dependencies. An unchanged ANY outcome does not permit omitting the affected requirement from review.
7. Database review uses a restricted login and `ca_decide`, a SECURITY DEFINER function with a fixed trusted schema path. `session_user`, enabled authority and complete company scope are checked inside the transaction. A request cannot choose its reviewer name. Public function execution and direct reviewer table writes are denied.
8. Evidence head and proposal head locks follow a common order. A new snapshot, later proposal revision, expired evidence or revoked reviewer makes prior acceptance stale. The original decision remains immutable.
9. The browser uses a different SELECT-only identity, strict same-origin content policy, no third-party scripts and no write endpoints. It reads real PostgreSQL records and computes no substitute financial or dependency metrics in HTML.

The trusted local publisher controls source selection, the catalog and reviewer grants. This is not a production identity-provider integration or a tamper-resistant system against a PostgreSQL superuser. Review gates establish readiness within the finite declared architecture, never external operational acceptance or cutover authority.

## Why the revised replacement is still blocked

Replacement revision 1 lacks the declared `permission` field required by the campaign input contract. Revision 2 repairs that metadata, restoring modeled campaign support. The disputed Atlas owner and unobserved annual adapter remain unresolved. Correcting an interface does not establish complete collection, business accountability or runtime acceptance.

The annual workflow has zero recorded executions in a partial October sample. That is not evidence that the annual dependency is unused. Separately, two unanchored approval requirements remain Unknown.

## Evidence and reproduction

- [Observed execution, screenshots and independent comparisons](evidence/change-assurance/README.md)
- [Local launch, review and teardown](change-assurance-operations.md)
- [Validation boundaries and test design](change-assurance-validation.md)
- [Preserved original model semantics](model-semantics.md)
- [Original generated assessments](../examples/generated/estate-overview.md)

All entities and observations are synthetic. No actual enterprise, client architecture, vendor certification, cost saving or production deployment is claimed.
