# Validation design and claim boundaries

The original engine and its independent graph oracle are preserved byte-for-byte. New tests live in `change_tests/` and run separately so they do not replace original test collection or fixtures.

| Area | Executed acceptance design |
|---|---|
| Original regression | Native PostgreSQL suite, including 350 generated bounded graph comparisons; original demo regenerated twice to fresh directories |
| Scoped evidence | Repeated local CRM IDs, artifact revision/provenance readback, unknown inventory, owner conflict, failed/stale sources, denied source authority and cross-company references |
| Proposal correctness | All six change classes, interface repair with remaining blockers, conservative scope omissions, reversed dependency bindings, cycles and missing sequencing evidence |
| Independent comparison | Preserved recursive proof oracle plus a separate typed-foundation adapter; compares baseline and every displayed counterfactual without reusing production node states |
| Governance | Actual separate reviewer logins, denied scope, denied direct table writes, blocked acceptance, recorded rejection, immutable versions/decisions, stale revision/evidence and revoked authority |
| Recovery | Compare-and-swap race, snapshot/revision rollback and real child-process termination before each publication commit; successful retry and authoritative readback |
| Browser | Keyboard interaction, target-state graph, witness drilldown, persisted metrics, exact downloaded record, error state, no external requests, rejected write endpoints, five viewport widths and axe accessibility checks |
| Packaging | Built-wheel byte parity, source-bound screenshots, original-byte inventory, current SHA-256 package manifest, local Markdown targets and public-file pattern scan |
| Container lane | Actual Linux CI Compose startup, seed completion, restricted console mounts, non-root/read-only application containers, browser checks and independent exact-project resource absence after teardown |

[The observed execution record](evidence/change-assurance/README.md) gives actual counts and versions. CI is reported separately from local execution; configuration alone does not establish a hosted pass.

## Limits

- All source observations, entities and reviewer reasons are synthetic. The application does not discover a real estate, invoke a model, certify a vendor, retire technology or establish business savings.
- Interface containment proves declared metadata compatibility only. Operational acceptance, capacity, tenant isolation under hostile workloads and cutover execution require separate evidence.
- The independent oracle is bounded. Its typed adapter independently resolves finite system/integration foundations and declared interface sets; it is not an independent reimplementation of source authority, PostgreSQL permissions or all migration semantics. Those are challenged by separate negative tests.
- Native PostgreSQL roles provide real local permission boundaries. The trusted owner can change policy and grants; the application does not defeat an administrator or implement enterprise SSO.
- Automated accessibility checks cover recorded states, with rule-specific rechecks of any incomplete result. They do not replace assistive-technology testing or an accessibility certification.
- Current package hashes describe current files. Original package manifests, diagrams, screenshots and prior verification records remain historical artifacts with their original bytes and scope.
