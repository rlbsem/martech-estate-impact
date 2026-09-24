# Model semantics

## Evidence and identity

Source assertions remain independent of conclusions. An assertion has a stable hash identity, typed subject and key, JSON value, source artifact, collection timestamp/scope and source location. The key must equal `kind:subject`. An artifact hash includes metadata and source content. Whitespace/content changes therefore create a new artifact identity even when meaning is unchanged; importing the identical artifact is idempotent.

Crosswalk entries are scoped by source and external identifier. One target resolves; no target or multiple targets quarantines the record. Duplicate crosswalk entries fail validation. The model does not guess that two similar labels are the same system. Inventory's two work-manager aliases have consistent values and converge on one typed system fact.

The policy specifies admissible sources and maximum age **per assertion type**. Source membership is scoped authority, not a universal precedence ranking. Multiple admissible equal values corroborate; different values remain disputed. Expired, future-dated or inadmissible claims remain unresolved. A resolution can accept only current admissible assertion IDs with one value; it cannot make stale evidence current. Accepted, rejected, disputed and unresolved dispositions belong to the snapshot. The underlying assertions are unchanged.

Positive evidence from a partial export can still establish a positive claim. It cannot establish absence or completeness. Execution observations are corroboration only: a zero count always leaves usage Unknown. Complete architecture manifests are signed-off declared review scopes at a timestamp, not a claim of full execution history. No finite sample automatically establishes that an annual workflow is unused.

## Requirements and alternatives

Leaf support requires a resolved active system, or a resolved integration whose source, destination and runtime are supported. A proposed activation is support in the declared target model, never evidence of deployment. An absent leaf is Unknown. A declared retired or inactive leaf is Unsupported.

A resolved dependency must be explicitly qualified. Where a contract is specified, offered events, fields and correlation keys must include the required sets. A known gap is Unsupported; absent interface evidence is Unknown. Contract containment is necessary metadata compatibility only. Delivery ordering, schema types, throughput, authorization, replay and observed behavior are not verified by these set checks.

ALL fails on any established mandatory failure; otherwise it is Unknown while any mandatory input is unresolved. ANY succeeds when one qualified candidate is supported; otherwise it is Unknown while a candidate is unresolved, and Unsupported when all candidates definitely fail. Optional inputs are recorded but excluded from mandatory status. An unresolved input cannot safely be assumed optional. Empty groups are Unknown.

The evaluator initializes derived nodes to Unknown. Synchronous passes monotonically refine information until a fixed point. At most one refinement per requirement is needed; unseeded cycles stay Unknown. A supported external alternative can establish a cyclic group's support; an established mandatory failure can propagate through a cycle. Integration cycles, such as CRM lead/status feedback, are not business requirement cycles and are valid topology.

## Proposals, residuals and scope

Proposals never mutate their base snapshot. A relationship removal leaves a referenced requirement input Unknown until the requirement is explicitly revised; deletion is not silently treated as proof of independence. A replacement needs explicit activation, retirement, rewiring and dependency changes. Shared labels do not trigger a swap.

Residual references inspect integration sources, destinations and runtimes, plus direct system-provider dependencies, including unresolved candidate references. A known remaining reference is a blocker even if optional to a business outcome. An unresolved reference is an evidence gap. A removed integration still referenced by a requirement produces Unknown through the dependency evaluator.

Assessment dispositions are ordered: established unsupported requirements or known residual references → `ESTABLISHED_BLOCKERS`; otherwise unresolved requirements, coverage, quarantined identities or uncertain residuals → `UNRESOLVED_EVIDENCE`; otherwise `NO_IDENTIFIED_BLOCKERS_WITHIN_REVIEWED_SCOPE`. Proposed integrations also require established endpoints/runtime; a proposed dependency without a binding to its consumer group remains an explicit evidence gap. Changed failures/unknown outcomes outside selected requirements prevent an apparently clean scoped result. Pre-existing unresolved facts outside the scope are disclosed but do not automatically invalidate a separately reviewed architectural proposal. Contradictory lifecycle actions for the same system are rejected rather than allowing ordering to disguise the final target.

Witness branches explain decisive support/failure/unknown paths with assertion or proposal-action IDs. They are bounded at 50 paths and depth 30, with explicit truncation. They are not minimal-cut proofs or a probability of success. Reports distinguish baseline outcome from target outcome and show unchanged supported requirements.

## Sequencing

Activities carry owners, explicit prerequisites, completion declarations and required acceptance evidence identifiers. Topological order is the structural plan. `ready_now` requires completed prerequisites and available evidence; `completed` also validates declared completion against those gates. Cycle members are distinguished from their blocked descendants and from missing prerequisite IDs. Evidence availability is a trusted reviewed input, not a verifier of the authenticity or operational adequacy of an acceptance artifact. The fixture supplies no operational acceptance evidence, so handoff remains gated even for the revised target.

Snapshot and assessment hashes provide reproducible identity, not signatures or access control. Any input change requires a new record. Time is supplied as an explicit review `as_of`; the dated fixture is reproducible and does not claim current knowledge of a real estate.
