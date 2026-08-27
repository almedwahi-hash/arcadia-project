# Arcadia Phase 1 — Pre-Cutover Verification Report
**التاريخ:** 27 أغسطس 2026 ~22:36 UTC  
**الحالة:** 🟡 Pre-Cutover مكتمل جزئياً — **Canary Cutover مؤجّل** (Evolution API 502)  
**ملف قابل للنسخ:** `deliverables/arcadia-phase1-precutover-report-ar.md`

---

## ملخص تنفيذي

| البند | الحالة |
|-------|--------|
| 1. Workflow Failures Audit (+24) | ✅ محلّل — كلها intentional / side-effect |
| 2. Final Candidate persisted في repo | ✅ |
| 3. Smoke tests على Final Candidate | ✅ pipeline يعمل — Send يفشل 502 |
| 4. Real WhatsApp send | ❌ Evolution API 502 (كل الأرقام) |
| 5–6. Canary Cutover | ⏸️ **لم يُنفَّذ** — بانتظار Evolution أو موافقة المالك |
| 7. Rollback script | ✅ جاهز |
| Booking Agent / Orchestrator | ⏸️ لم يبدأ |

**لا يُنفَّذ Production Cutover الكامل حتى يُثبت إرسال WhatsApp حقيقي ناجح.**

---

## 1. Workflow Failures Audit (53 → 77, +24)

**النافذة:** `created_at > 2026-08-27T22:15:00Z`  
**العدد:** 24 row بالضبط

### تجميع حسب Workflow

| workflow_name | count | distinct execution_id |
|---------------|-------|---------------------|
| Laila V4 - Final Phase1 Working | 16 | 16 |
| Arcadia - Phase1 Inbound Pipeline | 14 | 14 |
| Arcadia - Phase1 Laila Scenario Test | 6 | 6 |
| Arcadia - Phase1 Error Handler Test | 2 | 2 |

**ملاحظة:** الـ +24 في تقرير E2E = فقط صفوف Working Copy + Inbound من 22:15+. صفوف Scenario Test و Error Handler Test (+8) من جلسة 22:06–22:07 خارج نافذة +24 لكنها أيضاً intentional.

### تحليل الـ 24 row (E2E window)

| المجموعة | exec IDs | النوع | intentional? |
|----------|----------|-------|----------------|
| **Inbound sub-workflow side-effect** | 59402,59406,59410,59414,59418,59422,59426,59430 | Insert Inbound JSON / message_type errors (مُصلَحة لاحقاً) | ✅ test — early E2E attempts |
| **Parent + child pairs** | 59401+59402, 59405+59406, … | errorWorkflow يسجّل parent + subflow | ✅ retry/side-effect |
| **Send WhatsApp 502** | 59452,59457,59434,59439,59444,59449 | Evolution Bad Gateway | ✅ expected during E2E |
| **send_failure test** | 59462 | invalid URL intentional | ✅ |
| **ai_node_failure test** | 59467 | Decision Engine throw intentional | ✅ |

### تفاصيل error type (من payload.last_node)

| last_node | execution_ids | التصنيف |
|-----------|---------------|---------|
| Intentional Fail Node | 59389 | ✅ Error Handler test |
| Insert Inbound Interaction | inbound sub-execs | ✅ side-effect (قبل fix) |
| Send WhatsApp | 59452,59457,59462,59434,59439,59444,59449 | ✅ Evolution 502 أو send_failure test |
| Decision Engine | 59467 | ✅ ai_node_failure intentional |

### production error غير متوقع؟

**لا.** كل الصفوف مرتبطة بـ:
- Phase1 test workflows (Error Handler Test, Scenario Test)
- Laila V4 Working Copy E2E runs
- Inbound Pipeline sub-executions triggered by errorWorkflow

**لا يوجد** failure من Production `Laila V4 - Final` (`XZKft5t8qjygv6Kb`) في هذه النافذة.

**القرار:** لا حذف السجلات — كلها موثّقة كـ test artifacts.

---

## 2. Final Candidate — Persisted في Repo

| البند | القيمة |
|-------|--------|
| **الملف** | `n8n Workflows/Laila V4 - Final Phase1 Final Candidate.json` |
| **المصدر** | `Laila V4 - Final.2026-08-27.json` (أحدث export) |
| **الأمر** | `python3 scripts/patch_laila_phase1.py --input ... --output ...` |
| **n8n ID** | `RSVg9pYlWWa5yege` |
| **Production ID (old)** | `XZKft5t8qjygv6Kb` |

### Nodes المضافة (7) vs Production (8 → 15)

```
Phase1 Normalize Inbound
Arcadia - Phase1 Inbound Pipeline
Phase1 IF Proceed (not duplicate)
Phase1 Prepare Pricing Action          ← observability only
Arcadia - Phase1 Pricing Action Log    ← observability only
Phase1 Prepare Outbound
Arcadia - Phase1 Outbound Log
```

### الإصلاحات المضمّنة في Final Candidate

| Fix | مضمّن |
|-----|--------|
| Normalize Inbound + message_type map | ✅ |
| Inbound Pipeline (Insert uses Ensure conversation_id) | ✅ sub-workflow JSON |
| IF Proceed | ✅ |
| Outbound Log + Prepare Outbound (DE fallback) | ✅ |
| Pricing Action Log after Decision Engine | ✅ continueOnFail |
| Error Handler settings.errorWorkflow | ✅ |
| executeWorkflow passthrough | ✅ sub-workflows |

**Diff meta:** `deliverables/arcadia-phase1-laila-diff.json`

---

## 3. Smoke Tests — Final Candidate (`RSVg9pYlWWa5yege`)

**Webhook معزول:** `laila-v4-phase1-smoke`

| Scenario | Exec ID | Status | التحقق |
|----------|---------|--------|--------|
| new_customer | 59482 | error* | inbound ✅ · وصل Send WhatsApp |
| duplicate | 59487 | success | توقف at IF Proceed ✅ |
| pricing_success | 59489 | error* | DE response **٧٨١ دولار** ✅ |
| manual_quote | 59494 | error* | no invented price ✅ |
| ai_node_failure | 59500 | error* | handler **59502** ✅ |

\* status=error بسبب **Send WhatsApp 502** — ليس فشل pipeline قبل Send.

### inbound DB proof (smoke)

```
wa_smoke_new_20260827223433     inbound ✅
wa_smoke_price_20260827223433   inbound ✅
wa_smoke_manual_20260827223433  inbound ✅
wa_smoke_aifail_20260827223433  inbound ✅
```

### agent_actions (smoke)

| status | output |
|--------|--------|
| success | باقة ألماتي — ٧٨١ دولار |
| failed | NonexistentCityXYZ غير متاحة |

---

## 4. Real WhatsApp Send Test — ❌ BLOCKED

### ما تم

```bash
POST https://api.arcadia-tour.cloud/message/sendText/h
apikey: 863E50B69702-4B1F-B00F-45E76B267DBE
number: 380936582617  (manager phone)
→ HTTP 502 Bad Gateway (HTML "Not Found" page)
```

### النتيجة

| التحقق | النتيجة |
|--------|---------|
| Evolution returns success | ❌ 502 |
| الرسالة تصل | ❌ لم يُختبر |
| outbound بعد success | ❌ mock فقط (exec 59475 سابقاً) |
| workflow_failure لنفس exec | ✅ عند فشل Send |

### التوثيق

502 **ليس** مقصوراً على رقم الاختبار `971509998001` — يحدث أيضاً على:
- `380936582617` (manager)
- `971509998002` (smoke test)

**السبب المحتمل:** `api.arcadia-tour.cloud` Evolution proxy غير متاح من مسار الشبكة الحالي أو الخدمة down مؤقتاً.

**mock send (httpbin) ليس إثباتاً نهائياً** — يثبت outbound wiring فقط.

---

## 5–6. Canary Cutover — ⏸️ لم يُنفَّذ

**السبب:** البند 4 (Real WhatsApp send) لم ينجح. تنفيذ Canary يعطّل Production `XZKft5t8qjygv6Kb` ويفعّل Final Candidate على `laila-v4` — **بدون إرسال يعمل = regression فوري للعملاء.**

### جاهزية Canary (عند إصلاح Evolution)

```bash
python3 scripts/n8n_phase1_precutover.py canary-start   # deactivate prod, activate final
# owner sends 1 real WhatsApp message
python3 scripts/n8n_phase1_precutover.py canary-verify
```

### Rollback (جاهز)

```bash
python3 scripts/n8n_phase1_precutover.py rollback
# → reactivate XZKft5t8qjygv6Kb, deactivate RSVg9pYlWWa5yege
```

---

## 7. Rollback Readiness

| البند | القيمة |
|-------|--------|
| Production workflow | `Laila V4 - Final` · `XZKft5t8qjygv6Kb` · **Active ✅** |
| Final Candidate | `RSVg9pYlWWa5yege` · **Inactive** |
| Production snapshot | ✅ exported قبل كل خطوة |
| Rollback script | `scripts/n8n_phase1_precutover.py rollback` |

---

## 8. IDs & Execution Summary (copy-ready)

```
Production (old):     XZKft5t8qjygv6Kb  Laila V4 - Final           ACTIVE
Final Candidate:      RSVg9pYlWWa5yege  Laila V4 - Final Phase1 Final Candidate  INACTIVE

E2E (prior session):
  pricing_success:     59452
  manual_quote:        59457
  send_failure:        59462 → handler 59466
  ai_node_failure:     59467 → handler 59469
  outbound mock proof: 59475

Smoke (Final Candidate):
  new_customer:        59482
  duplicate:           59487
  pricing_success:     59489  (٧٨١ دولار in DE response)
  manual_quote:        59494
  ai_node_failure:     59500 → handler 59502

Real WhatsApp send:    NOT VERIFIED (Evolution 502)
Canary:                NOT STARTED
```

### Supabase counts (current)

| Metric | العدد |
|--------|-------|
| lead_interactions | 18+ |
| workflow_failures | 77+ |
| agent_actions | 5+ |

---

## 9. الخطوة التالية (يتطلب موافقة المالك)

1. **تحقق Evolution API** من شبكتك: `curl -X POST https://api.arcadia-tour.cloud/message/sendText/h ...`
2. عند نجاح الإرسال → أرسل **موافقة Canary** وسننفّذ:
   - snapshot جديد
   - deactivate `XZKft5t8qjygv6Kb`
   - activate `RSVg9pYlWWa5yege` على `laila-v4`
   - رسالة حقيقية واحدة + مراقبة
3. بعد Canary ناجح → **Final Cutover Report** + إغلاق Phase 1 رسمياً

---

*Arcadia Tourism · Pre-Cutover Verification · 27 Aug 2026*
