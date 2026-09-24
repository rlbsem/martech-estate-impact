# Demonstration walkthrough

## Eight-minute path

**0:00–0:50 — State the decision.** Open the README. “This is a synthetic 24-system Marketing estate. Before retiring a platform, I want to know which outcomes depend on it, which claims establish that dependence and what remains unknown.” Explicitly say all systems, evidence and results are synthetic and do not represent any real company or client architecture.

**0:50–1:40 — Show the model.** Open the [estate overview](../examples/generated/estate-overview.md) and [focused campaign map](../examples/generated/campaign-workflow-diagram.md). Explain separate business accountability and technical operators. Point to the disputed owner or stale personalization integration; the system preserves the uncertainty instead of silently selecting a convenient source.

**1:40–3:20 — Retire work management.** Open the [retirement assessment](../examples/generated/retire-work-manager-assessment.md) and [impact diagram](../examples/generated/retire-work-manager-impact-diagram.md). Follow the business requirement backward: follow-up → webinar identifiers → shared campaign creation → work-manager brief/status dependency. The result came from typed rules, not graph reachability. Open one assertion in [evidence-index.json](../examples/generated/evidence-index.json) and show source location, collection time and evidence ID.

**3:20–4:10 — Explain the non-failures.** Registration remains supported. Operational reporting's work-manager input is optional, so its business requirement remains supported even though a remaining integration reference must still be cleaned up. The seasonal workflow is Unknown: zero recent executions in a partial window cannot prove an annual dependency has disappeared.

**4:10–5:40 — Replace the webinar platform.** Compare the [incomplete replacement](../examples/generated/replace-webinar-incomplete-assessment.md) and [revised result](../examples/generated/replace-webinar-revised-assessment.md). Registration is supported in both; attendance follow-up and campaign attribution require events/fields/keys absent from the incomplete offer. The revised proposal closes those declared gaps and rewires references. Show the [target state](../examples/generated/webinar-target-state-diagram.md) and [diff](../examples/generated/target-state-diff.md). The original snapshot remains unchanged.

**5:40–6:40 — Explain what must happen first.** Show the activity order and missing acceptance evidence. The retirement fixture also has an explicit prerequisite cycle; data-flow feedback loops are allowed, but a circular plan cannot progress. “No identified blockers within reviewed scope” does not mean operational compatibility, deployment authorization or safe cutover.

**6:40–8:00 — Show evidence of engineering quality.** Open the [verification report](../examples/generated/verification-report.md). Mention actual PostgreSQL rollback/concurrency tests, immutable snapshots, the independent bounded evaluator and metamorphic checks. Finish at the handoff boundary: architecture analysis defines the target requirements; migration assurance checks preservation during transition; execution governance governs what may run.

## Deeper 20–30 minute discussion

Spend five minutes on enterprise discovery and review scope: who owns the completeness declaration, how seasonal dependencies are collected and how a contradiction is resolved. Spend five on ALL/ANY logic and cycles using `tests/test_requirements.py` and the independent oracle. Spend five on transactional publication, content identity and typed SQL projections. Spend five on proposal isolation, residual references, metadata compatibility limits and activity gates. Use the remaining time to discuss larger-estate performance and organizational adoption work that has not been implemented.

## What the presenter must understand

- Why connected systems can remain unaffected, and why a qualified alternative still does not remove residual references.
- The difference between a source assertion, its snapshot disposition and a proposed future assertion.
- How ALL/ANY and Unknown interact, why optional inputs do not fail mandatory groups, and why circular claims cannot prove themselves.
- Why a point-in-time architecture review can be complete while runtime exports are partial, and why that limits the conclusion.
- Why interface set containment is weaker than operational compatibility and why acceptance evidence is still required.
- What was actually run locally versus merely configured for Docker/GitHub, and where the portfolio's other repositories have different responsibilities.

Do not present the synthetic reviews as personal client delivery history or claim an automatic enterprise discovery capability. Be prepared to explain the code and decisions; the artifacts support a discussion, not a substitute for understanding them.
