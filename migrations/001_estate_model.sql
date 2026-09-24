-- Append-only evidence; immutable snapshots retain the complete decision input.
CREATE TABLE IF NOT EXISTS source_artifact (
 id text PRIMARY KEY, source text NOT NULL, checksum text NOT NULL,
 parser text NOT NULL, collected_at timestamptz NOT NULL,
 scope jsonb NOT NULL, status text NOT NULL CHECK(status IN ('complete','partial','failed')),
 payload jsonb NOT NULL
);
CREATE TABLE IF NOT EXISTS assertion (
 id text PRIMARY KEY, artifact_id text NOT NULL REFERENCES source_artifact(id),
 fact_key text NOT NULL, kind text NOT NULL CHECK(kind IN
 ('system','ownership','integration','interface','requirement','dependency','capability','team','authority','execution')),
 subject text NOT NULL, source_location text NOT NULL, value jsonb NOT NULL, payload jsonb NOT NULL,
 UNIQUE(artifact_id, fact_key, source_location)
);
CREATE INDEX IF NOT EXISTS assertion_key_idx ON assertion(fact_key);
CREATE TABLE IF NOT EXISTS identity_quarantine (
 artifact_id text NOT NULL REFERENCES source_artifact(id), ordinal integer NOT NULL,
 payload jsonb NOT NULL, PRIMARY KEY(artifact_id, ordinal)
);
CREATE TABLE IF NOT EXISTS estate_snapshot (
 id text PRIMARY KEY, as_of timestamptz NOT NULL, policy_hash text NOT NULL,
 payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS snapshot_fact (
 snapshot_id text NOT NULL REFERENCES estate_snapshot(id), fact_key text NOT NULL,
 kind text NOT NULL, subject text NOT NULL, state text NOT NULL CHECK(state IN ('SUPPORTED','UNKNOWN')),
 value jsonb, PRIMARY KEY(snapshot_id, fact_key), UNIQUE(snapshot_id, kind, subject)
);
CREATE TABLE IF NOT EXISTS snapshot_assertion (
 snapshot_id text NOT NULL REFERENCES estate_snapshot(id), assertion_id text NOT NULL REFERENCES assertion(id),
 disposition text NOT NULL CHECK(disposition IN ('accepted','rejected','disputed','unresolved')),
 PRIMARY KEY(snapshot_id, assertion_id)
);
CREATE TABLE IF NOT EXISTS assessment (
 id text PRIMARY KEY, snapshot_id text NOT NULL REFERENCES estate_snapshot(id),
 proposal_hash text NOT NULL, implementation text NOT NULL, payload jsonb NOT NULL
);
CREATE OR REPLACE FUNCTION forbid_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'append-only analytical record: create a new version'; END; $$;
DO $$ DECLARE t text; BEGIN
 FOREACH t IN ARRAY ARRAY['source_artifact','assertion','identity_quarantine','estate_snapshot',
                          'snapshot_fact','snapshot_assertion','assessment'] LOOP
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = t || '_immutable' AND tgrelid = to_regclass(t)) THEN
   EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION forbid_mutation()', t || '_immutable', t);
  END IF;
 END LOOP;
END $$;
-- Inspectable typed projections; no inference from data-flow connectivity.
CREATE OR REPLACE VIEW integration_topology AS
 SELECT snapshot_id, subject AS integration_id, state,
 value->>'source' AS source_system, value->>'destination' AS destination_system,
 value->>'runtime' AS execution_runtime FROM snapshot_fact WHERE kind='integration';
CREATE OR REPLACE VIEW dependency_requirements AS
 SELECT snapshot_id, fact_key, state, value->>'consumer' AS consumer,
 value->>'provider' AS provider, value->>'qualified' AS qualified,
 value->>'optional' AS optional FROM snapshot_fact WHERE kind='dependency';
CREATE OR REPLACE VIEW evidence_trace AS
 SELECT sa.snapshot_id, a.fact_key, a.kind, a.subject, sa.disposition,
 a.id AS assertion_id, a.source_location, a.value, s.source, s.collected_at, s.scope, s.checksum
 FROM snapshot_assertion sa JOIN assertion a ON a.id=sa.assertion_id
 JOIN source_artifact s ON s.id=a.artifact_id;
CREATE OR REPLACE VIEW system_instances AS
 SELECT snapshot_id, subject AS system_id, state, value->>'label' AS label,
 value->>'lifecycle' AS lifecycle, value->>'operator' AS technical_operator,
 value->>'environment' AS environment FROM snapshot_fact WHERE kind='system';
CREATE OR REPLACE VIEW business_accountability AS
 SELECT snapshot_id, subject AS system_id, state, value->>'team' AS accountable_team
 FROM snapshot_fact WHERE kind='ownership';
CREATE OR REPLACE VIEW business_capabilities AS
 SELECT snapshot_id, subject AS capability_id, state, value->>'label' AS label,
 value->>'owner' AS accountable_team, value->>'criticality' AS criticality
 FROM snapshot_fact WHERE kind='capability';
CREATE OR REPLACE VIEW workflow_requirements AS
 SELECT snapshot_id, subject AS requirement_id, state, value->>'mode' AS group_mode,
 value->>'capability' AS capability_id, value->'inputs' AS dependency_keys
 FROM snapshot_fact WHERE kind='requirement';
CREATE OR REPLACE VIEW interface_contracts AS
 SELECT snapshot_id, subject AS system_id, state, value->'events' AS event_types,
 value->'fields' AS field_groups, value->'keys' AS correlation_keys
 FROM snapshot_fact WHERE kind='interface';
CREATE OR REPLACE VIEW authority_claims AS
 SELECT snapshot_id, subject AS authority_id, state, value->>'domain' AS domain,
 value->'field_group' AS field_group, value->>'role' AS authority_role, value->>'scope' AS scope
 FROM snapshot_fact WHERE kind='authority';
