// Shared helpers for Phase 2.2+ Booking Agent workflows
// eslint-disable-next-line no-unused-vars

function sbEnv() {
  const SB = String($env.SUPABASE_URL || 'https://xfibcjhshpmqkrhlpsoa.supabase.co').replace(/\/$/, '');
  const KEY = $env.SUPABASE_KEY || $env.SUPABASE_SERVICE_ROLE_KEY;
  if (!KEY) throw new Error('n8n env SUPABASE_KEY (service role) required');
  return {
    SB,
    KEY,
    HDR: {
      apikey: KEY,
      Authorization: `Bearer ${KEY}`,
      'Content-Type': 'application/json',
      Prefer: 'return=representation',
    },
  };
}

async function sbRequest(ctx, method, path, body, extraHeaders = {}) {
  const { SB, HDR } = sbEnv();
  const opts = {
    method,
    url: `${SB}/rest/v1/${path}`,
    headers: { ...HDR, ...extraHeaders },
    json: true,
  };
  if (body !== undefined) opts.body = body;
  return await ctx.helpers.httpRequest(opts);
}

async function sbRpc(ctx, fn, args) {
  const rows = await sbRequest(ctx, 'POST', `rpc/${fn}`, args);
  return Array.isArray(rows) ? rows[0] : rows;
}

async function loadConfig(ctx, key) {
  const rows = await sbRequest(ctx, 'GET', `arcadia_system_config?config_key=eq.${encodeURIComponent(key)}&select=config_value`);
  return rows[0]?.config_value || {};
}

async function loadStaffAllowlist(ctx) {
  const cfg = await loadConfig(ctx, 'booking_staff_telegram_allowlist');
  return (cfg.user_ids || []).map(String);
}

async function loadTelegramOps(ctx) {
  return await loadConfig(ctx, 'telegram_booking_ops');
}

const ALLOWED_TRANSITIONS = {
  pending: ['requested', 'failed', 'skipped'],
  requested: ['awaiting_confirmation', 'failed', 'skipped'],
  awaiting_confirmation: ['confirmed', 'failed', 'skipped'],
  confirmed: [],
  failed: ['requested', 'skipped'],
  skipped: [],
  cancelled: [],
};

function isTransitionAllowed(from, to) {
  return (ALLOWED_TRANSITIONS[from] || []).includes(to);
}

function taskIsRequired(task) {
  return task.is_required !== false;
}

async function logTaskChange(ctx, { taskId, bookingId, field, oldVal, newVal, changedBy, reason, metadata }) {
  await sbRequest(ctx, 'POST', 'booking_task_status_log', {
    task_id: taskId,
    booking_id: bookingId,
    field_changed: field,
    old_value: oldVal != null ? String(oldVal) : null,
    new_value: newVal != null ? String(newVal) : null,
    changed_by: changedBy,
    reason,
    metadata: metadata || {},
  });
}

async function logAgentAction(ctx, payload) {
  await sbRequest(ctx, 'POST', 'agent_actions', payload);
}

async function checkIdempotency(ctx, key, meta) {
  const existing = await sbRequest(ctx, 'GET', `booking_telegram_idempotency?idempotency_key=eq.${encodeURIComponent(key)}&select=idempotency_key`);
  if (existing.length) return { duplicate: true, key };
  try {
    await sbRequest(ctx, 'POST', 'booking_telegram_idempotency', {
      idempotency_key: key,
      action_type: meta.action_type || 'telegram_callback',
      booking_id: meta.booking_id || null,
      task_id: meta.task_id || null,
      metadata: meta,
    });
  } catch (e) {
    if (String(e.message || e).includes('23505')) return { duplicate: true, key };
    throw e;
  }
  return { duplicate: false, key };
}

async function recomputeLifecycle(ctx, bookingId) {
  return await sbRpc(ctx, 'recompute_booking_lifecycle', { p_booking_id: bookingId });
}

function pendingTaskSummary(tasks) {
  const pending = tasks.filter(t => ['pending', 'requested', 'awaiting_confirmation'].includes(t.status));
  const byType = {};
  for (const t of pending) {
    byType[t.task_type] = (byType[t.task_type] || 0) + 1;
  }
  return { count: pending.length, byType };
}

module.exports = {
  sbEnv,
  sbRequest,
  sbRpc,
  loadConfig,
  loadStaffAllowlist,
  loadTelegramOps,
  ALLOWED_TRANSITIONS,
  isTransitionAllowed,
  taskIsRequired,
  logTaskChange,
  logAgentAction,
  checkIdempotency,
  recomputeLifecycle,
  pendingTaskSummary,
};
