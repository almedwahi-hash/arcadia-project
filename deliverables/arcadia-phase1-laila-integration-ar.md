# n8n — Phase 1 تكامل Laila V5 (بدون كسر الإنتاج)

**التاريخ:** 27 أغسطس 2026  
**الشرط:** Export production Laila V5 **قبل** أي تعديل — احفظ في:

```
n8n Workflows/production-backup/Arcadia - Laila Telegram V5.YYYY-MM-DD.json
n8n Workflows/Arcadia - Laila Telegram V5.json
```

---

## 1. conversation_id — إعادة الاستخدام

```
عند رسالة واردة:
  1. SELECT lead_id, conversation_id FROM leads WHERE phone = $phone
  2. IF conversation_id IS NULL:
       SET conversation_id = gen_random_uuid()  -- مرة واحدة للجلسة
       UPDATE leads SET conversation_id = $new_id
  3. USE leads.conversation_id في كل lead_interactions لهذه المحادثة
```

**لا** تستخدم `gen_random_uuid()` داخل INSERT interaction.

**إعادة فتح جلسة جديدة (اختياري لاحقاً):** عند `stage = closed/lost` أو أمر staff — rotate conversation_id.

---

## 2. Idempotency — provider_message_id

```
قبل أي معالجة — فقط إذا provider_message_id موجود وغير فارغ:
  IF provider_message_id IS NOT NULL AND trim(provider_message_id) <> '':
    SELECT 1 FROM lead_interactions
    WHERE channel = $channel AND provider_message_id = $id
    IF exists → STOP (duplicate webhook — no AI, no reply)
  ELSE:
    تابع المعالجة (لا dedupe)
```

**في n8n:** استخدم IF node قبل AI — لا تعتمد على EXCEPTION فقط.
بديل SQL: `INSERT ... ON CONFLICT DO NOTHING` ثم تحقق إن `interaction_id` رجع.

**WhatsApp:** `messages[0].id`  
**Telegram:** `message.message_id` + chat id في metadata

---

## 3. تسجيل المحادثة — ترتيب العقد

### A) بعد Normalize payload — قبل AI

**Supabase INSERT** → `lead_interactions`:
```json
{
  "lead_id": "...",
  "customer_id": "...",
  "conversation_id": "<from leads.conversation_id>",
  "channel": "whatsapp",
  "direction": "inbound",
  "role": "user",
  "message_type": "text|image|...",
  "message_text": "...",
  "provider_message_id": "...",
  "metadata": { "raw_type": "...", "media_id": "..." }
}
```

### B) بعد نجاح Send Message — بعد AI

**Supabase INSERT** → `lead_interactions` (outbound):
```json
{
  "direction": "outbound",
  "role": "assistant",
  "message_type": "text",
  "message_text": "<sent text>",
  "provider_message_id": "<wa/tg send response id if available>",
  "conversation_id": "<same session id>"
}
```

### C) agent_actions (عند التسعير)

بعد `TOOL:get_price` نجاح/فشل:
```json
{
  "agent_name": "sales",
  "action_type": "get_price",
  "lead_id": "...",
  "source_channel": "whatsapp",
  "input_summary": "RU Moscow 4pax 5n",
  "output_summary": "final_price_usd=4643",
  "status": "success|failed"
}
```

---

## 4. ربط Central Error Handler

في Laila V5 settings:
- **Error Workflow** → `Arcadia - Central Error Handler`
- لا error branch محلي فقط

---

## 5. ما لا يُغيّر في Phase 1

- System prompt Laila
- Pricing Engine RPC / TOOL:get_price
- Follow-up Cron
- Admin Commands
- `leads.stage` values (no `approved`)

---

## 6. customer_id

بعد upsert lead:
```
IF leads.customer_id IS NULL:
  upsert customers by phone
  UPDATE leads SET customer_id = customers.customer_id
```

Migration backfill يغطي الحالي؛ العقد أعلاه للـ leads الجديدة.

---

*Arcadia Tourism · Phase 1 n8n integration guide*
