// Phase 2.4A — Booking Approval Handler (Telegram callback + test webhook)
// MANUAL-ONLY POLICY: approves cost/variance/skip metadata — never executes payments.
// Supports: supplier_price_change, booking_financial_commit (gate only), manual_override

const SB = String($env.SUPABASE_URL || 'https://xfibcjhshpmqkrhlpsoa.supabase.co').replace(/\/$/, '');
const KEY = $env.SUPABASE_KEY || $env.SUPABASE_SERVICE_ROLE_KEY;
if (!KEY) throw new Error('SUPABASE_KEY required');

const HDR = {
  apikey: KEY,
  Authorization: `Bearer ${KEY}`,
  'Content-Type': 'application/json',
  Prefer: 'return=representation',
};

async function sb(method, path, body, extra = {}) {
  const opts = { method, url: `${SB}/rest/v1/${path}`, headers: { ...HDR, ...extra }, json: true };
  if (body !== undefined) opts.body = body;
  return await this.helpers.httpRequest(opts);
}

async function sbRpc(fn, args) {
  const rows = await sb.call(this, 'POST', `rpc/${fn}`, args);
  return Array.isArray(rows) ? rows[0] : rows;
}

async function loadAllowlist() {
  const rows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_staff_telegram_allowlist&select=config_value');
  return (rows[0]?.config_value?.user_ids || []).map(String);
}

async function idempotent(key, meta) {
  const hit = await sb.call(this, 'GET', `booking_telegram_idempotency?idempotency_key=eq.${encodeURIComponent(key)}&select=idempotency_key`);
  if (hit.length) return true;
  try {
    await sb.call(this, 'POST', 'booking_telegram_idempotency', {
      idempotency_key: key,
      action_type: meta.action_type || 'approval_callback',
      booking_id: meta.booking_id || null,
      task_id: meta.task_id || null,
      metadata: meta,
    });
  } catch (e) {
    if (String(e.message || e).includes('23505')) return true;
    throw e;
  }
  return false;
}

async function logDenied(userId, action, reason) {
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'approval_denied',
    source_channel: 'telegram:staff',
    input_summary: `user=${userId} action=${action}`.slice(0, 500),
    output_summary: reason,
    status: 'failed',
    metadata: { phase: '2.4A', denied: true },
  });
}

async function tgAnswer(callbackId, text, showAlert = false, simulated = false) {
  if (simulated) return;
  const token = $env.TELEGRAM_BOT_TOKEN || $env.LAILA_TELEGRAM_BOT_TOKEN;
  if (!token || !callbackId) return;
  try {
    await this.helpers.httpRequest({
      method: 'POST',
      url: `https://api.telegram.org/bot${token}/answerCallbackQuery`,
      body: { callback_query_id: callbackId, text: text || 'OK', show_alert: showAlert },
      json: true,
    });
  } catch (_e) {
    // ignore in test mode
  }
}

function parseInput(raw) {
  const payload = raw.body ?? raw;
  if (payload.simulate || payload.callback_data || payload.approval_id) {
    return {
      userId: String(payload.telegram_user_id || ''),
      callbackData: payload.callback_data || '',
      callbackId: payload.callback_query_id || `sim_appr_${Date.now()}`,
      approvalId: payload.approval_id || null,
      decision: payload.decision || null,
      reason: payload.reason || null,
      simulated: true,
    };
  }
  const cb = (payload.callback_query || payload);
  if (payload.callback_query) {
    return {
      userId: String(cb.from?.id || ''),
      callbackData: cb.data || '',
      callbackId: cb.id,
      approvalId: null,
      decision: null,
      reason: null,
      simulated: false,
    };
  }
  return { error: 'invalid_input' };
}

function verifyFinancialWebhookAuth(raw, body) {
  const headers = raw.headers || {};
  const secret =
    headers['x-booking-agent-secret']
    || headers['X-Booking-Agent-Secret']
    || body?.auth_secret
    || raw.auth_secret;
  const expected = $env.BOOKING_AGENT_START_SECRET || $env.BOOKING_AGENT_TEST_SECRET;
  if (expected) {
    if (secret === expected) return { ok: true, method: 'webhook_secret' };
    return { ok: false, error: 'webhook_secret_required' };
  }
  return { ok: true, method: 'allowlist_only' };
}

async function handleApprovalDecision({ approvalId, decision, userId, callbackId, reason, simulated }) {
  const staffTag = `staff:${userId}`;
  const idemKey = `cb:${callbackId}:appr:${approvalId}:${decision}`;

  if (await idempotent.call(this, idemKey, { action_type: 'approval_decision', approval_id: approvalId, decision })) {
    const rows = await sb.call(this, 'GET', `human_approval_queue?approval_id=eq.${encodeURIComponent(approvalId)}&select=approval_id,status,action_type,booking_id`);
    const a = rows[0] || {};
    return { ok: true, idempotent: true, approval_id: approvalId, status: a.status, booking_id: a.booking_id };
  }

  const allowedTypes = ['supplier_price_change', 'booking_financial_commit', 'manual_override'];
  const apprRows = await sb.call(this, 'GET', `human_approval_queue?approval_id=eq.${encodeURIComponent(approvalId)}&select=*`);
  if (!apprRows.length) return { ok: false, error: 'approval_not_found' };
  const appr = apprRows[0];
  if (!allowedTypes.includes(appr.action_type)) {
    return { ok: false, error: 'action_type_not_supported', action_type: appr.action_type };
  }

  const rpcDecision = decision === 'approve' ? 'approved' : 'rejected';
  const result = await sbRpc.call(this, 'resolve_booking_approval', {
    p_approval_id: approvalId,
    p_decision: rpcDecision,
    p_resolved_by: staffTag,
    p_reason: reason,
  });

  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'approval_decision',
    booking_id: appr.booking_id,
    source_channel: 'telegram:staff',
    input_summary: `${appr.action_type} ${decision}`.slice(0, 500),
    output_summary: JSON.stringify(result).slice(0, 500),
    status: 'success',
    metadata: {
      phase: '2.4A',
      approval_id: approvalId,
      task_id: appr.task_id,
      telegram_user_id: userId,
      idempotent: !!result.idempotent,
    },
  });

  await tgAnswer.call(this, callbackId, `${appr.action_type}: ${rpcDecision}`, false, simulated);

  return {
    ok: true,
    idempotent: !!result.idempotent,
    approval_id: approvalId,
    action_type: appr.action_type,
    decision: rpcDecision,
    booking_id: appr.booking_id,
    lifecycle_status: result.lifecycle_status,
  };
}

// --- Main ---
const raw = $input.first().json;
const parsed = parseInput(raw);
if (parsed.error) {
  return [{ json: { ok: false, error: parsed.error, phase: '2.4A' } }];
}

const authBody = raw.body ?? raw;
const auth = verifyFinancialWebhookAuth(raw, authBody);
if (!auth.ok && (parsed.simulated || authBody.approval_id || authBody.simulate)) {
  await logDenied.call(this, parsed.userId || 'unknown', 'approval_webhook', auth.error);
  return [{ json: { ok: false, error: auth.error, phase: '2.4A', denied: true, policy: 'manual_only' } }];
}

const { userId, callbackData, callbackId, simulated } = parsed;
let { approvalId, decision, reason } = parsed;

const allowlist = await loadAllowlist.call(this);
const authorized = allowlist.includes(userId);

const parts = (callbackData || '').split(':');
// bk:appr:{approvalId}:approve | bk:appr:{approvalId}:deny
if (!approvalId && parts[0] === 'bk' && parts[1] === 'appr' && parts[2]) {
  approvalId = parts[2];
  decision = parts[3] === 'deny' ? 'deny' : 'approve';
}

if (!approvalId || !decision) {
  return [{ json: { ok: false, error: 'missing_approval_or_decision', phase: '2.4A', callback_data: callbackData } }];
}

if (!authorized) {
  await logDenied.call(this, userId, callbackData || `${approvalId}:${decision}`, 'unauthorized_telegram_user');
  await tgAnswer.call(this, callbackId, 'Access denied.', true, simulated);
  return [{ json: { ok: false, error: 'unauthorized', phase: '2.4A', denied: true, simulated } }];
}

const result = await handleApprovalDecision.call(this, {
  approvalId,
  decision,
  userId,
  callbackId,
  reason,
  simulated,
});

return [{ json: { ...result, phase: '2.4A', simulated } }];
