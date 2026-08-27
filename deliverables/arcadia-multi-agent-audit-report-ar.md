# تقرير Audit + خطة Multi-Agent — أركاديا السياحية

**التاريخ:** 27 أغسطس 2026  
**النطاق:** Audit فقط — **لم يُنفَّذ أي تعديل على n8n أو Supabase أو Laila**  
**مصادر الفحص:**
- Supabase Project: `xfibcjhshpmqkrhlpsoa` (eu-central-1) — **مُفحوص مباشرة**
- Git repo الحالي — **مُفحوص**
- n8n instance — **غير متاح من Cloud Agent** (الاعتماد على التوثيق الداخلي + ما يجب تصديره)

---

## 0. ملخص تنفيذي (Executive Summary)

| البند | الحالة |
|-------|--------|
| **المبيعات + التسعير** | ✅ يعملان — Laila V5 + Pricing Engine (Supabase RPC) |
| **Follow-up + Admin** | ✅ موثّقان ويعملان حسب التشغيل |
| **الحجوزات الآلية** | ❌ `bookings` موجود (147 سجل) لكن **غير مربوط** بـ leads/quotes ولا Agent |
| **Orchestrator مركزي** | ❌ غير موجود — كل workflow مستقل |
| **lead_interactions** | ❌ **غير موجود** في DB رغم ذكره في التوثيق |
| **حالتان متعارضتان** | ⚠️ `leads` (7 صفوف، مستخدم) + `lead_state` (0 صفوف، فارغ) |
| **quote_offers vs quotes** | ⚠️ جدولان منفصلان — `quotes` (117) نشط، `quote_offers` (0) |
| **Marketing** | 🟡 `content_queue` موجود (36 مسودة) — بدون Agent منفصل |
| **أمن DB** | 🔴 25+ جدول بدون RLS — مخاطرة عالية |

**القرار:** النظام **قائم وقابل للتوسع** — لا نبني من الصفر. نضيف طبقة Orchestrator + Booking Agent + جداول observability **بدون كسر** Laila V5 / Pricing / Follow-up / Admin.

---

## 1. AUDIT — n8n Workflows

### 1.1 حدود الفحص

- مجلد `n8n Workflows/` **غير موجود** في Git repo الحالي
- لا يوجد وصول مباشر إلى n8n Cloud/self-hosted من Cloud Agent
- التالي مبني على: `email-bd-playbook-ar.md`، `email-ops-system-ar.md`، `outreach-sent-log-batch4-ar.md`

### 1.2 Workflows المؤكدة (حسب التوثيق — ✅ تشغيل)

| Workflow | الوظيفة | القنوات | الحالة |
|----------|---------|---------|--------|
| **Arcadia - Laila Telegram V5** | Sales Agent — جمع بيانات، رد، استدعاء تسعير | WhatsApp + Telegram | ✅ Production |
| **Arcadia - Follow-up Cron (3h-24h)** | متابعة تلقائية بعد عرض السعر | WhatsApp leads | ✅ Production |
| **Arcadia - Admin Commands** | `/status`, `/lead`, `/pause`, `/resume` | Telegram Admin | ✅ Production |

### 1.3 Workflows مذكورة — غير مؤكدة في repo

| Workflow | الوصف | الحالة |
|----------|-------|--------|
| **Calculator Bot v2** | تقدير أولي Telegram | 🟡 مذكور — لم يُفحص JSON |
| **Laila V4 cancel node** | إلغاء follow-up عند رد العميل | 🟡 جزء من V5 أو workflow قديم |
| **Zoho → Telegram** (مقترح) | تنبيه بريد جديد | ❌ غير مُنفَّذ |
| **info@ webhook** | استفسار بريد → lead | ❌ غير مستخدم (batch4 log) |
| **Instagram / Website Gateway** | — | ❌ غير موجود |

### 1.4 Workflows محتملة مكررة/قديمة (يحتاج تصدير n8n)

| المرشح | السبب | التوصية |
|--------|-------|---------|
| Laila V1–V4 | V5 هو المعتمد | أرشف — لا حذف قبل تصدير |
| Naseem (قديم) | `conversations` + `naseem_instructions` في DB | تحقق إن كان workflow ما زال Active |
| Pricing webhook منفصل | قد يكون داخل Laila V5 | توحيد عبر Orchestrator لاحقاً |

**إجراء مطلوب قبل المرحلة 1:**

```
من n8n UI → Export JSON لكل workflow Active يحتوي "Arcadia" أو "Laila"
→ حفظ في repo: n8n Workflows/
→ تسليم قائمة Webhook URLs + Cron schedules
```

### 1.5 Webhooks المستخدمة (مستنتجة — تحتاج تأكيد)

| Webhook | المستهلك | الغرض |
|---------|----------|-------|
| WhatsApp Business API callback | Laila V5 | رسائل واردة |
| Telegram Bot webhook | Laila V5 + Admin Commands | رسائل + أوامر |
| **Pricing Engine webhook** | Laila V5 (`TOOL:get_price`) | استدعاء تسعير — **الوجهة الفعلية غير معروفة من repo** |
| Follow-up Cron | داخلي (Schedule) | لا webhook — cron trigger |
| Zoho IMAP/webhook | — | ❌ غير مفعّل |

**ملاحظة Pricing Engine:** التوثيق يذكر webhook خارجي، لكن Supabase فيه RPC كامل (`quote_package`, `quote_multi`, …). **الاحتمال الأقوى:** n8n يستدعي Supabase REST/RPC عبر `service_role` أو webhook wrapper — **يجب تصدير Laila V5 JSON للتأكيد**.

### 1.6 Credentials / Secrets (بدون قيم)

| Credential | الاستخدام |
|------------|-----------|
| Supabase `service_role` | n8n → قراءة/كتابة leads, quotes, pricing |
| Supabase `anon` key | أدوات read-only محدودة |
| OpenAI / LLM API | Laila Agent node |
| WhatsApp Business API token | إرسال/استقبال |
| Telegram Bot token | Laila + Admin |
| Zoho SMTP / IMAP | outreach scripts (خارج n8n) |

---

## 2. AUDIT — Supabase (مُفحوص مباشرة)

**Project:** `xfibcjhshpmqkrhlpsoa`  
**Postgres:** 17.6  
**Edge Functions:** 0  
**Migrations:** 33 (آخر: `create_fit_rates_and_addons`)

### 2.1 جداول Sales / CRM / Conversations

| الجدول | الصفوف | RLS | الدور |
|--------|--------|-----|-------|
| **leads** | 7 | ❌ | CRM رئيسي — `phone` unique، `stage` check constraint |
| **lead_state** | 0 | ✅ (no policy) | State machine تفصيلي — **فارغ / غير مستخدم حالياً** |
| **pending_messages** | 0 | ✅ (no policy) | Dead-letter / retry queue — **جاهز structurally** |
| **conversations** | 28 | ❌ | سجل رسائل قديم (`phone`, `role`, `message`) — آخر: 2026-06-28 |
| **reviews** | 0 | ❌ | feedback post-trip — مربوط بـ `lead_id` |
| **bot_sessions** | 1 | ✅ | Calculator Bot state |
| **manager_instructions** | 1 | ❌ | تعليمات ديناميكية للـ Agent |
| **naseem_instructions** | 24 | ❌ | نظام قديم (Naseem) |

**⚠️ `lead_interactions` — غير موجود.** التوثيق في `email-bd-playbook-ar.md` §6.1 **قديم/غير دقيق**.

**حالات `leads.stage` الفعلية:**

```
new | quoted | interested | followup | manual_quote | closed | lost | handoff
```

**توزيع حالي (27 أغسطس 2026):**

- new: 3
- quoted: 3 (RU offers — $1088, $2951, $4643)
- lost: 1

### 2.2 جداول Pricing

| الجدول/Function | الصفوف | الدور |
|-----------------|--------|-------|
| **hotels** | 101 | contracts |
| **room_types** | 248 | |
| **seasons** | 244 | |
| **rate_plans** | 840 | FIT pricing source |
| **services** | 487 | transfers, tours, guides |
| **fx_rates** | 8 | conversion |
| **group_rates** | 3 | B2B 15–40 pax (KZ/Almaty/4N) |
| **fit_rates** | 16 | FIT bands |
| **fit_addon_excursions** | 13 | extras |
| **remote_tour_*** | 5+8+40 | Charyn/Kolsai transport |
| **quotes** | 117 | FIT/B2B quote archive (103 B2B draft) |
| **quote_offers** | 0 | B2B structured offers — **schema جاهز، غير مستخدم** |

**Pricing Engine = Supabase RPC Functions:**

```
quote_package()        — single city FIT
quote_multi()          — multi-city
quote_multi_options()  — options comparison
quote_options()        — wrapper
list_hotels()          — hotel lookup
find_hotel()           — fuzzy search
room_cost() / rc()     — room configuration
acquire_lead_lock()    — concurrency control
release_lead_lock()    — concurrency control
```

**قاعدة التسعير:** AI **لا يحسب** — يستدعي RPC ويرجع `final_price_usd` أو `error`.

### 2.3 جداول Operations / Bookings

| الجدول | الصفوف | RLS | الدور |
|--------|--------|-----|-------|
| **bookings** | 147 | ✅ | ops app — **يدوي/داخلي** |
| **destinations** | 5 | ✅ | FK من bookings |
| **app_users** | 3 | ✅ | internal ops users |
| **itineraries** | 71 | ✅ | programs |
| **packages** | 4 | ✅ | marketing packages |

**حالات `bookings.status` الفعلية:**

```
confirmed: 133 | pending: 10 | cancelled: 2 | in_hotel: 2
```

**⚠️ `bookings` لا يحتوي:** `lead_id`, `quote_id`, `quote_ref`, `customer_id` — **معزول عن Sales pipeline**.

### 2.4 جداول B2B / Marketing

| الجدول | الصفوف | الدور |
|--------|--------|-------|
| **b2b_partners** | 1 | partner CRM |
| **outreach_log** | 0 | email/WA correspondence |
| **content_queue** | 36 | instagram drafts (32 draft + 1 approved) |

### 2.5 أين تُحفظ حالة العميل والمحادثة؟

```
┌─────────────────────────────────────────────────────────┐
│  PRODUCTION PATH (Laila V5 — مؤكد من DB data)          │
├─────────────────────────────────────────────────────────┤
│  Identity:     leads.phone (unique)                     │
│  CRM state:    leads.stage + leads.sales_state (jsonb)  │
│  Qualification: leads.destination, travel_dates,       │
│                 pax_adults, children_ages, budget...    │
│  Offer:        leads.offer_sent (jsonb) + offer_amount  │
│  Follow-up:    leads.next_followup, follow_up_count,  │
│                 paused, needs_human                     │
│  Conversation: ❌ lead_interactions غير موجود           │
│                 conversations (legacy, 28 rows)          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PLANNED BUT UNUSED                                     │
├─────────────────────────────────────────────────────────┤
│  lead_state — structured FSM, awaiting_field, lock     │
│  pending_messages — retry queue                        │
└─────────────────────────────────────────────────────────┘
```

### 2.6 كيف يعمل Pricing Engine (مستنتج + مؤكد DB)

```
Laila V5 (AI Agent)
    │
    ├─► يجمع: dest, city, nights, adults, children, dates, hotel tier
    │
    ├─► TOOL:get_price ──► [n8n HTTP node أو Supabase RPC]
    │                           │
    │                           ├─ FIT (2–14 pax): quote_package / quote_multi
    │                           ├─ Group (15–40): group_rates lookup
    │                           └─ Error: no_hotel_for_city → manual_quote
    │
    ├─► يحفظ: leads.offer_sent + offer_amount_usd
    ├─► quotes table (117 archived calculations)
    └─► leads.stage = 'quoted'
```

**ممنوع:** حساب سعر في prompt — موثّق صراحة في playbook.

### 2.7 كيف تعمل Laila V5 (من التوثيق + DB)

```
[WhatsApp/Telegram inbound]
        │
        ▼
[Identify customer by phone → SELECT leads WHERE phone=]
        │
        ▼
[AI Agent — سؤال واحد/رسالة]
        │
        ├─► UPDATE leads (fields + stage)
        ├─► IF data complete → call Pricing Agent/Engine
        ├─► Send formatted offer to customer
        └─► SET next_followup for Cron
        │
[Customer replies]
        │
        └─► Cancel pending follow-ups (V4 cancel node)
```

### 2.8 Follow-up Cron

```
[Schedule: every X minutes]
        │
        ▼
[SELECT leads WHERE stage IN ('quoted','interested','followup')
              AND next_followup <= NOW()
              AND paused = false]
        │
        ├─► 3h: first follow-up message
        ├─► 24h: second follow-up
        └─► UPDATE follow_up_count, next_followup
```

### 2.9 Admin Commands

```
Telegram message from Admin chat
        │
        ├─► /status     → aggregate leads counts
        ├─► /lead +phone → lead details
        ├─► /pause +phone → leads.paused = true
        └─► /resume +phone → leads.paused = false
```

**⚠️:** read-only جزئياً — `/pause`/`/resume` يكتبان DB.

### 2.10 نقاط ضعف / Single Points of Failure

| # | المخاطرة | التأثير | الأولوية |
|---|----------|---------|----------|
| 1 | **n8n instance واحد** | توقف كل Agents | 🔴 |
| 2 | **لا lead_interactions** | لا audit trail للمحادثات | 🔴 |
| 3 | **leads + lead_state مزدوج** | confusion / data drift | 🟡 |
| 4 | **bookings معزول** | لا automation بعد الموافقة | 🔴 |
| 5 | **25+ table sin RLS** | data exposure via anon key | 🔴 |
| 6 | **quotes vs quote_offers** | duplicate quote models | 🟡 |
| 7 | **Laila = monolith workflow** | صعب التوسع بدون Orchestrator | 🟡 |
| 8 | **conversations legacy** | duplicate chat log | 🟢 |
| 9 | **لا error dead-letter active** | pending_messages فارغ | 🟡 |
| 10 | **Workflow JSONs خارج Git** | no version control | 🟡 |

### 2.11 منطق في Prompts يجب نقله لـ DB/Workflow

| المنطق | المكان الحالي | الأفضل |
|--------|---------------|--------|
| قائمة destinations/cities | prompt | `destinations` table ✅ موجود |
| أسعار B2B | prompt (محتمل) | `group_rates` ✅ |
| program days | prompt | `itineraries.notes_ar` ✅ |
| lead stage transitions | prompt + leads.stage | `lead_state` FSM أو workflow rules |
| follow-up timing 3h/24h | Cron workflow | ✅ صحيح في workflow |
| hotel tier mapping | prompt | `quote_package` modes ✅ |
| approval rules (refund/discount) | prompt (implicit) | `human_approval_queue` ❌ ناقص |

---

## 3. Architecture Diagram (مبني على الموجود)

### 3.1 الوضع الحالي (As-Is)

```
 WhatsApp ──────┐
 Telegram ──────┼──► [Laila V5] ──► Supabase (leads, quotes, RPC pricing)
                │         │
                │         └──► WhatsApp/Telegram reply
                │
 Admin TG ───────┼──► [Admin Commands] ──► Supabase leads (read/write pause)
                │
 Cron ──────────┼──► [Follow-up 3h-24h] ──► Supabase leads ──► WhatsApp
                │
 Email info@ ────┼──► [Zoho manual + Python scripts] ──► markdown logs
                │                                    └──► b2b_partners (partial)
 Website ────────┼──► [No agent gateway]
 Instagram ──────┘

 Ops Team ──► [Internal App] ──► bookings (147) — MANUAL, no lead link

 Marketing ──► content_queue (36 drafts) — separate, no agent
```

### 3.2 الهدف (To-Be) — Multi-Agent

```
 WhatsApp / Telegram / Instagram / Website / Email
                        │
                        ▼
              ┌─────────────────────┐
              │  Arcadia Gateway    │  ← thin: normalize payload
              │  (webhook router)   │
              └─────────┬───────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ Arcadia Orchestrator │  ← LIGHT ONLY:
              │                      │    identify, read state, intent,
              │                      │    route, log routing
              └─────────┬───────────┘
                        │
     ┌──────────┬───────┼───────┬──────────┬──────────┐
     ▼          ▼       ▼       ▼          ▼          ▼
 [Sales]   [Pricing] [Booking] [CS]   [Marketing] [Manager]
  Laila      Agent     Agent    Agent    Agent      Agent
  V5+        sub-WF    sub-WF   sub-WF   sub-WF     sub-WF
     │          │       │       │          │          │
     └──────────┴───────┴───────┴──────────┴──────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │     Supabase        │
              │  (shared truth)     │
              └─────────┬───────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    Customer reply   Staff notify   Manager report
    (WA/TG)         (Telegram)     (Telegram cron)
```

**قاعدة Orchestrator:** لا prompts ثقيلة — فقط routing + logging.

---

## 4. Data Model — مقترح vs موجود

### 4.1 Entity Mapping

| الكيان المطلوب | الموجود | القرار |
|----------------|---------|--------|
| **customers** | ❌ | **جديد** — أو derive from `leads.phone` initially |
| **leads** | ✅ `leads` | **استخدم الموجود** — extend columns |
| **lead_interactions** | ❌ | **جديد** — replace `conversations` |
| **conversation_state** | 🟡 `lead_state` (فارغ) | **قرار:** merge into `lead_state` OR extend `leads` — see §4.3 |
| **itineraries** | ✅ | استخدم |
| **group_rates** | ✅ | استخدم |
| **quote_offers** | ✅ (0 rows) | استخدم لـ B2B؛ `quotes` لـ FIT archive |
| **bookings** | ✅ (147) | **extend** — add FKs, don't recreate |
| **booking_tasks** | ❌ | **جديد** |
| **booking_status_log** | ❌ | **جديد** |
| **reminders** | ❌ | **جديد** |
| **complaints** | ❌ | **جديد** |
| **content_queue** | ✅ (36) | استخدم |
| **agent_actions** | ❌ | **جديد** |
| **human_approval_queue** | ❌ | **جديد** |
| **workflow_errors** (DLQ) | 🟡 `pending_messages` | extend OR new `workflow_failures` |

### 4.2 العلاقات المقترحة (Keys)

```
customers
  customer_id (uuid PK)
  phone (unique)
  name, email, country, preferred_language
  created_at

leads
  lead_id (uuid PK) ← موجود
  customer_id (uuid FK → customers) ← NEW
  phone ← keep for backward compat
  stage, sales_state, ...
  quote_id (FK → quotes.id) ← NEW optional
  booking_id (FK → bookings.booking_id) ← NEW optional

lead_interactions ← NEW
  interaction_id (uuid PK)
  lead_id (FK)
  customer_id (FK)
  conversation_id (uuid) — groups one chat session
  channel (whatsapp|telegram|email|web)
  direction (inbound|outbound)
  role (user|assistant|system|staff)
  message_text
  metadata jsonb
  created_at

lead_state ← EXISTING — activate OR deprecate
  Option A: populate from leads on each message
  Option B: migrate leads.stage logic here

quotes ← EXISTING (FIT engine output)
  id, quote_ref, total_usd, packages jsonb, status

quote_offers ← EXISTING (B2B formal offers)
  offer_id, partner_id, lead_id ← NEW FK, payload, status

bookings ← EXTEND
  booking_id (text PK) ← keep
  lead_id ← NEW
  quote_id / quote_ref ← NEW
  customer_id ← NEW
  status ← normalize to new enum

booking_tasks ← NEW
  task_id, booking_id, task_type (hotel|transfer|tour|...),
  supplier_name, status, assigned_to,
  confirmation_number, due_at, completed_at

booking_status_log ← NEW
  log_id, booking_id, old_status, new_status,
  changed_by (agent|staff|system), note, created_at

reminders ← NEW
  reminder_id, booking_id, lead_id, reminder_type,
  scheduled_at, sent_at, channel, status

complaints ← NEW
  complaint_id, lead_id, booking_id, severity,
  category, status, escalated, resolution

agent_actions ← NEW
  (as specified in requirements)

human_approval_queue ← NEW
  approval_id, action_type, payload, status,
  requested_by_agent, approved_by, resolved_at

content_queue ← EXISTING — add lead_id, offer_id optional FKs
```

### 4.3 قرار `conversation_state` — توصية

**لا تنشئ جدولاً ثالثاً.** الخطة:

1. **قصير المدى:** `leads` + `sales_state` jsonb (backward compatible مع Laila V5)
2. **متوسط المدى:** populate `lead_state` تدريجياً — فيه `awaiting_field`, locks, `acquire_lead_lock()`
3. **Interactions:** `lead_interactions` جديد — **مصدر الحقيقة للمحادثات**

---

## 5. State Machines

### 5.1 Lead State — Mapping (موجود → مقترح)

| الحالة المقترحة | Mapping من `leads.stage` | ملاحظة |
|-----------------|--------------------------|--------|
| **NEW** | `new` | ✅ |
| **QUALIFYING** | `new` + partial fields | derive: missing destination/dates/pax |
| **QUALIFIED** | `new` + all required fields | workflow rule — not new enum yet |
| **QUOTED** | `quoted` | ✅ |
| **NEGOTIATING** | `interested`, `followup` | merge |
| **PRICE_REVIEW_REQUIRED** | `manual_quote` | ✅ perfect match |
| **APPROVED** | ❌ missing | **add** `approved` to check constraint |
| **BOOKING_PENDING** | `handoff` | rename semantically |
| **CONFIRMED** | `closed` (when booking confirmed) | split meaning |
| **TRAVELING** | ❌ missing | derive from booking dates |
| **COMPLETED** | ❌ missing | post-trip |
| **LOST** | `lost` | ✅ |

**توصية:** لا تستبدل الـ 8 stages دفعة واحدة. **أضف:** `approved`, `booking_pending`, `traveling`, `completed` — واحتفظ بالقديم مع mapping layer في Orchestrator.

### 5.2 Booking State — Mapping

| المقترح | الموجود في `bookings.status` | Action |
|---------|------------------------------|--------|
| DRAFT | — | new |
| PENDING_SUPPLIER | `pending` | map |
| PENDING_PAYMENT | — | new (derive from is_paid) |
| PARTIALLY_CONFIRMED | — | new |
| CONFIRMED | `confirmed` | ✅ |
| IN_PROGRESS | `in_hotel` | map |
| COMPLETED | — | new |
| CANCELLED | `cancelled` | ✅ |

---

## 6. Agent Actions — المواصفات

كل عملية مهمة يقوم بها أي Agent تُسجَّل في `agent_actions`:

| الحقل | النوع | الوصف |
|-------|------|-------|
| agent_name | text | sales / pricing / booking / cs / marketing / manager / orchestrator |
| action_type | text | qualify_lead / get_price / create_booking / send_reminder / ... |
| customer_id | uuid | FK optional |
| lead_id | uuid | FK optional |
| booking_id | text | FK optional |
| source_channel | text | whatsapp / telegram / email / cron |
| input_summary | text | ملخص مختصر للمدخلات |
| output_summary | text | ملخص مختصر للمخرجات |
| status | text | success / failed / pending |
| error_message | text | عند الفشل |
| created_at | timestamptz | |

---

## 7. Human Approval Queue — العمليات المحظورة تلقائياً

لا يتم تنفيذ الأمور التالية بدون موافقة بشرية:

- refund
- cancellation فيها تكلفة
- خصم استثنائي
- تعديل سعر يدوي كبير
- نشر محتوى عام
- إرسال رسالة حساسة أو شكوى كبيرة
- حذف بيانات أو booking
- أي إجراء مالي

→ تدخل `human_approval_queue` + إشعار Telegram للمدير.

---

## 8. Error Handling — المركزي

أي Sub-workflow يفشل:

1. يسجل في `workflow_failures` (أو `pending_messages` الموسَّع)
2. يحفظ payload الأساسي
3. لا تضيع العملية
4. يرسل تنبيه Telegram عند الحاجة
5. قابل لإعادة التشغيل (retry_count + status)

---

## 9. Gap Analysis

| المكون | موجود | ناقص | الأولوية |
|--------|--------|------|----------|
| Sales Agent (Laila) | ✅ 80% | lead_interactions, customer entity, approved stage | 🟡 |
| Pricing Agent | ✅ 90% | formal sub-workflow, PRICE_REVIEW routing | 🟡 |
| Booking Agent | ❌ 10% | tasks, supplier notify, lead↔booking link | 🔴 |
| Customer Service | 🟡 30% | reminders table, trip-based cron | 🟡 |
| Marketing Agent | 🟡 40% | content_queue exists, no agent workflow | 🟢 |
| Manager Agent | 🟡 25% | Admin /status basic, no full report | 🟡 |
| Orchestrator | ❌ | gateway + router | 🔴 |
| agent_actions | ❌ | full observability | 🔴 |
| human_approval_queue | ❌ | sensitive ops gate | 🔴 |
| Error handling / DLQ | 🟡 | pending_messages unused | 🟡 |
| n8n in Git | ❌ | version control | 🟡 |
| RLS security | ❌ | 25+ tables exposed | 🔴 |

---

## 10. Implementation Plan (مرتب بالأولوية والمخاطر)

### Phase 0 — Pre-req (أسبوع 0, zero risk)

- [ ] Export all n8n Arcadia workflows → Git
- [ ] Document webhook URLs + cron schedules
- [ ] Confirm Pricing Engine call path in Laila V5 JSON
- [ ] Backup Supabase schema

### Phase 1 — Foundation (low risk, no breaking changes)

**Risk: 🟢 Low | Impact: 🔴 High**

1. Create `lead_interactions` table
2. Create `agent_actions` table
3. Create `workflow_failures` (or activate `pending_messages`)
4. Create `human_approval_queue` table
5. Add nullable FKs to `bookings`: `lead_id`, `quote_ref`, `customer_id`
6. Add Laila V5 nodes: **INSERT lead_interactions** on every message (append-only)
7. Add Laila V5 nodes: **INSERT agent_actions** on pricing/booking events

**لا تلمس:** Laila prompts, Pricing RPC, Follow-up logic, Admin commands

### Phase 2 — Orchestrator Shell (medium risk)

**Risk: 🟡 Medium**

1. Create `Arcadia Gateway` webhook (normalize WA/TG payload)
2. Create `Arcadia Orchestrator` (intent classify + route)
3. **Parallel run:** Gateway → Orchestrator → **still calls existing Laila V5** as sub-workflow
4. Log routing in `agent_actions`

### Phase 3 — Booking Agent (priority #1 feature)

**Risk: 🟡 Medium**

1. Create `booking_tasks`, `booking_status_log`
2. Create `Arcadia - Booking Agent` sub-workflow
3. Trigger: `leads.stage = approved` (new stage)
4. Create booking + tasks + Telegram staff notify
5. Staff confirmation → update task → auto-update booking status

### Phase 4 — Laila Evolution → Sales Agent

**Risk: 🟡 Medium**

1. Add fields: hotel_category, budget, B2B/FIT, transport, tours
2. Don't repeat answered questions (read leads + lead_interactions)
3. Call Pricing sub-workflow via Orchestrator
4. Route to Booking on approval keywords

### Phase 5 — Manager Agent

**Risk: 🟢 Low (read-only)**

1. `Arcadia - Manager Report` cron 08:00 Almaty
2. SQL aggregates → Telegram
3. Extend Admin Commands to call same queries

### Phase 6 — Customer Service Agent

**Risk: 🟡 Medium**

1. `reminders` table
2. Cron based on `bookings.arrival_date`
3. Complaints → `complaints` + escalation rules

### Phase 7 — Marketing Agent (later)

**Risk: 🟢 Low**

1. Read itineraries + group_rates + approved offers
2. Write to content_queue
3. Human review only — no auto-publish

### Phase 8 — Security Hardening

**Risk: 🟡 Medium (can break if wrong)**

1. Enable RLS on sensitive tables with service_role bypass
2. Revoke anon write on leads, bookings, quotes

---

## 11. Phase 1 — ما سأعدّله بالضبط (للمراجعة قبل التنفيذ)

### ✅ WILL MODIFY (Phase 1 only)

| # | التعديل | النوع | Breaking? |
|---|---------|-------|-----------|
| 1 | SQL migration: `lead_interactions` | DDL new table | ❌ No |
| 2 | SQL migration: `agent_actions` | DDL new table | ❌ No |
| 3 | SQL migration: `human_approval_queue` | DDL new table | ❌ No |
| 4 | SQL migration: `workflow_failures` | DDL new table | ❌ No |
| 5 | SQL migration: `bookings` add nullable columns | DDL alter | ❌ No |
| 6 | SQL migration: `customers` table | DDL new | ❌ No |
| 7 | n8n Laila V5: add 2 Supabase INSERT nodes after reply | Workflow append | ❌ No |
| 8 | n8n Laila V5: add error branch → workflow_failures + Telegram alert | Workflow append | ❌ No |
| 9 | Git: add `n8n Workflows/` with exported JSONs | Docs | ❌ No |
| 10 | Git: add `Database/supabase_schema_multi_agent_phase1.sql` | Migration file | ❌ No |

### ❌ WILL NOT MODIFY (Phase 1)

- Laila V5 system prompt / AI Agent config
- Pricing Engine RPC functions
- Follow-up Cron timing/logic
- Admin Commands commands/logic
- `leads.stage` check constraint (until Phase 3)
- `bookings.status` values
- Any production webhook URLs
- Instagram / Website / Email gateways

### ⚠️ NEEDS YOUR INPUT BEFORE Phase 1

1. **Export n8n JSONs** — لا يمكن تعديل Laila بدونها
2. **Approve `approved` stage** — add to leads constraint in Phase 3 or now?
3. **`lead_state` vs `leads`** — activate lead_state or keep leads only?
4. **`quotes` vs `quote_offers`** — unified model or keep both?
5. **RLS hardening** — now or after Booking Agent stable?

---

## 12. SQL Skeleton — Phase 1 (for review, NOT applied)

```sql
-- Phase 1 ONLY — DO NOT RUN without approval

CREATE TABLE IF NOT EXISTS public.customers (
  customer_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  phone text UNIQUE NOT NULL,
  name text,
  email text,
  country_code text,
  preferred_language text DEFAULT 'ar',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.lead_interactions (
  interaction_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid REFERENCES public.leads(lead_id) ON DELETE SET NULL,
  customer_id uuid REFERENCES public.customers(customer_id) ON DELETE SET NULL,
  conversation_id uuid NOT NULL DEFAULT gen_random_uuid(),
  channel text NOT NULL CHECK (channel IN ('whatsapp','telegram','email','web','instagram')),
  direction text NOT NULL CHECK (direction IN ('inbound','outbound')),
  role text NOT NULL CHECK (role IN ('user','assistant','system','staff')),
  message_text text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX lead_interactions_lead_idx ON public.lead_interactions (lead_id, created_at DESC);
CREATE INDEX lead_interactions_conversation_idx ON public.lead_interactions (conversation_id, created_at);

CREATE TABLE IF NOT EXISTS public.agent_actions (
  action_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name text NOT NULL,
  action_type text NOT NULL,
  customer_id uuid REFERENCES public.customers(customer_id) ON DELETE SET NULL,
  lead_id uuid REFERENCES public.leads(lead_id) ON DELETE SET NULL,
  booking_id text REFERENCES public.bookings(booking_id) ON DELETE SET NULL,
  source_channel text,
  input_summary text,
  output_summary text,
  status text NOT NULL DEFAULT 'success' CHECK (status IN ('success','failed','pending')),
  error_message text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX agent_actions_agent_idx ON public.agent_actions (agent_name, created_at DESC);

CREATE TABLE IF NOT EXISTS public.human_approval_queue (
  approval_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  action_type text NOT NULL,
  lead_id uuid REFERENCES public.leads(lead_id) ON DELETE SET NULL,
  booking_id text REFERENCES public.bookings(booking_id) ON DELETE SET NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  reason text,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','expired')),
  requested_by_agent text,
  approved_by text,
  resolved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.workflow_failures (
  failure_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_name text NOT NULL,
  node_name text,
  agent_name text,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  error_message text NOT NULL,
  retry_count int NOT NULL DEFAULT 0,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','retrying','resolved','dead')),
  resolved_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.bookings
  ADD COLUMN IF NOT EXISTS lead_id uuid REFERENCES public.leads(lead_id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS customer_id uuid REFERENCES public.customers(customer_id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS quote_ref text;
```

---

## 13. Checklist — ما أحتاجه منك للمتابعة

```
[ ] 1. موافقة على Phase 1 scope أعلاه
[ ] 2. Export n8n workflows (Laila V5, Follow-up, Admin, Calculator, أي Arcadia*)
[ ] 3. تأكيد: Pricing Engine = Supabase RPC مباشرة أم webhook منفصل؟
[ ] 4. قرار lead_state: تفعيل أو إهمال
[ ] 5. قرار quotes vs quote_offers: توحيد أو فصل
[ ] 6. Telegram Admin chat_id للتنبيهات
[ ] 7. قائمة task_types للـ Booking Agent (hotel, transfer, tour, ...)
```

---

## 14. ملاحظة أمنية مهمة

Supabase Advisor يُظهر **25+ جدولاً بدون RLS** في schema `public` — بما فيها `leads`, `hotels`, `rate_plans`, `conversations`. أي شخص يملك `anon key` يمكنه قراءة/تعديل البيانات.

**لا أنصح بتفعيل RLS بدون policies** — سيكسر n8n. الخطة: Phase 8 بعد استقرار Agents، مع policies لـ `service_role` bypass.

---

**نهاية التقرير**

*Arcadia Tourism · Mohammad Ali · info@arcadia-tour.com · 27 أغسطس 2026*
