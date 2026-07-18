"""010 — Case Reconstruction read functions (Slice 3A, AGC Session 014).

No tables are created or altered: the reconstruction is a transient,
read-only projection with no epistemic standing of its own. These STABLE
functions are the PostgreSQL rendering of CASE_RECONSTRUCTION.md 0.1.0;
the Python composer is the independent sibling, and the H8 suite compares
them through semantic structural equality strengthened by canonical byte
identity (via the parity-proven argus_private.canonical_jsonb).

Composition may reveal relationships already present in the constitutional
graph. It may never create a meaning that no constitutional record already
carries.

Revision ID: 010_case_reconstruction
Revises: 009_hypotheses
"""

from alembic import op

revision = "010_case_reconstruction"
down_revision = "009_hypotheses"
branch_labels = None
depends_on = None

INVOKER = "LANGUAGE plpgsql STABLE SET search_path = argus_private, pg_catalog, pg_temp"
SQL_STABLE = "LANGUAGE sql STABLE SET search_path = argus_private, pg_catalog, pg_temp"


def upgrade() -> None:
    # Canonical timestamp rendering (chain_version=1 form, shared with the
    # audit chain): YYYY-MM-DDTHH:MM:SS.ffffffZ, UTC.
    op.execute(
        """
        CREATE FUNCTION argus_private.rc_ts(t timestamptz) RETURNS text
        LANGUAGE sql IMMUTABLE
        SET search_path = argus_private, pg_catalog, pg_temp
        AS $$
            SELECT CASE WHEN t IS NULL THEN NULL
                        ELSE to_char(t AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
                   END
        $$;
        """
    )

    # Independent SQL recomputation of chain integrity (never the Python
    # verifier): CHAIN_VALID means chain integrity only — never that
    # evidence, claims, or the case are verified.
    op.execute(
        """
        CREATE FUNCTION argus_private.audit_chain_status(p_case_id text) RETURNS text
        """ + INVOKER + """
        AS $$
        DECLARE
            v_head record; r record;
            v_prev text := repeat('0', 64);
            v_expected integer := 0;
            v_text text;
            v_valid boolean := true;
        BEGIN
            SELECT last_sequence, last_event_hash INTO v_head
              FROM public.case_audit_heads WHERE case_id = p_case_id;
            IF NOT FOUND THEN RETURN 'CHAIN_INVALID'; END IF;
            FOR r IN SELECT * FROM public.audit_entries
                      WHERE case_id = p_case_id ORDER BY seq LOOP
                v_expected := v_expected + 1;
                IF r.seq IS DISTINCT FROM v_expected THEN v_valid := false; END IF;
                IF r.previous_event_hash IS DISTINCT FROM v_prev THEN v_valid := false; END IF;
                v_text :=
                    argus_private.chain_field('chain_version', r.chain_version::text) || E'\n' ||
                    argus_private.chain_field('case_id', r.case_id) || E'\n' ||
                    argus_private.chain_field('seq', r.seq::text) || E'\n' ||
                    argus_private.chain_field('target_type', r.target_type) || E'\n' ||
                    argus_private.chain_field('target_id', r.target_id) || E'\n' ||
                    argus_private.chain_field('action', r.action) || E'\n' ||
                    argus_private.chain_field('actor_class', r.actor_class) || E'\n' ||
                    argus_private.chain_field('actor_id', r.actor_id) || E'\n' ||
                    argus_private.chain_field('ai_model_version', r.ai_model_version) || E'\n' ||
                    argus_private.chain_field('occurred_at',
                        to_char(r.occurred_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')) || E'\n' ||
                    argus_private.chain_field('outcome', r.outcome) || E'\n' ||
                    argus_private.chain_field('canonical_payload', r.canonical_payload) || E'\n' ||
                    argus_private.chain_field('previous_event_hash', r.previous_event_hash);
                IF encode(sha256(convert_to(v_text, 'UTF8')), 'hex')
                   IS DISTINCT FROM r.event_hash THEN
                    v_valid := false;
                END IF;
                v_prev := r.event_hash;
            END LOOP;
            IF v_expected = 0 THEN
                IF v_head.last_sequence <> 0
                   OR v_head.last_event_hash <> repeat('0', 64) THEN
                    v_valid := false;
                END IF;
            ELSE
                IF v_head.last_sequence <> v_expected
                   OR v_head.last_event_hash <> v_prev THEN
                    v_valid := false;
                END IF;
            END IF;
            RETURN CASE WHEN v_valid THEN 'CHAIN_VALID' ELSE 'CHAIN_INVALID' END;
        END $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.rc_retraction(
            p_retracted timestamptz, p_reason text
        ) RETURNS jsonb
        LANGUAGE sql IMMUTABLE
        SET search_path = argus_private, pg_catalog, pg_temp
        AS $$
            SELECT CASE WHEN p_retracted IS NULL THEN NULL::jsonb
                        ELSE jsonb_build_object(
                            'retracted_at', argus_private.rc_ts(p_retracted),
                            'reason', p_reason)
                   END
        $$;
        """
    )

    op.execute(
        """
        CREATE FUNCTION argus_private.case_reconstruction(p_case_id text) RETURNS jsonb
        """ + INVOKER + """
        AS $$
        DECLARE v_doc jsonb;
        BEGIN
            PERFORM 1 FROM public.cases WHERE id = p_case_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'ONT-CAS-001: inadmissible: ONT-CAS-001:unknown-case';
            END IF;

            SELECT jsonb_build_object(
                'case', (
                    SELECT jsonb_build_object(
                        'id', c.id, 'title', c.title, 'status', c.status,
                        'responsible_actor', c.responsible_actor,
                        'created_at', argus_private.rc_ts(c.created_at),
                        'ontology_class', 'ONT-CAS-001',
                        'authorities', coalesce((
                            SELECT jsonb_agg(jsonb_build_object(
                                       'id', a.id, 'basis', a.basis,
                                       'recorded_by', a.recorded_by,
                                       'created_at', argus_private.rc_ts(a.created_at))
                                   ORDER BY argus_private.rc_ts(a.created_at) COLLATE "C", a.id COLLATE "C")
                              FROM public.case_authorities a
                             WHERE a.case_id = c.id), '[]'::jsonb))
                      FROM public.cases c WHERE c.id = p_case_id),
                'evidence_artifacts', coalesce((
                    SELECT jsonb_agg(
                        CASE WHEN e.status = 'SEALED' THEN jsonb_build_object(
                            'id', e.id, 'ontology_class', 'ONT-EVA-001',
                            'status', e.status,
                            'created_at', argus_private.rc_ts(e.created_at),
                            'retraction', CASE WHEN e.retracted_at IS NULL THEN NULL::jsonb
                                ELSE jsonb_build_object(
                                    'retracted_at', argus_private.rc_ts(e.retracted_at),
                                    'reason', e.retraction_reason,
                                    'superseded_by', e.superseded_by) END,
                            'visibility', jsonb_build_object(
                                'state', 'SEALED', 'content_visible', false,
                                'provenance_detail_visible', false,
                                'withholding_basis', 'AUTHORITY_REQUIRED'))
                        ELSE jsonb_build_object(
                            'id', e.id, 'ontology_class', 'ONT-EVA-001',
                            'status', e.status,
                            'hash_algorithm', e.hash_algorithm,
                            'hash_digest', e.hash_digest,
                            'size_bytes', e.size_bytes,
                            'media_type', e.media_type,
                            'acquisition_description', e.acquisition_description,
                            'ingested_by_class', e.ingested_by_class,
                            'ingested_by_id', e.ingested_by_id,
                            'human_authority', e.human_authority,
                            'created_at', argus_private.rc_ts(e.created_at),
                            'retraction', CASE WHEN e.retracted_at IS NULL THEN NULL::jsonb
                                ELSE jsonb_build_object(
                                    'retracted_at', argus_private.rc_ts(e.retracted_at),
                                    'reason', e.retraction_reason,
                                    'superseded_by', e.superseded_by) END,
                            'visibility', jsonb_build_object(
                                'state', 'FULL', 'content_visible', true,
                                'provenance_detail_visible', true,
                                'withholding_basis', NULL))
                        END ORDER BY e.id COLLATE "C")
                      FROM public.evidence_artifacts e
                     WHERE e.case_id = p_case_id), '[]'::jsonb),
                'source_locators', coalesce((
                    SELECT jsonb_agg(jsonb_build_object(
                               'id', l.id, 'ontology_class', 'ONT-SRC-001',
                               'artifact_id', l.artifact_id, 'scheme', l.scheme,
                               'payload', l.payload::jsonb,
                               'created_by_class', l.created_by_class,
                               'created_by_id', l.created_by_id,
                               'created_at', argus_private.rc_ts(l.created_at),
                               'retraction', argus_private.rc_retraction(
                                   l.retracted_at, l.retraction_reason))
                           ORDER BY l.id COLLATE "C")
                      FROM public.source_locators l
                     WHERE l.case_id = p_case_id), '[]'::jsonb),
                'observations', coalesce((
                    SELECT jsonb_agg(jsonb_build_object(
                               'id', o.id, 'citation', o.citation,
                               'ontology_class', 'ONT-OBS-001',
                               'statement', o.statement,
                               'method_description', o.method_description,
                               'event_time_start', argus_private.rc_ts(o.event_time_start),
                               'event_time_end', argus_private.rc_ts(o.event_time_end),
                               'created_by_class', o.created_by_class,
                               'created_by_id', o.created_by_id,
                               'created_at', argus_private.rc_ts(o.created_at),
                               'retraction', argus_private.rc_retraction(
                                   o.retracted_at, o.retraction_reason),
                               'groundings', coalesce((
                                   SELECT jsonb_agg(jsonb_build_object(
                                              'id', g.id, 'locator_id', g.locator_id,
                                              'created_at', argus_private.rc_ts(g.created_at))
                                          ORDER BY g.locator_id COLLATE "C")
                                     FROM public.observation_groundings g
                                    WHERE g.observation_id = o.id), '[]'::jsonb),
                               'derived', jsonb_build_object(
                                   'is_grounded', argus_private.is_observation_grounded(o.id)))
                           ORDER BY o.citation COLLATE "C")
                      FROM public.observations o
                     WHERE o.case_id = p_case_id), '[]'::jsonb),
                'interpretations', coalesce((
                    SELECT jsonb_agg(jsonb_build_object(
                               'id', i.id, 'citation', i.citation,
                               'ontology_class', 'ONT-INT-001',
                               'meaning_statement', i.meaning_statement,
                               'reasoning_description', i.reasoning_description,
                               'uncertainty_status', i.uncertainty_status,
                               'uncertainty_explanation', i.uncertainty_explanation,
                               'created_by_class', i.created_by_class,
                               'created_by_id', i.created_by_id,
                               'created_at', argus_private.rc_ts(i.created_at),
                               'retraction', argus_private.rc_retraction(
                                   i.retracted_at, i.retraction_reason),
                               'groundings', coalesce((
                                   SELECT jsonb_agg(jsonb_build_object(
                                              'id', g.id,
                                              'observation_id', g.observation_id,
                                              'statement_fingerprint', g.statement_fingerprint,
                                              'grounding_role', g.grounding_role,
                                              'linked_at', argus_private.rc_ts(g.linked_at))
                                          ORDER BY g.observation_id COLLATE "C")
                                     FROM public.interpretation_groundings g
                                    WHERE g.interpretation_id = i.id), '[]'::jsonb),
                               'derived', jsonb_build_object(
                                   'grounding_health',
                                   argus_private.interpretation_grounding_health(i.id)))
                           ORDER BY i.citation COLLATE "C")
                      FROM public.interpretations i
                     WHERE i.case_id = p_case_id), '[]'::jsonb),
                'unknowns', coalesce((
                    SELECT jsonb_agg(jsonb_build_object(
                               'id', u.id, 'citation', u.citation,
                               'ontology_class', 'ONT-UNK-001',
                               'question', u.question,
                               'impact_statement', u.impact_statement,
                               'operational_state', u.operational_state,
                               'created_by_class', u.created_by_class,
                               'created_by_id', u.created_by_id,
                               'created_at', argus_private.rc_ts(u.created_at),
                               'links', coalesce((
                                   SELECT jsonb_agg(jsonb_build_object(
                                              'id', ul.id,
                                              'target_type', ul.target_type,
                                              'target_id', ul.target_id,
                                              'nature', ul.nature,
                                              'linked_at', argus_private.rc_ts(ul.linked_at),
                                              'retraction', argus_private.rc_retraction(
                                                  ul.retracted_at, ul.retraction_reason))
                                          ORDER BY ul.target_type COLLATE "C", ul.target_id COLLATE "C")
                                     FROM public.unknown_links ul
                                    WHERE ul.unknown_id = u.id), '[]'::jsonb),
                               'resolution', (
                                   SELECT jsonb_build_object(
                                              'id', r.id,
                                              'resolution_type', r.resolution_type,
                                              'rationale', r.rationale,
                                              'answering_claims', r.answering_claims::jsonb,
                                              'resolved_by', r.resolved_by,
                                              'created_at', argus_private.rc_ts(r.created_at))
                                     FROM public.unknown_resolutions r
                                    WHERE r.unknown_id = u.id),
                               'derived', jsonb_build_object(
                                   'status', coalesce((
                                       SELECT r.resolution_type
                                         FROM public.unknown_resolutions r
                                        WHERE r.unknown_id = u.id), u.operational_state)))
                           ORDER BY u.citation COLLATE "C")
                      FROM public.unknowns u
                     WHERE u.case_id = p_case_id), '[]'::jsonb),
                'contradictions', coalesce((
                    SELECT jsonb_agg(jsonb_build_object(
                               'id', ct.id, 'citation', ct.citation,
                               'ontology_class', 'ONT-CON-001',
                               'description', ct.description,
                               'contradiction_type', ct.contradiction_type,
                               'scope_definition', ct.scope_definition,
                               'incompatibility_basis', ct.incompatibility_basis,
                               'operational_state', ct.operational_state,
                               'created_by_class', ct.created_by_class,
                               'created_by_id', ct.created_by_id,
                               'created_at', argus_private.rc_ts(ct.created_at),
                               'members', coalesce((
                                   SELECT jsonb_agg(jsonb_build_object(
                                              'id', m.id,
                                              'member_type', m.member_type,
                                              'member_id', m.member_id,
                                              'member_fingerprint', m.member_fingerprint,
                                              'member_role', m.member_role,
                                              'linked_at', argus_private.rc_ts(m.linked_at))
                                          ORDER BY m.member_type COLLATE "C", m.member_id COLLATE "C")
                                     FROM public.contradiction_members m
                                    WHERE m.contradiction_id = ct.id), '[]'::jsonb),
                               'links', coalesce((
                                   SELECT jsonb_agg(jsonb_build_object(
                                              'id', cl.id,
                                              'hypothesis_id', cl.hypothesis_id,
                                              'hypothesis_fingerprint', cl.hypothesis_fingerprint,
                                              'relationship_type', cl.relationship_type,
                                              'explanation', cl.explanation,
                                              'linked_by_class', cl.linked_by_class,
                                              'linked_by_id', cl.linked_by_id,
                                              'linked_at', argus_private.rc_ts(cl.linked_at),
                                              'retraction', argus_private.rc_retraction(
                                                  cl.retracted_at, cl.retraction_reason))
                                          ORDER BY cl.hypothesis_id COLLATE "C")
                                     FROM public.contradiction_links cl
                                    WHERE cl.contradiction_id = ct.id), '[]'::jsonb),
                               'disposition', (
                                   SELECT jsonb_build_object(
                                              'id', d.id, 'outcome', d.outcome,
                                              'rationale', d.rationale,
                                              'informing_refs', d.informing_refs,
                                              'disposed_by', d.disposed_by,
                                              'created_at', argus_private.rc_ts(d.created_at))
                                     FROM public.contradiction_dispositions d
                                    WHERE d.contradiction_id = ct.id),
                               'derived', jsonb_build_object(
                                   'health', argus_private.contradiction_health(ct.id),
                                   'status', coalesce((
                                       SELECT d.outcome
                                         FROM public.contradiction_dispositions d
                                        WHERE d.contradiction_id = ct.id), ct.operational_state)))
                           ORDER BY ct.citation COLLATE "C")
                      FROM public.contradictions ct
                     WHERE ct.case_id = p_case_id), '[]'::jsonb),
                'hypotheses', coalesce((
                    SELECT jsonb_agg(jsonb_build_object(
                               'id', h.id, 'citation', h.citation,
                               'ontology_class', 'ONT-HYP-001',
                               'explanatory_statement', h.explanatory_statement,
                               'reasoning_description', h.reasoning_description,
                               'uncertainty_status', h.uncertainty_status,
                               'uncertainty_explanation', h.uncertainty_explanation,
                               'testability_statement', h.testability_statement,
                               'challenge_condition', h.challenge_condition,
                               'alternative_articulation_at_creation',
                                   h.alternative_articulation_at_creation,
                               'alternative_absence_explanation',
                                   h.alternative_absence_explanation,
                               'no_current_unknowns_explanation',
                                   h.no_current_unknowns_explanation,
                               'no_current_contradictions_explanation',
                                   h.no_current_contradictions_explanation,
                               'created_by_class', h.created_by_class,
                               'created_by_id', h.created_by_id,
                               'created_at', argus_private.rc_ts(h.created_at),
                               'retraction', argus_private.rc_retraction(
                                   h.retracted_at, h.retraction_reason),
                               'groundings', coalesce((
                                   SELECT jsonb_agg(jsonb_build_object(
                                              'id', g.id,
                                              'interpretation_id', g.interpretation_id,
                                              'interpretation_fingerprint', g.interpretation_fingerprint,
                                              'grounding_role', g.grounding_role,
                                              'linked_at', argus_private.rc_ts(g.linked_at))
                                          ORDER BY g.interpretation_id COLLATE "C")
                                     FROM public.hypothesis_groundings g
                                    WHERE g.hypothesis_id = h.id), '[]'::jsonb),
                               'derived', jsonb_build_object(
                                   'hypothesis_health', argus_private.hypothesis_health(h.id),
                                   'current_alternative_state',
                                       argus_private.current_alternative_state(h.id),
                                   'unknown_boundary_state',
                                       argus_private.unknown_boundary_state(h.id),
                                   'contradiction_boundary_state',
                                       argus_private.contradiction_boundary_state(h.id)))
                           ORDER BY h.citation COLLATE "C")
                      FROM public.hypotheses h
                     WHERE h.case_id = p_case_id), '[]'::jsonb),
                'hypothesis_alternatives', coalesce((
                    SELECT jsonb_agg(jsonb_build_object(
                               'id', ha.id,
                               'hypothesis_a_id', ha.hypothesis_a_id,
                               'hypothesis_b_id', ha.hypothesis_b_id,
                               'relation_explanation', ha.relation_explanation,
                               'linked_by_class', ha.linked_by_class,
                               'linked_by_id', ha.linked_by_id,
                               'linked_at', argus_private.rc_ts(ha.linked_at))
                           ORDER BY ha.hypothesis_a_id COLLATE "C", ha.hypothesis_b_id COLLATE "C")
                      FROM public.hypothesis_alternatives ha
                     WHERE ha.hypothesis_a_id IN (
                           SELECT id FROM public.hypotheses WHERE case_id = p_case_id)),
                    '[]'::jsonb),
                'audit_chain', jsonb_build_object(
                    'entry_count', (SELECT count(*)::int FROM public.audit_entries
                                     WHERE case_id = p_case_id),
                    'integrity_status', argus_private.audit_chain_status(p_case_id))
            ) INTO v_doc;
            RETURN v_doc;
        END $$;
        """
    )

    fns = [
        ("rc_ts", "timestamptz"),
        ("rc_retraction", "timestamptz, text"),
        ("audit_chain_status", "text"),
        ("case_reconstruction", "text"),
    ]
    for fn, args in fns:
        op.execute(f"REVOKE ALL ON FUNCTION argus_private.{fn}({args}) FROM PUBLIC")
        op.execute(f"GRANT EXECUTE ON FUNCTION argus_private.{fn}({args}) TO argus_app")


def downgrade() -> None:
    for stmt in [
        "DROP FUNCTION IF EXISTS argus_private.case_reconstruction(text)",
        "DROP FUNCTION IF EXISTS argus_private.rc_retraction(timestamptz, text)",
        "DROP FUNCTION IF EXISTS argus_private.audit_chain_status(text)",
        "DROP FUNCTION IF EXISTS argus_private.rc_ts(timestamptz)",
    ]:
        op.execute(stmt)
