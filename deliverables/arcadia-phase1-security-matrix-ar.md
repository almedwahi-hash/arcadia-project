# Security Matrix — Supabase Arcadia (قبل أي تغيير Policy)

**التاريخ:** 27 أغسطس 2026  
**Project:** `xfibcjhshpmqkrhlpsoa`  
**الغرض:** توثيق GRANTs + RLS الفعلية قبل Phase 1 — **لم يُغيّر أي policy على الجداول الموجودة**

---

## 1. كيف يعمل الوصول في Supabase

| Role | الاستخدام | يتجاوز RLS؟ |
|------|-----------|-------------|
| **service_role** | n8n, scripts خلفية | ✅ نعم |
| **anon** | مفاتيح عامة / PostgREST | ❌ يخضع لـ RLS إن مفعّل |
| **authenticated** | مستخدم مسجّل | ❌ يخضع لـ RLS |

**قاعدة:** إذا RLS **معطّل** لكن GRANTs كاملة → **anon يقرأ/يكتب كل الصفوف**.

---

## 2. Matrix — جداول حرجة (مُفحوص مباشرة)

| Table | RLS | anon GRANTs | authenticated GRANTs | Effective anon access |
|-------|-----|-------------|----------------------|------------------------|
| **leads** | ❌ OFF | SELECT, INSERT, UPDATE, DELETE, TRUNCATE | نفس الكل | 🔴 **Full read/write** |
| **conversations** | ❌ OFF | Full | Full | 🔴 **Full read/write** |
| **hotels** | ❌ OFF | Full | Full | 🔴 **Full read/write** |
| **rate_plans** | ❌ OFF | Full | Full | 🔴 **Full read/write** |
| **quotes** | ✅ ON | Full GRANTs | Full GRANTs | 🟡 يعتمد policies |
| **bookings** | ✅ ON | Full GRANTs | Full GRANTs | 🟡 يعتمد policies |
| **group_rates** | ✅ ON | **SELECT only** | لا يظهر في الفحص | 🟢 قراءة فقط (إن وُجد policy) |
| **lead_state** | ✅ ON | Full GRANTs | Full GRANTs | 🟡 policies غير موجودة = blocked? |
| **content_queue** | ✅ ON | Full GRANTs | Full GRANTs | 🟡 |
| **itineraries** | ✅ ON | Full GRANTs | Full GRANTs | 🟡 |
| **quote_offers** | ✅ ON | (revoked in schema file) | revoked | 🟢 service_role فقط |

### تفسير `lead_state` (RLS ON + no policies)

Supabase advisor: **RLS enabled, no policy** → anon/authenticated **لا يصلون** حتى مع GRANTs (Postgres يمنع بدون policy مطابقة).

### تفسير `leads` (RLS OFF + full GRANTs)

**أخطر سطح:** أي holder لـ `anon key` يمكنه تعديل كل leads.

---

## 3. Matrix — جداول Phase 1 (بعد migration)

| Table | RLS | anon | authenticated | service_role |
|-------|-----|------|---------------|--------------|
| **customers** | ✅ ON | REVOKE ALL | REVOKE ALL | implicit full |
| **lead_interactions** | ✅ ON | REVOKE ALL | REVOKE ALL | implicit full |
| **agent_actions** | ✅ ON | REVOKE ALL | REVOKE ALL | implicit full |
| **human_approval_queue** | ✅ ON | REVOKE ALL | REVOKE ALL | implicit full |
| **workflow_failures** | ✅ ON | REVOKE ALL | REVOKE ALL | implicit full |

**لا policies لـ anon** على الجداول الجديدة → **blocked لـ anon** — n8n فقط عبر service_role.

---

## 4. ما لم يُغيّر في Phase 1 (حسب موافقتك)

- ❌ لا تفعيل RLS على `leads`, `hotels`, `rate_plans`, `conversations`
- ❌ لا revoke على جداول production موجودة (قد يكسر ops app / أدوات)
- ❌ لا policies جديدة على جداول legacy

**Phase 8** (مؤجّل): RLS + policies بعد استقرار Agents.

---

## 5. توصيات قبل تغيير أي policy

1. **لا تفعّل RLS على `leads` بدون policy لـ service_role + ops app**
2. **احصر anon key** — لا تضعه في frontend عام
3. **راجع ops internal app** — يستخدم anon أم service_role؟
4. **اختبار:** `curl` مع anon key على `leads` — إن نجح INSERT = تأكيد المخاطرة

---

## 6. Checklist Security (Phase 1)

```
[x] Security matrix documented
[x] New tables: RLS ON + REVOKE anon/authenticated
[x] Existing tables: unchanged privileges
[ ] Owner: confirm ops app auth method before Phase 8 RLS
[ ] Owner: rotate anon key if ever exposed publicly
```

---

*Arcadia Tourism · Phase 1 Security Matrix · لا يُعدّل policies بدون مراجعة هذا الملف*
