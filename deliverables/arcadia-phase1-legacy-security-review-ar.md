# Security Review — Legacy Tables (Phase 1)

**التاريخ:** 27 أغسطس 2026  
**Project:** `xfibcjhshpmqkrhlpsoa`  
**المنهج:** GRANTs + RLS policies + RPC EXECUTE + استخدامات موثّقة في repo/docs  
**لم يُغيّر:** أي RLS أو GRANT في هذا المراجعة

---

## ملخص سريع

| Table | RLS | anon effective today | أخطر سطح |
|-------|-----|----------------------|----------|
| leads | OFF | SELECT+INSERT+UPDATE+DELETE | 🔴 write مفتوح |
| hotels | OFF | full | 🔴 write مفتوح |
| room_types | OFF | full | 🔴 write مفتوح |
| rate_plans | OFF | full | 🔴 write مفتوح |
| seasons | OFF | full | 🔴 write مفتوح |
| services | OFF | full | 🔴 write مفتوح |
| quotes | ON | SELECT+INSERT+UPDATE (policies) | 🟡 write مقصود للموقع |
| bookings | ON | ALL (policy `Allow all on bookings`) | 🟡 internal app |

**RPC:** `quote_package`, `quote_multi`, `list_hotels` — **anon EXECUTE ✅**  
عند **SECURITY INVOKER** (الحالة الحالية): الـ RPC يحتاج **anon SELECT** على جداول التسعير.

---

## 1. leads

| Permission | anon يحتاج؟ | السبب |
|------------|-------------|-------|
| SELECT | 🟡 محتمل | لا يوجد في repo — الموقع يوجّه لواتساب |
| INSERT | ❌ لا | n8n يستخدم **service_role** |
| UPDATE | ❌ لا | n8n service_role |
| DELETE | ❌ لا | لا استخدام موثّق |

**المستخدم فعلياً:** n8n Laila V5 (**service_role**), Admin Commands (**service_role**), Follow-up Cron (**service_role**)

**التوصية المبكرة (اقتراح فقط):**
```sql
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.leads FROM anon, authenticated;
-- احتفظ SELECT مؤقتاً إن وُجد عميل يقرأ leads؛ أو REVOKE ALL إن لا يوجد
```
**تحقق قبل التطبيق:** internal ops app لا يستخدم anon على `leads`.

---

## 2. hotels

| Permission | anon يحتاج؟ | السبب |
|------------|-------------|-------|
| SELECT | ✅ نعم | `quote_package()` invoker يقرأ hotels |
| INSERT | ❌ لا | إدارة عقود داخلية |
| UPDATE | ❌ لا | |
| DELETE | ❌ لا | |

**المستخدم فعلياً:** Supabase RPC **quote_package/quote_multi** (anon EXECUTE), n8n pricing (**service_role**), محتمل website quote widget

**التوصية المبكرة:**
```sql
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.hotels FROM anon, authenticated;
-- GRANT SELECT فقط إن RPC يبقى invoker
```

---

## 3. room_types

| Permission | anon يحتاج؟ | السبب |
|------------|-------------|-------|
| SELECT | ✅ نعم | سلسلة تسعير الفنادق عبر RPC |
| INSERT/UPDATE/DELETE | ❌ لا | |

**المستخدم:** RPC pricing, service_role admin

**التوصية المبكرة:** REVOKE write (مثل hotels)

---

## 4. rate_plans

| Permission | anon يحتاج؟ | السبب |
|------------|-------------|-------|
| SELECT | ✅ نعم | RPC يقرأ أسعار الغرف |
| INSERT/UPDATE/DELETE | ❌ لا | |

**المستخدم:** RPC pricing, service_role

**التوصية المبكرة:** REVOKE write

---

## 5. seasons

| Permission | anon يحتاج؟ | السبب |
|------------|-------------|-------|
| SELECT | ✅ نعم | RPC season filter |
| INSERT/UPDATE/DELETE | ❌ لا | |

**المستخدم:** RPC pricing

**التوصية المبكرة:** REVOKE write

---

## 6. services

| Permission | anon يحتاج؟ | السبب |
|------------|-------------|-------|
| SELECT | ✅ نعم | RPC transfers/tours/guides |
| INSERT/UPDATE/DELETE | ❌ لا | |

**المستخدم:** RPC pricing

**التوصية المبكرة:** REVOKE write

---

## 7. quotes

| Permission | anon يحتاج؟ | السبب |
|------------|-------------|-------|
| SELECT | ✅ نعم | policy `Allow public read` |
| INSERT | ✅ نعم | policy `Allow public insert` — أرشفة عروض |
| UPDATE | ✅ نعم | policy `Allow public update` |
| DELETE | ❌ لا | لا policy delete — لكن GRANT DELETE موجود |

**المستخدم:** website quote flow (محتمل), n8n Laila (**service_role**), Pricing archive

**التوصية المبكرة:**
```sql
REVOKE DELETE, TRUNCATE ON public.quotes FROM anon, authenticated;
-- لا تسحب INSERT/UPDATE دون تأكيد أن الموقع لا يعتمد عليهما
```

---

## 8. bookings

| Permission | anon يحتاج؟ | السبب |
|------------|-------------|-------|
| SELECT | ✅ نعم | internal ops app (147 سجل) |
| INSERT | ✅ نعم | policy `Allow all on bookings` |
| UPDATE | ✅ نعم | ops app تعديل حالة/دفع |
| DELETE | 🟡 غير معروف | policy ALL — مفعّل فعلياً |

**المستخدم:** **Internal ops app** (`app_users` — 3 users), ليس n8n Laila مباشرة

**التوصية المبكرة:** **لا REVOKE الآن** — يكسر ops app. Phase 8: policies per role + auth.

---

## 9. إجراء أمني مبكر مقترح (مجمّع)

**يمكن تطبيقه بأمان بعد تأكيد واحد:** ops app لا يكتب `leads` بـ anon.

```sql
-- Phase 1b early hardening (NOT APPLIED — proposal)
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.leads FROM anon, authenticated;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.hotels FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.room_types FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.rate_plans FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.seasons FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.services FROM anon, authenticated;

REVOKE DELETE, TRUNCATE ON public.quotes FROM anon, authenticated;
```

**لا يُطبَّق في Phase 1** حتى تأكيد المالك.

---

## 10. lead السابع غير المرتبط

| lead_id | السبب |
|---------|-------|
| `ac65db07-e65c-4033-9ddc-5f17893da76b` | `phone` = سلسلة فارغة (`length(trim(phone)) = 0`) — backfill يتخطى `trim(phone) <> ''` |

**إصلاح:** لا يُنشأ `customer` بلا phone (يفسد UNIQUE/CRM). **إجراء مقترح:** `needs_human = true` + مراجعة يدوية أو حذف lead وهمي.

---

*لا تغييرات policy في هذا الملف — مراجعة فقط*
