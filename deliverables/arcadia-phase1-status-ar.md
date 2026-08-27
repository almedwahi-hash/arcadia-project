# Phase 1 — موافقة + تنفيذ + الملفات القابلة للنسخ

**التاريخ:** 27 أغسطس 2026  
**الحالة:** ✅ SQL مُطبَّق على Supabase | ⚠️ Laila V5 لم يُعدَّل (ينتظر Export)

---

## 1. موافقتك — 15 نقطة (مُطبَّقة في التصميم)

| # | المطلوب | ✅ |
|---|---------|---|
| 1 | `customer_id` على `leads` | ✅ |
| 2 | `conversation_id` يُعاد استخدامه (لا UUID جديد لكل interaction) | ✅ |
| 3 | `message_type` + nullable text + media metadata | ✅ |
| 4 | `provider_message_id` + idempotency | ✅ UNIQUE (channel, provider_message_id) |
| 5 | inbound قبل AI / outbound بعد الإرسال | 📋 دليل n8n (بعد export Laila) |
| 6 | لا تفعيل `lead_state` | ✅ |
| 7 | لا توحيد quotes/quote_offers | ✅ |
| 8 | لا `approved` في Phase 1 | ✅ |
| 9 | Error Workflow مركزي n8n | ✅ template JSON |
| 10 | workflow_failures حقول إضافية | ✅ |
| 11 | indexes مطلوبة | ✅ |
| 12 | Security Matrix | ✅ |
| 13 | Export Laila قبل التعديل | ⚠️ **مطلوب منك** |
| 14 | backward-compatible + rollback | ✅ |
| 15 | migration + diff قبل التشغيل | ✅ ثم طُبّق |

---

## 2. نتيجة التطبيق على Supabase

| المؤشر | القيمة |
|--------|--------|
| Migration name | `multi_agent_phase1_observability` |
| جداول جديدة | customers, lead_interactions, agent_actions, human_approval_queue, workflow_failures |
| leads + أعمدة | customer_id, conversation_id |
| bookings + أعمدة | lead_id, customer_id, quote_ref |
| customers backfill | 6 |
| leads مربوطة بـ customer | 6 / 7 |
| Idempotency index | `lead_interactions_provider_dedupe_idx` |

**لم يُكسر:** Laila V5, Pricing Engine, Follow-up Cron, Admin Commands

---

## 3. الملفات في Repo (انسخ من هنا)

| الملف | الغرض |
|-------|--------|
| `Database/supabase_schema_multi_agent_phase1.sql` | Migration كامل |
| `Database/rollback_multi_agent_phase1.sql` | Rollback |
| `deliverables/arcadia-phase1-migration-diff-ar.md` | Diff تفصيلي |
| `deliverables/arcadia-phase1-security-matrix-ar.md` | Security Matrix |
| `deliverables/arcadia-phase1-laila-integration-ar.md` | خطوات Laila بعد Export |
| `n8n Workflows/Arcadia - Central Error Handler.json` | Error Workflow مركزي |
| `n8n Workflows/production-backup/README.md` | تعليمات Export Laila |

---

## 4. ما تفعله الآن (3 خطوات)

### أ) Export Laila (إلزامي)

```
n8n → Arcadia - Laila Telegram V5 → Export
→ احفظ: n8n Workflows/production-backup/Arcadia - Laila Telegram V5.2026-08-27.json
```

### ب) فعّل Error Workflow في n8n

1. Import: `Arcadia - Central Error Handler.json`
2. عيّنه كـ **Error Workflow** في:
   - Laila V5
   - Follow-up Cron
   - Admin Commands
3. عيّن credentials: Supabase service_role + `TELEGRAM_ADMIN_CHAT_ID`

### ج) طبّق عقد Laila (بعد Export)

اتبع: `deliverables/arcadia-phase1-laila-integration-ar.md`

**الترتيب:**
1. Idempotency check (`provider_message_id`)
2. INSERT inbound `lead_interactions` **قبل** AI
3. AI + Pricing (كما هو)
4. Send message
5. INSERT outbound `lead_interactions` **بعد** نجاح الإرسال

---

## 5. ما لم يُبدأ (حسب طلبك)

- ❌ Orchestrator
- ❌ Booking Agent
- ❌ تعديل prompts Laila
- ❌ `approved` stage

**بعد مراجعة Phase 1 + Laila integration → نتحرك للحجوزات.**

---

## 6. Security Matrix — ملخص

| Table | RLS | anon effective access |
|-------|-----|----------------------|
| leads | OFF | 🔴 Full read/write |
| hotels, rate_plans | OFF | 🔴 Full read/write |
| **جداول Phase 1 جديدة** | ON + REVOKE | 🟢 Blocked لـ anon |

**لم يُغيّر أي policy على جداول legacy** — راجع الملف الكامل للتفاصيل.

---

## 7. Rollback (إن لزم)

```bash
# في Supabase SQL Editor
\i Database/rollback_multi_agent_phase1.sql
```

---

*Arcadia Tourism · Phase 1 complete · انتظر Export Laila للخطوة التالية*
