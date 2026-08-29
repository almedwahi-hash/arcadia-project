// Shared auth for Booking Agent financial mutation webhooks (Phase 2.4A+).
// MANUAL-ONLY POLICY: these endpoints RECORD/AUDIT — they never execute money movement.

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
  // Legacy: allowlist-only when secret env not configured (log once per request via caller)
  return { ok: true, method: 'allowlist_only' };
}
