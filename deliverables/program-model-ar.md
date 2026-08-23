# نموذج البرامج B2B — أركاديا (كازاخستان / ألماتي)

> **المصدر المعتمد:** جدول `itineraries` في Supabase — `country = Kazakhstan`، مفتاح البرنامج `notes_ar` (مثل `nights:5`, `nights:6`).

## القاعدة

1. **البرنامج الأساسي** = أول N أيام من برنامج معتمد في DB (مدينة وألماتي القريبة فقط: ميديو، شيمبولاك، كوك توبه، السوق الأخضر، أوي كاراجاي، وادي الما-أرسان، إلخ).
2. **B2B 5 أيام / 4 ليالي** = `notes_ar: nights:4` — مشتق من `nights:5` أيام 1–5 (اليوم الأخير يدمج التسوق/كوك توبه + المغادرة).
3. **إضافات اختيارية منفصلة** — ليست في السعر الأساسي ولا في `entrances` ضمن `group_rates`:
   - وادي شارين (Charyn / Sharyn)
   - بحيرات كولساي (Kolsai)
   - بحيرة كايندي (Kaindy)
4. **التسعير B2B** = جدول `group_rates` — KZ / Almaty / 4N — شرائح 15–19 / 20–29 / 30–40 pax.

## تقطيع البرامج (slice)

| الليالي | أيام البرنامج | مفتاح DB | ملاحظة |
|--------|---------------|----------|--------|
| 4N | 5 | `nights:4` | B2B أساسي — PDF rate sheet |
| 5N | 6 | `nights:5` | برنامج FIT معتمد |
| 6N | 7 | `nights:6` | + حديقة مركزية / يوم تسوق إضافي |
| 7N | 8 | `nights:7` | + وادي بوتاكوفكا |

## ملفات التسليم

| الملف | الغرض |
|------|--------|
| `deliverables/pdfs/Arcadia-B2B-Rate-Sheet-Almaty.html` | HTML ASCII للشريك |
| `deliverables/pdfs/Arcadia-B2B-Rate-Sheet-Almaty.pdf` | PDF معتمد |
| `deliverables/templates/pdf-group-rate-sheet-en.html` | قالب EN |
| `deliverables/templates/b2b-ground-handling-agreement-en.html` | **قالب عقد B2B ground handling (EN)** — للتوقيع بعد LOI/اجتماع |
| `deliverables/contracts/` | (مستقبلاً) نسخ موقّعة PDF |
| `Database/seed_itinerary_kz_b2b_4n.sql` | إدراج `nights:4` |
| `Database/update_group_rates_kz_b2b_4n.sql` | تحديث `includes_json` |

## SQL للتشغيل (إن لم تُطبّق بعد)

```sql
-- 1) برنامج B2B 4N في itineraries
\i Database/seed_itinerary_kz_b2b_4n.sql

-- 2) تحديث group_rates (إزالة شارين/كولساي من entrances)
\i Database/update_group_rates_kz_b2b_4n.sql
```

---

*Arcadia Tourism · Mohammad Ali · info@arcadia-tour.com*
