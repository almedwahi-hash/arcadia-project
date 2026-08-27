# Phase 1 Migration — Diff & تطبيق

**التاريخ:** 27 أغسطس 2026  
**الملف:** `Database/supabase_schema_multi_agent_phase1.sql`  
**Rollback:** `Database/rollback_multi_agent_phase1.sql`

---

## موافقة التصميم (15 نقطة)

| # | المطلوب | الحالة في Migration |
|---|---------|---------------------|
| 1 | `customer_id` على `leads` | ✅ `ALTER leads ADD customer_id` |
| 2 | `conversation_id` بدون default per row | ✅ NOT NULL بدون DEFAULT؛ + `leads.conversation_id` للجلسة |
| 3 | `message_type` + nullable text + media | ✅ text/image/audio/document/location/video/sticker/unknown |
| 4 | idempotency `provider_message_id` | ✅ UNIQUE (channel, provider_message_id) |
| 5 | inbound قبل AI / outbound بعد الإرسال | 📋 n8n guide (لا تعديل Laila بدون export) |
| 6 | لا تفعيل `lead_state` | ✅ لم يُمس |
| 7 | لا توحيد quotes/quote_offers | ✅ لم يُمس |
| 8 | لا `approved` stage | ✅ لم يُمس |
| 9 | Error Workflow مركزي n8n | ✅ template في `n8n Workflows/` |
| 10 | workflow_failures حقول إضافية | ✅ execution_id, workflow_id, source_channel, lead_id, booking_id, last/next_retry |
| 11 | indexes مطلوبة | ✅ agent_actions(lead_id,created_at), workflow_failures(status,created_at), human_approval_queue(status,created_at) |
| 12 | Security Matrix | ✅ `deliverables/arcadia-phase1-security-matrix-ar.md` |
| 13 | Export Laila قبل تعديل | ⚠️ **مطلوب من المالك** — placeholder في Git |
| 14 | backward-compatible + rollback | ✅ ADD only + rollback file |
| 15 | migration + diff قبل التشغيل | ✅ هذا الملف |

---

## Diff — جداول جديدة

### `customers`
```
+ customer_id uuid PK
+ phone text NOT NULL UNIQUE
+ name, email, country_code, preferred_language
+ created_at, updated_at
```

### `lead_interactions`
```
+ interaction_id uuid PK
+ lead_id, customer_id FK
+ conversation_id uuid NOT NULL  (no DEFAULT — workflow sets + reuses)
+ channel, direction, role
+ message_type (text|image|audio|document|location|video|sticker|unknown)
+ message_text text NULL
+ provider_message_id text NULL
+ metadata jsonb
+ created_at
+ UNIQUE INDEX (channel, provider_message_id) WHERE provider_message_id IS NOT NULL
```

### `agent_actions`
```
+ action_id, agent_name, action_type, customer_id, lead_id, booking_id
+ source_channel, input_summary, output_summary, status, error_message, metadata, created_at
+ INDEX (lead_id, created_at DESC)
```

### `human_approval_queue`
```
+ approval_id, action_type, lead_id, booking_id, payload, reason, status
+ requested_by_agent, approved_by, resolved_at, created_at
+ INDEX (status, created_at DESC)
```

### `workflow_failures`
```
+ failure_id, workflow_name, workflow_id, execution_id, node_name, agent_name
+ source_channel, lead_id, booking_id, severity, payload, error_message
+ retry_count, status, last_retry_at, next_retry_at, resolved_at, created_at
+ INDEX (status, created_at DESC)
```

---

## Diff — أعمدة مُضافة (ALTER فقط)

### `leads`
```
+ customer_id uuid NULL → FK customers
+ conversation_id uuid NULL  (active session id for reuse)
+ INDEX customer_id, conversation_id
```

### `bookings`
```
+ lead_id uuid NULL → FK leads
+ customer_id uuid NULL → FK customers
+ quote_ref text NULL
+ INDEX lead_id
```

**لم يُحذف أو يُعاد تسمية أي عمود.**

---

## Backfill (آمن)

1. إنشاء `customers` من `leads.phone` المميز
2. ربط `leads.customer_id` بالمطابقة على phone

---

## ما لم يُنفَّذ في SQL (n8n — بعد export Laila)

1. INSERT inbound `lead_interactions` **قبل** AI Agent
2. INSERT outbound **بعد** نجاح Send
3. INSERT `agent_actions` على pricing/events
4. ربط كل workflow بـ **Arcadia - Central Error Handler**
5. تمرير `conversation_id` من `leads.conversation_id` (أو إنشاء جديد عند lead جديد)

---

## التحقق بعد التطبيق

```sql
-- جداول جديدة
SELECT table_name FROM information_schema.tables
WHERE table_schema='public'
  AND table_name IN ('customers','lead_interactions','agent_actions','human_approval_queue','workflow_failures');

-- أعمدة leads
SELECT column_name FROM information_schema.columns
WHERE table_name='leads' AND column_name IN ('customer_id','conversation_id');

-- idempotency index
SELECT indexname FROM pg_indexes
WHERE tablename='lead_interactions' AND indexname LIKE '%provider%';

-- backfill
SELECT count(*) AS customers FROM customers;
SELECT count(*) AS leads_linked FROM leads WHERE customer_id IS NOT NULL;
```

---

*بعد مراجعة هذا Diff — يُطبَّق migration على Supabase*
