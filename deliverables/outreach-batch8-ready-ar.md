# Batch 8 — جاهز للإرسال (الموجة 1 مكتملة)

> **التاريخ:** 2026-07-09  
> **الحالة:** ✅ **الموجة 1: DONE** — **15/48 مُرسَل** (14 وصل + 1 ارتد) | ⏸️ **الموجة 2: 33 متبقياً** بانتظار موافقة  
> **المصدر:** `deliverables/b2b-database-batch8-new.csv` (48 موثّقة)  
> **From:** info@arcadia-tour.com | **PDF:** `deliverables/pdfs/Arcadia-B2B-Rate-Sheet-Almaty.pdf`

---

## 1. ملخص

| البند | العدد |
|-------|------:|
| **إجمالي قائمة الانتظار** | **48** |
| **Priority A** (فيتنام، UK، الفلبين، كوريا، الأردن) | **31** |
| **Priority B** (اليابان، الهند، تركيا، HK، SG/MY/ID) | **13** |
| **Priority C** (المغرب، مصر) | **4** |
| **مُرسَل (الموجة 1)** | **15** |
| **متبقٍ (الموجة 2)** | **33** |

**ترتيب القائمة:** فيتنام → UK → الفلبين → كوريا → الأردن → باقي الأسواق (B ثم C).

---

## 2. الموجة الأولى — Tier A (أفضل 15) ✅ DONE

| # | Company | Country | Email | الحالة |
|---|---------|---------|-------|--------|
| 1 | Authentic Asia | Vietnam | sales@authentic-asia.com | ✅ sent |
| 2 | DH Travel (Du Lich Quoc Te DH) | Vietnam | director@dhtravel.com.vn | ✅ sent |
| 3 | Fiditour JSC | Vietnam | info@fiditour.com | ✅ sent |
| 4 | HaloBay Travel | Vietnam | info@halobay.vn | ⚠️ sent → bounced |
| 5 | Le Phong Travel | Vietnam | info@lephongtravel.com.vn | ✅ sent |
| 6 | Mai Tours | Vietnam | info@maitours.vn | ✅ sent |
| 7 | Premier Tour Vietnam | Vietnam | info@premiertour.com.vn | ✅ sent |
| 8 | Saigontourist Travel | Vietnam | info@saigontourist.net | ✅ sent |
| 9 | VGC Travel | Vietnam | info@vgctravel.com.vn | ✅ sent |
| 10 | Vietrantour | Vietnam | booking@vietrantour.com.vn | ✅ sent |
| 11 | Exodus Adventure Travels | United Kingdom | privatedepartures@exodus.co.uk | ✅ sent |
| 12 | Go Russia Ltd | United Kingdom | info@justgorussia.co.uk | ✅ sent |
| 13 | HF Holidays | United Kingdom | groups@hfholidays.co.uk | ✅ sent |
| 14 | Jules Verne (VJV) | United Kingdom | agents@vjv.com | ✅ sent |
| 15 | Regent Holidays | United Kingdom | regent@regentholidays.co.uk | ✅ sent |

> **السجل التفصيلي:** `deliverables/outreach-sent-log-batch8-ar.md` | **الملف الآلي:** `.tmp_batch8_sent.json`

---

## 3. الموجة الثانية — 33 هدفاً ⏸️ بانتظار الموافقة

| البند | القيمة |
|-------|--------|
| **الأهداف** | #16 Steppes Travel → #48 |
| **الملف** | `.tmp_batch8_remaining.json` |
| **الحالة** | لم يُرسَل شيء — بانتظار موافقة المستخدم الصريحة |

---

## 4. تشغيل SMTP (نفس نمط Batch 6/7)

> **تذكير:** أرفق `Arcadia-B2B-Rate-Sheet-Almaty.pdf` مع كل رسالة.
> **ملاحظة:** الموجة 1 أُرسلت عبر **Zoho Webmail (متصفح)** — SMTP غير متاح من بيئة sandbox.

```powershell
python scripts/batch8_targets.py
python scripts/send_batch8_outreach.py --build-from-md --dry-run
python scripts/send_batch8_outreach.py --only 1 --delay 0
python scripts/send_batch8_outreach.py --delay 3
```

| البند | المسار |
|-------|--------|
| قائمة الانتظار | `deliverables/outreach-batch8-queue.csv` |
| JSON المعلّق | `.tmp_batch8_remaining.json` |
| سجل المُرسَل | `.tmp_batch8_sent.json` |
| إصلاح SMTP | `deliverables/email-smtp-fix-ar.md` |

**Idempotent:** يتخطى أي email موجود في sent log أو `exclude_emails.txt`.

---

*Batch 8 outreach — 15/48 sent (wave 1 DONE) — 33 pending (wave 2) — لا إرسال للموجة 2 حتى موافقة صريحة*
