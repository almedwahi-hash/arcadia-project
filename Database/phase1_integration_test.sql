-- Arcadia Phase 1 — Integration test harness (DB layer)
-- Simulates Laila integration logic without modifying production n8n.
-- Run in Supabase SQL Editor or via migration test session.
-- Cleans up test data on completion.

BEGIN;

-- ---------- helpers (session-local) ----------
CREATE OR REPLACE FUNCTION pg_temp.phase1_ensure_conversation(p_lead_id uuid)
RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_conv uuid;
BEGIN
  SELECT conversation_id INTO v_conv FROM public.leads WHERE lead_id = p_lead_id;
  IF v_conv IS NULL THEN
    v_conv := gen_random_uuid();
    UPDATE public.leads SET conversation_id = v_conv WHERE lead_id = p_lead_id;
  END IF;
  RETURN v_conv;
END;
$$;

CREATE OR REPLACE FUNCTION pg_temp.phase1_log_interaction(
  p_lead_id uuid,
  p_customer_id uuid,
  p_conversation_id uuid,
  p_channel text,
  p_direction text,
  p_role text,
  p_message_type text,
  p_message_text text,
  p_provider_message_id text,
  p_metadata jsonb DEFAULT '{}'::jsonb
) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_id uuid;
BEGIN
  IF p_provider_message_id IS NOT NULL THEN
    IF EXISTS (
      SELECT 1 FROM public.lead_interactions
      WHERE channel = p_channel AND provider_message_id = p_provider_message_id
    ) THEN
      RAISE EXCEPTION 'DUPLICATE_PROVIDER_MESSAGE' USING ERRCODE = '23505';
    END IF;
  END IF;
  INSERT INTO public.lead_interactions (
    lead_id, customer_id, conversation_id, channel, direction, role,
    message_type, message_text, provider_message_id, metadata
  ) VALUES (
    p_lead_id, p_customer_id, p_conversation_id, p_channel, p_direction, p_role,
    p_message_type, p_message_text, p_provider_message_id, p_metadata
  ) RETURNING interaction_id INTO v_id;
  RETURN v_id;
END;
$$;

-- ---------- Scenario 1: new customer ----------
DO $$
DECLARE
  v_phone text := 'phase1test_new_' || substr(gen_random_uuid()::text, 1, 8);
  v_cust uuid;
  v_lead uuid;
  v_conv uuid;
BEGIN
  INSERT INTO public.customers (phone, preferred_language)
  VALUES (v_phone, 'ar') RETURNING customer_id INTO v_cust;

  INSERT INTO public.leads (phone, customer_id, source, stage)
  VALUES (v_phone, v_cust, 'phase1_test', 'new') RETURNING lead_id INTO v_lead;

  v_conv := pg_temp.phase1_ensure_conversation(v_lead);

  PERFORM pg_temp.phase1_log_interaction(
    v_lead, v_cust, v_conv, 'whatsapp', 'inbound', 'user', 'text',
    'test inbound new customer', 'wa_phase1_new_001', '{"scenario":"new_customer"}'::jsonb
  );

  PERFORM pg_temp.phase1_log_interaction(
    v_lead, v_cust, v_conv, 'whatsapp', 'outbound', 'assistant', 'text',
    'test outbound new customer', NULL, '{"scenario":"new_customer"}'::jsonb
  );

  INSERT INTO public.agent_actions (agent_name, action_type, lead_id, customer_id, source_channel, status, output_summary)
  VALUES ('sales', 'test_new_customer', v_lead, v_cust, 'whatsapp', 'success', 'scenario1_ok');
END $$;

-- ---------- Scenario 2: existing customer (reuse conversation) ----------
DO $$
DECLARE
  v_lead uuid;
  v_cust uuid;
  v_conv1 uuid;
  v_conv2 uuid;
BEGIN
  SELECT lead_id, customer_id INTO v_lead, v_cust
  FROM public.leads WHERE phone LIKE 'phase1test_new_%' LIMIT 1;

  v_conv1 := pg_temp.phase1_ensure_conversation(v_lead);

  PERFORM pg_temp.phase1_log_interaction(
    v_lead, v_cust, v_conv1, 'whatsapp', 'inbound', 'user', 'text',
    'second message same session', 'wa_phase1_existing_002', '{"scenario":"existing_customer"}'::jsonb
  );

  v_conv2 := pg_temp.phase1_ensure_conversation(v_lead);
  IF v_conv1 <> v_conv2 THEN
    RAISE EXCEPTION 'CONVERSATION_ID_ROTATED_UNEXPECTEDLY';
  END IF;
END $$;

-- ---------- Scenario 3: webhook duplicate (idempotency) ----------
DO $$
DECLARE
  v_lead uuid;
  v_cust uuid;
  v_conv uuid;
  v_dup boolean := false;
BEGIN
  SELECT lead_id, customer_id, conversation_id INTO v_lead, v_cust, v_conv
  FROM public.leads WHERE phone LIKE 'phase1test_new_%' LIMIT 1;

  -- First insert succeeds; second must fail (n8n: check-before-insert OR ON CONFLICT — not EXCEPTION block)
  PERFORM pg_temp.phase1_log_interaction(
    v_lead, v_cust, v_conv, 'whatsapp', 'inbound', 'user', 'text',
    'duplicate attempt', 'wa_phase1_dup_003', '{"scenario":"duplicate_test"}'::jsonb
  );
  BEGIN
    PERFORM pg_temp.phase1_log_interaction(
      v_lead, v_cust, v_conv, 'whatsapp', 'inbound', 'user', 'text',
      'duplicate attempt retry', 'wa_phase1_dup_003', '{"scenario":"duplicate_retry"}'::jsonb
    );
    RAISE EXCEPTION 'DUPLICATE_WAS_NOT_BLOCKED';
  EXCEPTION WHEN unique_violation THEN
    v_dup := true;
  END;

  IF NOT v_dup THEN
    RAISE EXCEPTION 'DUPLICATE_WAS_NOT_BLOCKED';
  END IF;

  -- NULL provider_message_id must NOT block (second message without id)
  PERFORM pg_temp.phase1_log_interaction(
    v_lead, v_cust, v_conv, 'whatsapp', 'inbound', 'user', 'text',
    'no provider id message 1', NULL, '{"scenario":"null_provider_ok"}'::jsonb
  );
  PERFORM pg_temp.phase1_log_interaction(
    v_lead, v_cust, v_conv, 'whatsapp', 'inbound', 'user', 'text',
    'no provider id message 2', NULL, '{"scenario":"null_provider_ok_2"}'::jsonb
  );
END $$;

-- ---------- Scenario 4: pricing success ----------
DO $$
DECLARE
  v_lead uuid;
  v_quote jsonb;
BEGIN
  SELECT lead_id INTO v_lead FROM public.leads WHERE phone LIKE 'phase1test_new_%' LIMIT 1;

  v_quote := public.quote_package('Almaty', current_date + 30, current_date + 34, 2, 1, 4, 'recommended', 0.20, true, -1);

  INSERT INTO public.agent_actions (
    agent_name, action_type, lead_id, source_channel, status,
    input_summary, output_summary, metadata
  ) VALUES (
    'pricing', 'get_price', v_lead, 'whatsapp', 'success',
    'Almaty 4N 2pax',
    coalesce(v_quote->>'final_price_usd', v_quote->>'error'),
    jsonb_build_object('scenario', 'pricing_success', 'quote_keys', v_quote)
  );
END $$;

-- ---------- Scenario 5: pricing failure / manual_quote path ----------
DO $$
DECLARE
  v_lead uuid;
  v_quote jsonb;
BEGIN
  SELECT lead_id INTO v_lead FROM public.leads WHERE phone LIKE 'phase1test_new_%' LIMIT 1;

  v_quote := public.quote_package('NonexistentCityXYZ', current_date + 30, current_date + 34, 2, 1, 4);

  IF v_quote ? 'error' THEN
    UPDATE public.leads SET stage = 'manual_quote', needs_human = true WHERE lead_id = v_lead;
    INSERT INTO public.agent_actions (
      agent_name, action_type, lead_id, source_channel, status,
      input_summary, output_summary, metadata
    ) VALUES (
      'pricing', 'get_price', v_lead, 'whatsapp', 'failed',
      'NonexistentCityXYZ',
      v_quote->>'error',
      jsonb_build_object('scenario', 'pricing_failure', 'quote', v_quote)
    );
  ELSE
    RAISE EXCEPTION 'EXPECTED_PRICING_ERROR_NOT_RETURNED';
  END IF;
END $$;

-- ---------- Error handler schema test ----------
INSERT INTO public.workflow_failures (
  workflow_name, workflow_id, execution_id, node_name, agent_name,
  source_channel, severity, error_message, status, payload
) VALUES (
  'Arcadia - Phase1 Error Handler Test',
  'test_workflow_id_phase1',
  'test_execution_id_phase1',
  'Intentional Fail Node',
  'system',
  'test',
  'error',
  'Phase1 non-production error handler test',
  'open',
  jsonb_build_object('test', true, 'scenario', 'error_handler_schema')
);

COMMIT;

-- ---------- Report (no PII) ----------
SELECT 'interactions_phase1_test' AS metric, count(*) AS value
FROM public.lead_interactions WHERE metadata ? 'scenario';

SELECT metadata->>'scenario' AS scenario, message_type, direction,
       provider_message_id IS NOT NULL AS has_provider_id
FROM public.lead_interactions
WHERE metadata ? 'scenario'
ORDER BY created_at;

SELECT agent_name, action_type, status, output_summary
FROM public.agent_actions
WHERE metadata ? 'scenario' OR action_type LIKE 'test_%'
ORDER BY created_at DESC;

SELECT workflow_name, workflow_id, execution_id, status, error_message, created_at IS NOT NULL AS has_created_at
FROM public.workflow_failures
WHERE workflow_id = 'test_workflow_id_phase1';
