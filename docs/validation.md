# Validation and evidence

Run `python scripts/verify.py`. It stops on failed dependency checks, lint, formatting or pytest; exercises actual PostgreSQL, regenerates the demo twice, compares bytes, checks an installed CLI assessment and records source hashes. It does not label unexecuted tests as passed. The [latest generated report](../examples/generated/verification-report.md), [machine record](evidence/verification.json) and [JUnit output](evidence/pytest.xml) record observed local results.

The tests focus on semantic boundaries, not an arbitrary count:

| Boundary | Challenge |
|---|---|
| Imports | Malformed CSV/JSON, missing identifiers, unsupported parsers, collection failure, duplicate identity |
| Identity and evidence | Explicit aliases, ambiguous and similar names, crosswalk collisions, contradictions, stale evidence, retained review decisions |
| Coverage | Seasonal zero executions, missing source, partial interval, stale/excluded review, complete-to-partial degradation |
| Requirements | ALL/ANY truth tables, optional inputs, qualified alternatives, missing support, integration versus business dependence, seeded and unseeded cycles |
| Counterfactual | Snapshot immutability, renamed topology, unrelated-system invariance, missing relationship, narrow scope, required interface dimensions |
| Explanation | Derived witness chain, source/proposal references, unresolved branches, bounded cycle explanations |
| Planning | Valid order, missing prerequisites, true cycle members versus downstream blocked activities, missing acceptance evidence |
| PostgreSQL | Real server check, concurrent identical imports, idempotence, append-only trigger, failed import/publication rollback, evidence view roundtrip |
| Reports and end-to-end | JSON/Markdown agreement, Mermaid node/edge consistency, escaped labels, filtering/truncation, three scenarios and deterministic regeneration |

## Independent reference

`tests/oracle/reference_evaluator.py` imports no production evaluator. It recursively searches finite proof branches, treats back-edges without a foundation as unresolved, and maps its own T/F/? results to the public states. The production implementation instead refines a global state vector synchronously. A deterministic seed creates 350 small graphs of five requirements with ALL/ANY groups, cycles, missing leaves and active/retired leaves. Agreement is an independent check on that bounded dependency sublanguage, not a formal proof of every importer, contract or larger graph.

Metamorphic checks reorder evidence, add an unrelated system, rename identifiers, remove supporting evidence, qualify an alternative and degrade collection coverage. They assert semantic invariants rather than copying individual implementation statements. Adding an unrelated system changes the snapshot/proposal identities; the test normalizes only those proposal-reference hashes while requiring the actual requirement states, evidence paths and original source references to stay the same.

## Review-driven fixes

The implementation review found and corrected these issues before delivery:

1. Unresolved integration candidates were omitted from topology output. They now appear with uncertain styling and remain Unknown in the analytical model.
2. A caller could narrow selected requirements and omit newly changed consequences. Assessments now surface out-of-scope changes, and failures there prevent a clean result.
3. Retirement witness leaves lacked the exact proposed-action reference. They now point to the relevant action in the evidence index.
4. Complete architecture review manifests could be read as complete runtime windows. Fixtures now explicitly scope them to point-in-time architecture; partial execution evidence remains separate.
5. Snapshot construction retained nested references to caller inputs. It now deep-copies those inputs, and a regression test confirms that later caller edits cannot alter an already constructed snapshot.

These fixes have regression tests. No difficult test was dropped to obtain green results. One invariance assertion was adjusted after proposal-action references were added: evidence identities must change when a proposal is rebound, while analytical consequences must remain invariant.

## Limits of the evidence

Local results are observed; GitHub-hosted CI and Docker execution are not claimed. The workflow is configured to provision PostgreSQL and run the same verification. Mermaid syntax and escaping are tested structurally; all four generated diagrams were additionally rendered with Mermaid 10.9.3 in headless Microsoft Edge and the focused views visually inspected. [Rendering evidence](evidence/diagram-rendering.json) records dimensions and node counts. This additional local presentation check is separate from the Python verification script; no cross-version browser renderer compatibility guarantee is made. There is no load benchmark, vendor API test, real enterprise export, disaster-recovery test or deployment safety certification. The model's correctness still depends on human-reviewed claims and scope.
