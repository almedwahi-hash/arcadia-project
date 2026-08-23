# سجل إرسال outreach — الدفعة 4 | أركاديا السياحية

> **From:** info@arcadia-tour.com  
> **التوقيع:** Mohammad Ali — Business Development Manager  
> **المرفق:** ❌ PDF مرفق آليًا محظور — ✅ رابط `https://arcadia-tour.com/` في نص كل رسالة  
> **التحقق:** مجلد **Отправленные (Sent)** في Zoho Mail

---

## ملخص تنفيذي (مُحدَّث 25 يونيو 2026)

| المؤشر | القيمة |
|--------|--------:|
| **إجمالي الأهداف** | **16** |
| **مُؤكَّد في Sent (Zoho)** | **16** |
| **معلق** | **0** |
| **آخر إرسال SMTP** | 25 يونيو 2026 — **12/12** (#5–16) + **4/4** سابقاً (#1–4) |

---

## جدول الإرسال — حالة مُحقَّقة

| # | الشركة | To | Subject | الحالة | التوقيت (Almaty) | مرفق |
|---|--------|-----|---------|--------|------------------|------|
| 1 | Musafir | holidays@musafir.com | Central Asia B2B Supplier — Kazakhstan Groups for Arabic Market \| Arcadia Tourism | ✅ **مؤكَّد Sent** | 19 يون ~1:26 AM | pdf_link |
| 2 | Arooha Leisure | mail@aroohaleisure.com | B2B Ground Partner — Kazakhstan Group Tours from Dubai \| Arcadia Tourism × Arooha | ✅ **مؤكَّد Sent** | 19 يون ~2:05 AM | pdf_link |
| 3 | CTC Travel | enquiry@ctc.com.sg | B2B Ground Partner — Grand Silk Road 2026 Almaty Segment \| Arcadia Tourism | ✅ **مؤكَّد Sent** | 19 يون ~2:07 AM | pdf_link |
| 4 | Regency Travel | tours@regencyholidays.com | B2B Ground Partner — Kazakhstan & Central Asia Groups \| Arcadia Tourism × Regency | ✅ **مؤكَّد Sent** | 19 يون ~9:22 PM | pdf_link |
| 5 | Siyana Travel | info@siyanatours.com | B2B Ground Rates — Almaty & Tashkent Groups \| Arcadia Tourism × Siyana | ✅ **مؤكَّد Sent** | 25 يون ~8:19 PM | pdf_link |
| 6 | Tailwinds Travels | info@tailwindstravels.co | B2B Ground Partner — 12N Central Asia Group Tours \| Arcadia Tourism (Almaty) | ✅ **مؤكَّد Sent** | 25 يون ~8:19 PM | pdf_link |
| 7 | Rose Travel | info@rosetravel.sa | B2B Ground Partner — Kazakhstan & Russia Groups \| Arcadia Tourism × Rose Travel | ✅ **مؤكَّد Sent** | 25 يون ~8:20 PM | pdf_link |
| 8 | Chan Brothers | inquiry@chanbrothers.com.sg | B2B Ground Rates — Central Asia Group Series \| Arcadia Tourism × Chan Brothers | ✅ **مؤكَّد Sent** | 25 يون ~8:20 PM | pdf_link |
| 9 | Villa Tours | villatourstravel@yahoo.co.id | B2B Ground Partner — 3–5 Stans Halal Groups \| Arcadia Tourism (Almaty) | ✅ **مؤكَّد Sent** | 25 يون ~8:21 PM | pdf_link |
| 10 | Kanoo Travel | bdm.travel@kanoo.com | Central Asia B2B Ground — Group Holidays \| Arcadia Tourism × Kanoo | ✅ **مؤكَّد Sent** | 25 يون ~8:21 PM | pdf_link |
| 11 | Asia Odyssey | inquiry@asiaodysseytravel.com | B2B Ground Partner — Central Asia Groups from Singapore \| Arcadia Tourism | ✅ **مؤكَّد Sent** | 25 يون ~8:22 PM | pdf_link |
| 12 | Middle East Expeditions | admin@asia-expeditions.org | B2B Ground Partnership — Central Asia Expedition Groups \| Arcadia Tourism | ✅ **مؤكَّد Sent** | 25 يون ~8:22 PM | pdf_link |
| 13 | Alghanim Travel | travelcare@alghanimtravel.com | B2B Supplier — Kazakhstan Group Holidays \| Arcadia Tourism × Alghanim | ✅ **مؤكَّد Sent** | 25 يون ~8:23 PM | pdf_link |
| 14 | Al Sabah Travels | sales@alsabahtravel.com | B2B Ground Partner — Silk Road Group Tours \| Arcadia Tourism | ✅ **مؤكَّد Sent** | 25 يون ~8:23 PM | pdf_link |
| 15 | FTTC | info@fttc-global.com | B2B Ground Partner — Central Asia Groups \| Arcadia Tourism × FTTC | ✅ **مؤكَّد Sent** | 25 يون ~8:24 PM | pdf_link |
| 16 | Masalamaa | info@masalamaa.com | B2B Ground Partner — Halal Central Asia Groups \| Arcadia Tourism | ✅ **مؤكَّد Sent** | 25 يون ~8:24 PM | pdf_link |

**الإجمالي: 16/16 مُؤكَّد ✅**

---

## محاولات الإرسال (25 يونيو 2026)

| الطريقة | النتيجة |
|---------|---------|
| **A) Zoho SMTP (Python)** | ✅ **16/16** — #1–4 (19 يون) + #5–16 (25 يون ~20:19–20:24 Almaty) عبر `scripts/send_batch4_outreach.py` / SMTP مباشر |
| **B) n8n webhook** | ❌ لا workflow لـ `info@` — غير مستخدم |
| **C) Browser MCP (Zoho UI)** | ❌ غير مطلوب — SMTP نجح |

---

## حماية إعادة التشغيل

| الملف | الغرض |
|-------|--------|
| `.tmp_batch4_remaining.json` | **فارغ** — لا أهداف معلّقة |
| `.tmp_batch4_sent.json` | سجل idempotent — 16/16 مُسجَّل |
| `scripts/send_batch4_outreach.py` | يقرأ **فقط** من remaining + يتخطى المُرسَل في sent log |

**إعادة تشغيل السكربت:** 0 رسائل (remaining فارغ + sent log كامل).

---

*25 يونيو 2026 — **16/16 مُؤكَّد ✅** — الدفعة 4 مكتملة*
