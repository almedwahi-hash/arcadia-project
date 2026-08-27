# Evolution API — Recovery Report
**التاريخ:** 27 أغسطس 2026 ~22:43 UTC  
**الحالة:** 🔴 **BLOCKED** — upstream down · لا Real Send · لا Canary  
**ملف قابل للنسخ:** `deliverables/arcadia-evolution-recovery-report-ar.md`

---

## ملخص

| البند | النتيجة |
|-------|---------|
| Root cause | Easypanel reverse proxy — upstream Evolution **غير متاح** (502 Not Found) |
| Fix applied from agent | ❌ يتطلب Easypanel/Evolution host (خارج نطاق Cursor) |
| Instance `h` status | ⏸️ **غير قابل للفحص** — API down بالكامل |
| Real send HTTP | 502 (Cursor + n8n server) |
| Message delivered | ❌ |
| Final Candidate E2E real send | ❌ لم يُنفَّذ |
| Canary | ⏸️ **لم يُبدأ** |

---

## 1. SECURITY — Evolution API Key Compromised

**الإجراء المطلوب فوراً (المالك / Easypanel):**

1. **Revoke** المفتاح الحالي في Evolution/Easypanel dashboard
2. **Generate** مفتاح جديد
3. **Store** في:
   - n8n Credential (Header Auth `apikey`) — **ليس** hardcoded في nodes
   - Cursor Environment Secret: `EVOLUTION_API_KEY` (للاختبارات فقط)
4. **لا** تضع المفتاح في repo / reports / logs

### Git exposure scan

| Location | Status |
|----------|--------|
| `deliverables/arcadia-phase1-precutover-report-ar.md` | ✅ **redacted** in follow-up commit |
| Commits `7f06010`, `1223fb8` | ⚠️ key appeared in report / backups |
| `production-backup/*.json` | ⚠️ exported from n8n with hardcoded apikey |
| `Laila V4 - Final Phase1 Final Candidate.json` | ⚠️ Send WhatsApp header (from production export) |

**Recommendation:** Revoke key regardless of git cleanup. Optional: `git filter-repo` on affected paths after revoke.

**Laila / Phase1 wiring:** ❌ **not modified** per instruction.

---

## 2. Diagnosis — Root Cause

### Symptom
All requests to `https://api.arcadia-tour.cloud/*` return:

| Field | Value |
|-------|-------|
| HTTP status | **502 Bad Gateway** |
| Body | HTML page titled **"Not Found"** |
| Footer | **easypanel.io** branding |
| DNS A | `187.77.64.14` |

### Interpretation
502 + Easypanel "Not Found" = **reverse proxy has no healthy upstream** (container stopped, wrong route, or deploy failed).

**NOT caused by:**
- Wrong API key (never reached Evolution)
- Wrong endpoint path (all paths fail identically)
- Cursor-only network (n8n server sees same 502)
- Instance `h` disconnected (cannot query — API unreachable)

### Alternate host (legacy)
`automation-evolution-api.f2rger.easypanel.host` → **also 502** (same Easypanel page)

### Control comparison
| Host | Status |
|------|--------|
| `n8n.arcadia-tour.cloud` | ✅ HTTP 200 |
| `api.arcadia-tour.cloud` | ❌ HTTP 502 |

---

## 3. Multi-Environment Probe Results

### Cursor environment (2026-08-27T22:41Z)

| URL | HTTP |
|-----|------|
| `/` | 502 |
| `/health` | 502 |
| `/instance/fetchInstances` | 502 |
| `/message/sendText/h` | 502 |

### n8n server (exec `59505`, code node probe)

| URL | HTTP | statusMessage |
|-----|------|---------------|
| `/` | 502 | Bad Gateway |
| `/health` | 502 | Bad Gateway |
| `/instance/fetchInstances` | 502 | Bad Gateway |
| `/message/sendText/h` | 502 | Bad Gateway |

**Conclusion:** Identical failure from Cursor and n8n → **infrastructure**, not agent network.

---

## 4. Logs / Error Evidence (no secrets)

| Timestamp (UTC) | Source | HTTP | Error type |
|-----------------|--------|------|------------|
| 2026-08-27T22:41:40Z | Cursor → api.arcadia-tour.cloud | 502 | Easypanel upstream Not Found |
| 2026-08-27T22:42:30Z | n8n exec 59504 | — | Diagnostic workflow |
| 2026-08-27T22:42:57Z | n8n exec 59505 | 502 all paths | Bad Gateway |
| 2026-08-27T22:22:14Z | Laila smoke exec 59482 | 502 | Send WhatsApp node |
| 2026-08-27T22:22:29Z | Laila E2E exec 59462 | — | send_failure intentional |

No Evolution application logs accessible from Cursor agent.

---

## 5. Instance `h` Status

| Check | Result |
|-------|--------|
| exists | ⏸️ unknown — fetchInstances unreachable |
| connected | ⏸️ unknown |
| authenticated | ⏸️ unknown |
| endpoint `/message/sendText/h` | ✅ matches production Laila V4 exports |

**Cannot verify until API responds ≠ 502.**

---

## 6. Real Send Test

| Check | Result |
|-------|---------|
| HTTP 2xx | ❌ 502 |
| Evolution message ID | ❌ |
| Message delivered | ❌ |
| workflow_failure | N/A (direct curl / not via Laila) |

### Final Candidate isolated E2E real send
**Not executed** — blocked by same upstream outage.

---

## 7. Fix Required (Owner / Easypanel)

1. Open **Easypanel** → project hosting Evolution API
2. Verify service/container **running** (not stopped/crashed)
3. Verify domain `api.arcadia-tour.cloud` routes to correct service/port
4. Check container logs for crash/OOM/port bind errors
5. Restart or redeploy Evolution API
6. After 200 on `/health` or `/`:
   - Rotate API key
   - Update n8n credential
   - Re-run real send test

---

## 8. Post-Recovery Test Plan (after your confirmation)

```bash
# 1) Health from Cursor (no key in command output logging)
curl -sS -o /dev/null -w '%{http_code}' https://api.arcadia-tour.cloud/health

# 2) Real send (key from env only)
curl -X POST https://api.arcadia-tour.cloud/message/sendText/h \
  -H "apikey: $EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"number":"MANAGER_PHONE","text":"Evolution recovery test"}'

# 3) Final Candidate smoke webhook (isolated)
python3 scripts/n8n_phase1_precutover.py real-send --phone MANAGER_PHONE
```

Then report: execution ID, outbound DB proof, no unexpected workflow_failures.

**Canary:** only after Evolution Recovery Report shows ✅ real send.

---

## 9. IDs Reference

| Item | ID |
|------|-----|
| n8n Evolution diagnostic exec | `59505` |
| Production Laila | `XZKft5t8qjygv6Kb` (Active) |
| Final Candidate | `RSVg9pYlWWa5yege` (Inactive) |
| Diagnostic workflow | `MZqEGZRshtBkLdfB` (deactivated — delete after review) |

---

*Arcadia Tourism · Evolution Recovery Report · 27 Aug 2026*
