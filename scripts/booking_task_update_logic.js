// Phase 2.4A — Booking Task Update (Telegram callback + test webhook)
// Deterministic — NO AI. Staff allowlist required for writes.

const SB = String($env.SUPABASE_URL || 'https://xfibcjhshpmqkrhlpsoa.supabase.co').replace(/\/$/, '');
const KEY = $env.SUPABASE_KEY || $env.SUPABASE_SERVICE_ROLE_KEY;
if (!KEY) throw new Error('SUPABASE_KEY required');

const HDR = {
  apikey: KEY,
  Authorization: `Bearer ${KEY}`,
  'Content-Type': 'application/json',
  Prefer: 'return=representation',
};

const ALLOWED = {
  pending: ['requested', 'failed', 'skipped'],
  requested: ['awaiting_confirmation', 'confirmed', 'failed', 'skipped'],
  awaiting_confirmation: ['confirmed', 'failed', 'skipped'],
  confirmed: [],
  failed: ['requested', 'skipped'],
  skipped: [],
};

async function sb(method, path, body, extra = {}) {
  const opts = { method, url: `${SB}/rest/v1/${path}`, headers: { ...HDR, ...extra }, json: true };
  if (body !== undefined) opts.body = body;
  return await this.helpers.httpRequest(opts);
}

async function sbRpc(fn, args) {
  const rows = await sb.call(this, 'POST', `rpc/${fn}`, args);
  let val = Array.isArray(rows) ? rows[0] : rows;
  if (typeof val === 'string') {
    try { val = JSON.parse(val); } catch (_e) { /* keep string */ }
  }
  return val;
}

async function loadAllowlist() {
  const rows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_staff_telegram_allowlist&select=config_value');
  return (rows[0]?.config_value?.user_ids || []).map(String);
}

async function loadSkipPolicy() {
  const rows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.booking_task_skip_policy&select=config_value');
  return rows[0]?.config_value || {};
}

function isSensitiveRequiredTask(task, policy) {
  if (task.is_required === false) return false;
  const sensitive = policy.sensitive_required_types || ['hotel', 'airport_transfer', 'intercity_transfer', 'train', 'guide'];
  return sensitive.includes(task.task_type);
}

async function idempotent(key, meta) {
  const hit = await sb.call(this, 'GET', `booking_telegram_idempotency?idempotency_key=eq.${encodeURIComponent(key)}&select=idempotency_key`);
  if (hit.length) return true;
  try {
    await sb.call(this, 'POST', 'booking_telegram_idempotency', {
      idempotency_key: key,
      action_type: meta.action_type || 'callback',
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

async function logTask(taskId, bookingId, field, oldVal, newVal, changedBy, reason, metadata) {
  await sb.call(this, 'POST', 'booking_task_status_log', {
    task_id: taskId,
    booking_id: bookingId,
    field_changed: field,
    old_value: oldVal != null ? String(oldVal) : null,
    new_value: newVal != null ? String(newVal) : null,
    changed_by: changedBy,
    reason,
    metadata: { source: 'telegram', ...(metadata || {}) },
  });
}

async function logDenied(userId, action, reason) {
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'task_update_denied',
    source_channel: 'telegram:staff',
    input_summary: `user=${userId} action=${action}`.slice(0, 500),
    output_summary: reason,
    status: 'failed',
    metadata: { phase: '2.4A', telegram_user_id: userId, denied: true },
  });
}

function respondJson(payload, simulated) {
  return [{ json: { ...payload, simulated: !!simulated } }];
}

function normalizeRef(ref) {
  return ref != null ? String(ref).trim() : '';
}

function evaluateConfirmationRefConflict(task, confirmationRef, confirmData) {
  const existing = normalizeRef(task.confirmation_ref);
  const incoming = normalizeRef(confirmationRef);
  if (!existing || task.status !== 'confirmed') return { action: 'proceed' };
  if (incoming && incoming === existing) {
    return { action: 'idempotent_replay', confirmation_ref: existing };
  }
  if (incoming && incoming !== existing) {
    const reason = normalizeRef(confirmData.override_reason);
    if (confirmData.override_confirmation_ref === true) {
      if (!reason) {
        return {
          action: 'reject',
          existing_confirmation_ref: existing,
          attempted_confirmation_ref: incoming,
          override_missing_reason: true,
        };
      }
      return {
        action: 'override',
        old_confirmation_ref: existing,
        new_confirmation_ref: incoming,
        override_reason: reason,
      };
    }
    return {
      action: 'reject',
      existing_confirmation_ref: existing,
      attempted_confirmation_ref: incoming,
    };
  }
  return { action: 'proceed' };
}

async function logConfirmationRefConflict(task, userId, conflict, metadata) {
  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'confirmation_ref_conflict',
    booking_id: task.booking_id,
    source_channel: 'telegram:staff',
    input_summary: `${task.task_key} ref conflict`.slice(0, 500),
    output_summary: `${conflict.existing_confirmation_ref} vs ${conflict.attempted_confirmation_ref}`.slice(0, 500),
    status: 'failed',
    metadata: {
      phase: '2.6',
      task_id: task.task_id,
      telegram_user_id: userId,
      ...(metadata || {}),
      ...conflict,
    },
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
    // ignore invalid callback ids in test/simulated mode
  }
}

async function tgSend(chatId, text, replyMarkup, simulated = false) {
  if (simulated) return { ok: true, delivery: 'skipped_simulated' };
  const token = $env.TELEGRAM_BOT_TOKEN || $env.LAILA_TELEGRAM_BOT_TOKEN;
  if (!token) throw new Error('TELEGRAM_BOT_TOKEN required');
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  try {
    return await this.helpers.httpRequest({
      method: 'POST',
      url,
      body: { chat_id: chatId, text, parse_mode: 'Markdown', reply_markup: replyMarkup },
      json: true,
    });
  } catch (e) {
    const msg = String(e.message || e);
    if (msg.includes('400') || msg.toLowerCase().includes('parse')) {
      return await this.helpers.httpRequest({
        method: 'POST',
        url,
        body: { chat_id: chatId, text: String(text || '').replace(/[*_`[\]]/g, ''), reply_markup: replyMarkup },
        json: true,
      });
    }
    throw e;
  }
}

function parseInput(raw) {
  const payload = raw.body ?? raw;
  // Test webhook simulation
  if (payload.simulate || payload.callback_data) {
    return {
      userId: String(payload.telegram_user_id || ''),
      callbackData: payload.callback_data || '',
      callbackId: payload.callback_query_id || `sim_${Date.now()}`,
      chatId: payload.chat_id || payload.telegram_chat_id,
      confirmData: payload.confirm_data || {},
      simulated: true,
    };
  }
  const upd = payload;
  const cb = upd.callback_query;
  if (!cb) return { error: 'not_a_callback' };
  return {
    userId: String(cb.from?.id || ''),
    callbackData: cb.data || '',
    callbackId: cb.id,
    chatId: cb.message?.chat?.id,
    confirmData: {},
    simulated: false,
  };
}

async function handleView(bookingId, chatId) {
  const rows = await sb.call(this, 'GET', `bookings?booking_id=eq.${encodeURIComponent(bookingId)}&select=booking_id,client_name,destination,arrival_date,departure_date,guest_count,quote_ref,lifecycle_status,payment_status`);
  if (!rows.length) return 'Booking not found.';
  const b = rows[0];
  return [
    `*Booking ${b.booking_id}*`,
    `Status: \`${b.lifecycle_status}\` / \`${b.payment_status}\``,
    `Guest: ${b.client_name || 'Guest'}`,
    `Destination: ${b.destination}`,
    `Dates: ${b.arrival_date} → ${b.departure_date}`,
    `Pax: ${b.guest_count} · Quote: ${b.quote_ref}`,
  ].join('\n');
}

function parseThresholdPct(cfgVal) {
  if (cfgVal == null) return NaN;
  if (typeof cfgVal === 'number') return cfgVal;
  if (typeof cfgVal === 'object' && cfgVal.value != null) return Number(cfgVal.value);
  return Number(cfgVal);
}

async function evaluateSupplierCostVariance(task, newCost, staffTag) {
  const quoted = Number(task.quoted_cost_usd || (task.metadata && task.metadata.quoted_cost) || 0);
  if (quoted <= 0) {
    await sb.call(this, 'PATCH', `booking_tasks?task_id=eq.${encodeURIComponent(task.task_id)}`, {
      metadata: { ...(task.metadata || {}), cost_review_required: true },
    });
    return { action: 'cost_review_required', baseline_available: false, task_id: task.task_id };
  }

  const thresholdRows = await sb.call(this, 'GET', 'arcadia_system_config?config_key=eq.supplier_price_change_threshold_pct&select=config_value');
  const thresholdPct = parseThresholdPct(thresholdRows[0] && thresholdRows[0].config_value);
  if (Number.isNaN(thresholdPct)) {
    throw new Error('supplier_price_change_threshold_pct not configured');
  }

  const pctChange = ((newCost - quoted) / quoted) * 100;
  if (pctChange <= thresholdPct) {
    return { action: 'within_threshold', approval_required: false, pct_change: pctChange, threshold_pct: thresholdPct };
  }

  const idemKey = `supplier_price_change:${task.task_id}:${Math.round(newCost * 100) / 100}`;
  const existing = await sb.call(this, 'GET', `human_approval_queue?action_type=eq.supplier_price_change&booking_id=eq.${encodeURIComponent(task.booking_id)}&idempotency_key=eq.${encodeURIComponent(idemKey)}&select=approval_id,status&limit=1`);
  if (existing.length) {
    return { action: 'approval_exists', idempotent: true, approval_id: existing[0].approval_id, status: existing[0].status };
  }

  const inserted = await sb.call(this, 'POST', 'human_approval_queue', {
    action_type: 'supplier_price_change',
    booking_id: task.booking_id,
    task_id: task.task_id,
    idempotency_key: idemKey,
    requested_by_agent: staffTag,
    reason: `Supplier cost +${pctChange.toFixed(1)}% exceeds threshold ${thresholdPct}%`,
    status: 'pending',
    payload: {
      task_id: task.task_id,
      task_key: task.task_key,
      task_type: task.task_type,
      quoted_cost_usd: quoted,
      proposed_cost_usd: newCost,
      old_cost_usd: task.supplier_cost_usd,
      pct_change: pctChange,
      threshold_pct: thresholdPct,
    },
  });

  await sb.call(this, 'PATCH', `booking_tasks?task_id=eq.${encodeURIComponent(task.task_id)}`, {
    metadata: {
      ...(task.metadata || {}),
      pending_supplier_price_change: true,
      proposed_supplier_cost_usd: newCost,
      quoted_cost_usd: quoted,
    },
  });

  return {
    action: 'approval_created',
    idempotent: false,
    approval_id: inserted[0].approval_id,
    pct_change: pctChange,
    threshold_pct: thresholdPct,
  };
}

async function handleTasksList(bookingId, chatId, simulated = false) {
  const tasks = await sb.call(this, 'GET', `booking_tasks?booking_id=eq.${encodeURIComponent(bookingId)}&select=task_id,task_key,task_type,status,city,is_required&order=task_key`);
  const open = tasks.filter(t => ['pending', 'requested', 'awaiting_confirmation'].includes(t.status));
  const lines = open.slice(0, 8).map(t => `• \`${t.task_key}\` [${t.status}]${t.is_required === false ? ' (opt)' : ''}`);
  const keyboard = open.slice(0, 5).flatMap(t => ([
    [
      { text: `📂 ${t.task_key.split(':').slice(0, 2).join(':')}`, callback_data: `bk:task:${t.task_id}:open` },
      { text: '→ req', callback_data: `bk:task:${t.task_id}:to:requested` },
    ],
  ]));
  if (open.length > 5) keyboard.push([{ text: `+${open.length - 5} more tasks`, callback_data: `bk:tasks:${bookingId}` }]);
  await tgSend.call(this, chatId, [`*Pending tasks* (${open.length})`, ...lines].join('\n'), { inline_keyboard: keyboard }, simulated);
  return { listed: open.length };
}

async function callDraftWebhook(taskId, requestedBy) {
  const n8nBase = String($env.N8N_PUBLIC_URL || 'https://n8n.arcadia-tour.cloud').replace(/\/$/, '');
  return await this.helpers.httpRequest({
    method: 'POST',
    url: `${n8nBase}/webhook/booking-supplier-draft`,
    headers: { 'Content-Type': 'application/json' },
    body: { task_id: taskId, requested_by: requestedBy },
    json: true,
  });
}

async function handleTaskOpen(taskId, chatId, simulated = false) {
  const tasks = await sb.call(this, 'GET', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}&select=*`);
  if (!tasks.length) return { ok: false, error: 'task_not_found' };
  const t = tasks[0];
  const drafts = await sb.call(this, 'GET', `booking_supplier_drafts?task_id=eq.${encodeURIComponent(taskId)}&status=neq.superseded&order=created_at.desc&limit=1&select=draft_id,status,sent_manually_at`);
  const d = drafts[0];
  const text = [
    `*Task* \`${t.task_key}\``,
    `Type: ${t.task_type} · City: ${t.city || '—'}`,
    `Status: ${t.status}`,
    `Supplier: ${t.supplier_name || '—'}`,
    `Confirmation: \`${t.confirmation_ref || '—'}\``,
    d ? `Latest draft: ${d.status}${d.sent_manually_at ? ' (sent)' : ''}` : 'No draft yet',
  ].join('\n');
  const keyboard = [
    [{ text: '📝 Generate draft', callback_data: `bk:task:${taskId}:draft` }],
  ];
  if (d && d.draft_id) {
    keyboard.push([{ text: '👁 Preview draft', callback_data: `bk:draft:${d.draft_id}:preview` }]);
    if (d.status !== 'sent_manually') {
      keyboard.push([{ text: '✅ Mark sent (manual)', callback_data: `bk:draft:${d.draft_id}:mark_sent` }]);
    }
  }
  keyboard.push([
    { text: '→ requested', callback_data: `bk:task:${taskId}:to:requested` },
    { text: '→ awaiting', callback_data: `bk:task:${taskId}:to:awaiting_confirmation` },
  ]);
  keyboard.push([
    { text: '⏳ Waiting', callback_data: `bk:task:${taskId}:resp:waiting` },
    { text: '❌ Unavailable', callback_data: `bk:task:${taskId}:resp:unavailable` },
  ]);
  keyboard.push([
    { text: '❓ Needs info', callback_data: `bk:task:${taskId}:resp:needs_information` },
    { text: '🔄 Alternative', callback_data: `bk:task:${taskId}:resp:alternative_offered` },
  ]);
  await tgSend.call(this, chatId, text, { inline_keyboard: keyboard }, simulated);
  return {
    ok: true,
    action: 'open',
    task_id: taskId,
    task_key: t.task_key,
    status: t.status,
    confirmation_ref: t.confirmation_ref || null,
  };
}

async function handleGenerateDraft({ taskId, userId, callbackId, chatId, simulated }) {
  const staffTag = `staff:${userId}`;
  const idemKey = `cb:${callbackId}:draft`;
  if (await idempotent.call(this, idemKey, { action_type: 'generate_draft', task_id: taskId })) {
    const drafts = await sb.call(this, 'GET', `booking_supplier_drafts?task_id=eq.${encodeURIComponent(taskId)}&order=created_at.desc&limit=1&select=draft_id,status,draft_text`);
    if (drafts.length) {
      return { ok: true, idempotent: true, draft_id: drafts[0].draft_id, status: drafts[0].status, phase: '2.6' };
    }
  }
  const result = await callDraftWebhook.call(this, taskId, staffTag);
  if (!result.ok) {
    await tgAnswer.call(this, callbackId, result.error || 'Draft failed', true, simulated);
    return { ...result, phase: '2.6' };
  }
  const preview = (result.draft_text || '').slice(0, 3500);
  const statusLine = result.status === 'needs_information' ? '⚠️ *needs_information*' : '📋 *draft ready*';
  await tgSend.call(this, chatId, [
    statusLine,
    `Task draft · \`${result.facts?.task_key || taskId}\``,
    '',
    '```',
    preview,
    '```',
    '',
    '_NOT sent — staff must send manually_',
  ].join('\n'), {
    inline_keyboard: [[
      { text: '✅ Mark sent (manual)', callback_data: `bk:draft:${result.draft_id}:mark_sent` },
    ]],
  }, simulated);
  await tgAnswer.call(this, callbackId, result.idempotent ? 'Draft exists' : 'Draft generated', false, simulated);
  return { ok: true, action: 'draft', ...result, phase: '2.6', auto_send: false };
}

async function handleDraftPreview(draftId, chatId, callbackId, simulated) {
  const rows = await sb.call(this, 'GET', `booking_supplier_drafts?draft_id=eq.${encodeURIComponent(draftId)}&select=*`);
  if (!rows.length) return { ok: false, error: 'draft_not_found' };
  const d = rows[0];
  await tgSend.call(this, chatId, [`*Draft* ${d.status}`, '```', (d.draft_text || '').slice(0, 3500), '```'].join('\n'), {
    inline_keyboard: d.status !== 'sent_manually' ? [[{ text: '✅ Mark sent (manual)', callback_data: `bk:draft:${draftId}:mark_sent` }]] : undefined,
  }, simulated);
  await sb.call(this, 'PATCH', `booking_supplier_drafts?draft_id=eq.${encodeURIComponent(draftId)}`, { status: d.status === 'needs_information' ? 'needs_information' : 'previewed' });
  await tgAnswer.call(this, callbackId, 'Draft preview');
  return { ok: true, action: 'preview', draft_id: draftId, phase: '2.6' };
}

async function handleDraftMarkSent({ draftId, userId, callbackId, chatId, simulated }) {
  const staffTag = `staff:${userId}`;
  const idemKey = `cb:${callbackId}:mark_sent:${draftId}`;
  if (await idempotent.call(this, idemKey, { action_type: 'mark_sent', draft_id: draftId })) {
    return { ok: true, idempotent: true, action: 'mark_sent', draft_id: draftId, phase: '2.6' };
  }
  const rows = await sb.call(this, 'GET', `booking_supplier_drafts?draft_id=eq.${encodeURIComponent(draftId)}&select=*`);
  if (!rows.length) return { ok: false, error: 'draft_not_found' };
  const draft = rows[0];
  if (draft.status === 'sent_manually') {
    return { ok: true, idempotent: true, draft_id: draftId, phase: '2.6' };
  }

  await sb.call(this, 'PATCH', `booking_supplier_drafts?draft_id=eq.${encodeURIComponent(draftId)}`, {
    status: 'sent_manually',
    sent_manually_at: new Date().toISOString(),
    sent_manually_by: staffTag,
  });

  const taskId = draft.task_id;
  const tasks = await sb.call(this, 'GET', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}&select=*`);
  if (tasks.length) {
    const task = tasks[0];
    if (task.status === 'pending') {
      await handleTaskTransition.call(this, {
        taskId,
        toStatus: 'requested',
        userId,
        callbackId: `internal_${callbackId}`,
        chatId,
        confirmData: { notes: 'supplier_request_sent_manually' },
        simulated: true,
      });
    } else if (task.status === 'requested') {
      // already requested — no-op
    }
    await sb.call(this, 'PATCH', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}`, {
      metadata: {
        ...(task.metadata || {}),
        supplier_request_sent_manually: true,
        supplier_draft_id: draftId,
      },
    });
  }

  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'supplier_request_sent_manually',
    booking_id: draft.booking_id,
    source_channel: 'telegram:staff',
    input_summary: `draft ${draftId}`.slice(0, 500),
    output_summary: `task ${taskId} marked sent by ${staffTag}`,
    status: 'success',
    metadata: { phase: '2.6', task_id: taskId, draft_id: draftId, auto_send: false },
  });

  await tgAnswer.call(this, callbackId, 'Marked sent (manual)', false, simulated);
  return { ok: true, action: 'mark_sent', draft_id: draftId, task_id: taskId, phase: '2.6', auto_send: false };
}

async function handleSupplierResponse({ taskId, responseType, userId, confirmData, callbackId, simulated }) {
  const staffTag = `staff:${userId}`;
  const confirmationRef = confirmData.confirmation_ref || null;
  const supplierCost = confirmData.supplier_cost_usd != null ? Number(confirmData.supplier_cost_usd) : null;
  const notes = confirmData.notes || null;
  const idemKey = confirmData.idempotency_key || `supplier_resp:${taskId}:${responseType}:${confirmationRef || 'noref'}`;

  const tasks = await sb.call(this, 'GET', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}&select=*`);
  if (!tasks.length) return { ok: false, error: 'task_not_found' };
  const task = tasks[0];

  if (responseType === 'confirmed' && confirmationRef) {
    const conflict = evaluateConfirmationRefConflict(task, confirmationRef, confirmData);
    if (conflict.action === 'idempotent_replay') {
      await tgAnswer.call(this, callbackId, 'Already confirmed.', false, simulated);
      return {
        ok: true,
        idempotent: true,
        action: 'supplier_response',
        task_id: taskId,
        response_type: responseType,
        status: 'confirmed',
        confirmation_ref: conflict.confirmation_ref,
        phase: '2.6',
      };
    }
    if (conflict.action === 'reject') {
      await logConfirmationRefConflict.call(this, task, userId, conflict, { source: 'supplier_response' });
      await tgAnswer.call(this, callbackId, 'Confirmation ref conflict.', true, simulated);
      return {
        ok: false,
        error: 'confirmation_ref_conflict',
        task_id: taskId,
        existing_confirmation_ref: conflict.existing_confirmation_ref,
        attempted_confirmation_ref: conflict.attempted_confirmation_ref,
        phase: '2.6',
      };
    }
    if (conflict.action === 'override') {
      const overrideResult = await sbRpc.call(this, 'override_task_confirmation_ref', {
        p_task_id: taskId,
        p_new_ref: conflict.new_confirmation_ref,
        p_reason: conflict.override_reason,
        p_recorded_by: staffTag,
      });
      await sb.call(this, 'POST', 'agent_actions', {
        agent_name: 'booking',
        action_type: 'confirmation_ref_override',
        booking_id: task.booking_id,
        source_channel: 'telegram:staff',
        input_summary: `${task.task_key} override`.slice(0, 500),
        output_summary: `${conflict.old_confirmation_ref} -> ${conflict.new_confirmation_ref}`.slice(0, 500),
        status: 'success',
        metadata: {
          phase: '2.6',
          task_id: taskId,
          telegram_user_id: userId,
          reason: conflict.override_reason,
          override_result: overrideResult,
        },
      });
      await tgAnswer.call(this, callbackId, 'Confirmation ref corrected.', false, simulated);
      return {
        ok: true,
        action: 'confirmation_ref_override',
        task_id: taskId,
        response_type: responseType,
        status: 'confirmed',
        confirmation_ref: conflict.new_confirmation_ref,
        old_confirmation_ref: conflict.old_confirmation_ref,
        override: true,
        phase: '2.6',
      };
    }
  }

  const existing = await sb.call(this, 'GET', `booking_supplier_responses?idempotency_key=eq.${encodeURIComponent(idemKey)}&select=response_id`);
  if (existing.length) {
    return { ok: true, idempotent: true, response_id: existing[0].response_id, phase: '2.6' };
  }

  await sb.call(this, 'POST', 'booking_supplier_responses', {
    task_id: taskId,
    booking_id: task.booking_id,
    response_type: responseType,
    confirmation_ref: confirmationRef,
    supplier_quoted_cost_usd: supplierCost,
    notes,
    recorded_by: staffTag,
    idempotency_key: idemKey,
    metadata: { phase: '2.6', source: 'telegram' },
  });

  const metaPatch = {
    ...(task.metadata || {}),
    supplier_response_type: responseType,
    supplier_response_at: new Date().toISOString(),
  };

  let newStatus = task.status;
  if (responseType === 'confirmed' && confirmationRef) {
    const transResult = await handleTaskTransition.call(this, {
      taskId,
      toStatus: 'confirmed',
      userId,
      callbackId: `internal_${callbackId}`,
      chatId: null,
      confirmData: { confirmation_ref: confirmationRef, supplier_cost_usd: supplierCost, notes },
      simulated: true,
    });
    if (transResult.ok && !transResult.blocked && !transResult.error) {
      newStatus = 'confirmed';
    } else if (transResult.error === 'confirmation_ref_conflict') {
      return transResult;
    } else if (transResult.idempotent) {
      newStatus = 'confirmed';
    } else {
      await sb.call(this, 'PATCH', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}`, { metadata: metaPatch });
      newStatus = task.status;
    }
  } else if (responseType === 'unavailable') {
    if (['pending', 'requested', 'awaiting_confirmation'].includes(task.status)) {
      await handleTaskTransition.call(this, {
        taskId, toStatus: 'failed', userId, callbackId: `internal_${callbackId}`, chatId: null,
        confirmData: { notes: notes || 'supplier_unavailable' }, simulated: true,
      });
      newStatus = 'failed';
    }
  } else if (responseType === 'waiting' || responseType === 'needs_information') {
    if (task.status === 'pending') {
      await handleTaskTransition.call(this, {
        taskId, toStatus: 'awaiting_confirmation', userId, callbackId: `internal_${callbackId}`, chatId: null,
        confirmData: { notes }, simulated: true,
      });
      newStatus = 'awaiting_confirmation';
    }
    await sb.call(this, 'PATCH', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}`, { metadata: metaPatch });
  } else {
    await sb.call(this, 'PATCH', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}`, { metadata: metaPatch });
  }

  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'supplier_response_recorded',
    booking_id: task.booking_id,
    source_channel: 'telegram:staff',
    input_summary: `${task.task_key} ${responseType}`.slice(0, 500),
    output_summary: confirmationRef || responseType,
    status: 'success',
    metadata: { phase: '2.6', task_id: taskId, response_type: responseType, auto_send: false },
  });

  await tgAnswer.call(this, callbackId, `Recorded: ${responseType}`, false, simulated);
  return { ok: true, action: 'supplier_response', task_id: taskId, response_type: responseType, status: newStatus, phase: '2.6' };
}

async function handleTaskTransition({ taskId, toStatus, userId, callbackId, chatId, confirmData, simulated }) {
  const staffTag = `staff:${userId}`;

  const idemKey = `cb:${callbackId}`;
  if (await idempotent.call(this, idemKey, { action_type: 'task_transition', task_id: taskId, to: toStatus })) {
    const existing = await sb.call(this, 'GET', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}&select=task_key,status,booking_id`);
    const t = existing[0] || {};
    return { ok: true, idempotent: true, task_id: taskId, status: t.status, booking_id: t.booking_id, task_key: t.task_key };
  }

  const tasks = await sb.call(this, 'GET', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}&select=*`);
  if (!tasks.length) return { ok: false, error: 'task_not_found' };
  const task = tasks[0];
  const fromStatus = task.status;

  if (!(ALLOWED[fromStatus] || []).includes(toStatus)) {
    return { ok: false, error: 'transition_not_allowed', from: fromStatus, to: toStatus };
  }

  const skipPolicy = await loadSkipPolicy.call(this);

  if (toStatus === 'skipped' && isSensitiveRequiredTask(task, skipPolicy)) {
    const skipReason = confirmData.reason || confirmData.notes || 'unspecified';
    const skipResult = await sbRpc.call(this, 'request_required_task_skip', {
      p_task_id: taskId,
      p_requested_by: staffTag,
      p_skip_reason: skipReason,
      p_idempotency_key: `manual_override:skip:${taskId}:${skipReason}`,
    });
    await sb.call(this, 'POST', 'agent_actions', {
      agent_name: 'booking',
      action_type: 'task_skip_approval_requested',
      booking_id: task.booking_id,
      source_channel: 'telegram:staff',
      input_summary: `${task.task_key} skip:${skipReason}`.slice(0, 500),
      output_summary: JSON.stringify(skipResult).slice(0, 500),
      status: 'success',
      metadata: { phase: '2.4A', task_id: taskId, telegram_user_id: userId },
    });
    await tgAnswer.call(this, callbackId, 'Skip requires approval', true, simulated);
    return {
      ok: true,
      skip_blocked: true,
      approval_required: true,
      task_id: taskId,
      booking_id: task.booking_id,
      ...skipResult,
    };
  }

  const patch = { status: toStatus, updated_at: new Date().toISOString() };
  if (toStatus === 'requested') patch.requested_at = new Date().toISOString();
  if (toStatus === 'confirmed') {
    const incomingRef = normalizeRef(confirmData.confirmation_ref);
    const existingRef = normalizeRef(task.confirmation_ref);
    if (fromStatus === 'confirmed' && existingRef) {
      if (incomingRef && incomingRef === existingRef) {
        return {
          ok: true,
          idempotent: true,
          task_id: taskId,
          task_key: task.task_key,
          status: 'confirmed',
          confirmation_ref: existingRef,
          booking_id: task.booking_id,
        };
      }
      if (incomingRef && incomingRef !== existingRef) {
        const reason = normalizeRef(confirmData.override_reason);
        if (!(confirmData.override_confirmation_ref === true && reason)) {
          return {
            ok: false,
            error: 'confirmation_ref_conflict',
            task_id: taskId,
            booking_id: task.booking_id,
            existing_confirmation_ref: existingRef,
            attempted_confirmation_ref: incomingRef,
          };
        }
        const overrideResult = await sbRpc.call(this, 'override_task_confirmation_ref', {
          p_task_id: taskId,
          p_new_ref: incomingRef,
          p_reason: reason,
          p_recorded_by: staffTag,
        });
        return {
          ok: true,
          action: 'confirmation_ref_override',
          task_id: taskId,
          task_key: task.task_key,
          status: 'confirmed',
          confirmation_ref: incomingRef,
          old_confirmation_ref: existingRef,
          booking_id: task.booking_id,
          override: true,
          override_result: overrideResult,
        };
      }
    }
    patch.confirmed_at = new Date().toISOString();
    patch.confirmation_ref = incomingRef || existingRef || `REF-${Date.now()}`;
    if (confirmData.supplier_name || task.supplier_name) patch.supplier_name = confirmData.supplier_name || task.supplier_name;
    if (confirmData.notes) patch.notes = confirmData.notes;
    if (confirmData.supplier_cost_usd != null) {
      const newCost = Number(confirmData.supplier_cost_usd);
      const variance = await evaluateSupplierCostVariance.call(this, task, newCost, staffTag);
      if (variance.action === 'approval_created' || variance.action === 'approval_exists') {
        await sb.call(this, 'POST', 'agent_actions', {
          agent_name: 'booking',
          action_type: 'supplier_price_change_pending',
          booking_id: task.booking_id,
          source_channel: 'telegram:staff',
          input_summary: `${task.task_key} cost=${newCost}`.slice(0, 500),
          output_summary: JSON.stringify(variance).slice(0, 500),
          status: 'success',
          metadata: { phase: '2.4A', task_id: taskId, telegram_user_id: userId },
        }).catch(() => {});
        await tgAnswer.call(this, callbackId, 'Supplier cost approval required', true, simulated);
        return {
          ok: true,
          blocked: true,
          reason: 'supplier_price_change_approval_required',
          task_id: taskId,
          booking_id: task.booking_id,
          variance,
        };
      }
      if (variance.action === 'cost_review_required') {
        await tgAnswer.call(this, callbackId, 'Cost review required — no baseline', true, simulated);
        return { ok: true, blocked: true, reason: 'cost_review_required', task_id: taskId, booking_id: task.booking_id, variance };
      }
      if (variance.action === 'within_threshold' && newCost > 0) {
        patch.supplier_cost_usd = newCost;
      } else if (newCost > 0 && task.quoted_cost_usd == null && !(task.metadata && task.metadata.quoted_cost)) {
        patch.supplier_cost_usd = newCost;
      }
    }
  }
  if (toStatus === 'skipped') {
    patch.notes = confirmData.notes || confirmData.reason || 'skipped_by_staff';
  }

  const updated = await sb.call(this, 'PATCH', `booking_tasks?task_id=eq.${encodeURIComponent(taskId)}`, patch);
  const newTask = updated[0] || { ...task, ...patch };

  await logTask.call(this, taskId, task.booking_id, 'status', fromStatus, toStatus, staffTag, 'telegram_task_update', { callback_id: callbackId });

  const newLifecycle = await sbRpc.call(this, 'recompute_booking_lifecycle', { p_booking_id: task.booking_id });

  await sb.call(this, 'POST', 'agent_actions', {
    agent_name: 'booking',
    action_type: 'task_update',
    booking_id: task.booking_id,
    source_channel: 'telegram:staff',
    input_summary: `${task.task_key} ${fromStatus}->${toStatus}`.slice(0, 500),
    output_summary: `lifecycle=${newLifecycle}`,
    status: 'success',
    metadata: { phase: '2.4A', task_id: taskId, telegram_user_id: userId, idempotent: false },
  });

  await tgAnswer.call(this, callbackId, `${task.task_key}: ${fromStatus} → ${toStatus}`, false, simulated);

  return {
    ok: true,
    idempotent: false,
    simulated: !!simulated,
    task_id: taskId,
    task_key: task.task_key,
    from: fromStatus,
    to: toStatus,
    booking_id: task.booking_id,
    lifecycle_status: newLifecycle,
  };
}

// --- Main ---
const raw = $input.first().json;
const parsed = parseInput(raw);
if (parsed.error) {
  return respondJson({ ok: false, error: parsed.error, phase: '2.4A' }, true);
}

const { userId, callbackData, callbackId, chatId, confirmData, simulated } = parsed;
const allowlist = await loadAllowlist.call(this);
const authorized = allowlist.includes(userId);

const parts = (callbackData || '').split(':');
// bk:view:{bookingId} | bk:tasks:{bookingId} | bk:task:{taskId}:to:{status}

if (!authorized) {
  await logDenied.call(this, userId, callbackData, 'unauthorized_telegram_user');
  if (callbackId) await tgAnswer.call(this, callbackId, 'Access denied.', true);
  return respondJson({ ok: false, error: 'unauthorized', phase: '2.4A', denied: true }, simulated);
}

if (parts[0] !== 'bk') {
  return respondJson({ ok: false, error: 'unknown_callback', callback_data: callbackData, phase: '2.4A' }, simulated);
}

const viewIdem = `cb:${callbackId}:view`;
if (parts[1] === 'view' && parts[2]) {
  if (await idempotent.call(this, viewIdem, { action_type: 'view_booking', booking_id: parts[2] })) {
    await tgAnswer.call(this, callbackId, 'Already viewed.');
    return respondJson({ ok: true, idempotent: true, action: 'view', booking_id: parts[2], phase: '2.4A' }, simulated);
  }
  try {
    const text = await handleView.call(this, parts[2], chatId);
    await tgSend.call(this, chatId, text, undefined, simulated);
    await tgAnswer.call(this, callbackId, 'Booking loaded');
    return respondJson({ ok: true, action: 'view', booking_id: parts[2], phase: '2.4A' }, simulated);
  } catch (err) {
    return respondJson({
      ok: false,
      error: 'view_booking_failed',
      booking_id: parts[2],
      message: String(err.message || err),
      phase: '2.4A',
    }, simulated);
  }
}

if (parts[1] === 'tasks' && parts[2]) {
  const listIdem = `cb:${callbackId}:tasks`;
  if (await idempotent.call(this, listIdem, { action_type: 'list_tasks', booking_id: parts[2] })) {
    await tgAnswer.call(this, callbackId, 'Already listed.');
    return respondJson({ ok: true, idempotent: true, action: 'tasks', booking_id: parts[2], phase: '2.4A' }, simulated);
  }
  try {
    const result = await handleTasksList.call(this, parts[2], chatId, simulated);
    await tgAnswer.call(this, callbackId, `Tasks: ${result.listed}`);
    return respondJson({ ok: true, action: 'tasks', booking_id: parts[2], ...result, phase: '2.4A' }, simulated);
  } catch (err) {
    return respondJson({
      ok: false,
      error: 'tasks_list_failed',
      booking_id: parts[2],
      message: String(err.message || err),
      phase: '2.4A',
    }, simulated);
  }
}

if (parts[1] === 'task' && parts[2] && parts[3] === 'open') {
  const openIdem = `cb:${callbackId}:open`;
  if (await idempotent.call(this, openIdem, { action_type: 'open_task', task_id: parts[2] })) {
    await tgAnswer.call(this, callbackId, 'Already opened.');
    return respondJson({ ok: true, idempotent: true, action: 'open', task_id: parts[2], phase: '2.6' }, simulated);
  }
  try {
    const result = await handleTaskOpen.call(this, parts[2], chatId, simulated);
    await tgAnswer.call(this, callbackId, 'Task opened');
    return respondJson({ ...result, phase: '2.6' }, simulated);
  } catch (err) {
    return respondJson({
      ok: false,
      error: 'open_task_failed',
      task_id: parts[2],
      message: String(err.message || err),
      phase: '2.6',
    }, simulated);
  }
}

if (parts[1] === 'task' && parts[2] && parts[3] === 'draft') {
  try {
    const result = await handleGenerateDraft.call(this, {
      taskId: parts[2], userId, callbackId, chatId, simulated,
    });
    return respondJson(result, simulated);
  } catch (err) {
    return respondJson({ ok: false, error: 'draft_exception', message: String(err.message || err), phase: '2.6' }, simulated);
  }
}

if (parts[1] === 'task' && parts[2] && parts[3] === 'resp' && parts[4]) {
  try {
    const result = await handleSupplierResponse.call(this, {
      taskId: parts[2],
      responseType: parts[4],
      userId,
      confirmData,
      callbackId,
      simulated,
    });
    return respondJson(result, simulated);
  } catch (err) {
    return respondJson({ ok: false, error: 'supplier_response_exception', message: String(err.message || err), phase: '2.6' }, simulated);
  }
}

if (parts[1] === 'draft' && parts[2] && parts[3] === 'preview') {
  const result = await handleDraftPreview.call(this, parts[2], chatId, callbackId, simulated);
  return respondJson(result, simulated);
}

if (parts[1] === 'draft' && parts[2] && parts[3] === 'mark_sent') {
  try {
    const result = await handleDraftMarkSent.call(this, {
      draftId: parts[2], userId, callbackId, chatId, simulated,
    });
    return respondJson(result, simulated);
  } catch (err) {
    return respondJson({ ok: false, error: 'mark_sent_exception', message: String(err.message || err), phase: '2.6' }, simulated);
  }
}

if (parts[1] === 'task' && parts[2] && parts[3] === 'to' && parts[4]) {
  try {
    const result = await handleTaskTransition.call(this, {
      taskId: parts[2],
      toStatus: parts[4],
      userId,
      callbackId,
      chatId,
      confirmData,
      simulated,
    });
    return respondJson({ ...result, phase: '2.6' }, simulated);
  } catch (err) {
    const msg = String(err.message || err);
    await sb.call(this, 'POST', 'agent_actions', {
      agent_name: 'booking',
      action_type: 'task_update_error',
      source_channel: 'telegram:staff',
      input_summary: callbackData.slice(0, 500),
      output_summary: msg.slice(0, 500),
      status: 'failed',
      metadata: { phase: '2.6', telegram_user_id: userId },
    }).catch(() => {});
    return respondJson({ ok: false, error: 'task_update_exception', message: msg, phase: '2.6' }, simulated);
  }
}

return respondJson({ ok: false, error: 'invalid_callback', callback_data: callbackData, phase: '2.6' }, simulated);
