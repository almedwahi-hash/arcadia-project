# Arcadia Phase 2.6 — تقرير مساعد عمليات الموردين

**تاريخ الاختبار:** 2026-08-28  
**النتيجة:** 10/10 ✅  
**حجز Canary:** `RU-2026-032` · مهمة `hotel:moscow:1`

---

## الهدف

بعد إنشاء Booking Agent للحجز والمهام، يساعد النظام موظفي Arcadia في تنفيذ حجوزات الموردين **بدون صلاحية دفع**.

**التدفق:** `booking_task` → مسودة طلب مورد → معاينة Telegram → موظف يضغط «تم الإرسال يدويًا»

---

## تدقيق بيانات المورد (قبل إنشاء جداول مكررة)

| المصدر | الاستخدام |
|--------|-----------|
| `hotels` | اسم الفندق، المدينة، الهاتف، البريد، المورد |
| `booking_tasks` | supplier_name, supplier_channel, confirmation_ref, due_at, metadata |
| `rh_hotel_cache` | موجود — لم يُ duplicated |

**جداول جديدة فقط:**
- `booking_supplier_drafts` — مسودات المعاينة (لا إرسال تلقائي)
- `booking_supplier_responses` — رد المورد (confirmed / unavailable / waiting / …)
- `booking_task_reminder_log` — dedupe للتذكيرات

---

## السياسات المفعّلة

- `booking_handoff_enabled = false` عالميًا — Canary عبر `canary_lead_ids` فقط
- `/book <lead_id> <quote_ref>` يبقى fallback آمن
- `auto_send_enabled = false` — لا رسائل للمورد تلقائيًا
- `booking_task_reminder_policy.enabled = false` — مراقب التذكيرات معطّل
- لا دفع، لا استرداد، لا Orchestrator، لا تغيير Laila

---

## نتائج Canary (10/10)

| # | الاختبار | النتيجة |
|---|----------|---------|
| 1 | مهمة مورد صحيحة + حقائق الحجز في المسودة | ✅ |
| 2 | توليد مسودة idempotent | ✅ |
| 3 | بيانات ناقصة → `needs_information` | ✅ |
| 4 | لا إرسال تلقائي للمورد | ✅ |
| 5 | موظف مصرّح يعلّم «تم الإرسال» | ✅ |
| 6 | تكرار «تم الإرسال» idempotent | ✅ |
| 7 | تأكيد المورد + confirmation_ref | ✅ |
| 8 | إعادة حساب lifecycle | ✅ |
| 9 | موظف غير مصرّح م blocked | ✅ |
| 10 | لا مدفوعات + handoff معطّل + لا workflow_failures | ✅ |

---

## مثال مسودة فندق (Brosko Hotel — Moscow)

```
Arcadia Tourism — Hotel Reservation Request
(DRAFT — staff review; NOT sent automatically)

Booking reference: RU-2026-032
Hotel: Brosko Hotel
City: Moscow
Check-in: 2026-11-17
Check-out: 2026-11-27
Guests: 5 pax
...
NOT sent — staff must send manually
```

---

## Telegram Booking Ops — callbacks جديدة

- `bk:task:{id}:open` — فتح المهمة
- `bk:task:{id}:draft` — توليد مسودة
- `bk:draft:{id}:preview` — معاينة
- `bk:draft:{id}:mark_sent` — تم الإرسال يدويًا
- `bk:task:{id}:resp:{type}` — تسجيل رد المورد

---

## STOP — ما لم يُفعّل

- ❌ handoff تلقائي للجميع
- ❌ إرسال تلقائي للموردين
- ❌ حجز بوابات فنادق
- ❌ دفع موردين / تحصيل / استرداد

---

## الخطوة التالية (بعد فترة Canary حقيقية)

الموظف يراجع المسودة الجاهزة ويرسلها بنفسه. بعد التأكد من دقة المورد والبيانات، نقرر إن كان بعض الموردين الموثوقين يستحقون إرسالًا تلقائيًا — **بدون صلاحية مالية**.

*Arcadia Tourism · Phase 2.6 · STOP*
