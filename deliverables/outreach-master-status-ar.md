# Outreach Master Status | أركاديا السياحية

> **آخر تحديث:** 2026-08-24 ~03:00 Almaty (UTC+5)  
> **From:** info@arcadia-tour.com  
> **SMTP:** ✅ Zoho `smtp.zoho.eu:465` — Batch 11 A/B/C

---

## ملخص تنفيذي

| المؤشر | القيمة |
|--------|--------:|
| **إجمالي مُرسَل (فريد تقريباً)** | **~140+** |
| **Batch 4** | 16/16 ✅ |
| **Batch 5** | 28/28 ✅ (browser + SMTP سابق) |
| **GCC follow-ups** | 5/5 ✅ |
| **Batch 6** | **18/18 ✅** (SMTP 2026-07-05 ~02:39–02:41) |
| **Batch 7** | **45/45 ✅** (موجتان: 19 موثّقة @03:58 + 26 جديدة @04:15) |
| **Batch 8 — الموجة 1** | **15/15 مُرسَل** (14 وصل، 1 ارتد — HaloBay) عبر Zoho Webmail 2026-07-09 21:32–22:45 |
| **Batch 8 — الموجة 2** | **33/33 مُرسَل** — ⚠️ **24 وصل مؤكَّد، 7 ارتد، 2 متأخر** (مُصحَّح 2026-07-11 بعد مراجعة صندوق الوارد) |
| **إجمالي Batch 8 الفعلي** | 38/48 وصل مؤكَّد، 8 ارتد، 2 معلّق |
| **Batch 9 — email FU** | **Hot 2 + GCC 5 + Tier NEXT 8 = 15/15 ✅** (2026-07-17 SMTP) |
| **Batch 10 — RIGHT cold** | **18/18 ✅** (2026-07-17 05:35–05:48 · PDF · تأخير 45ث · 0 فشل) |
| **Dynasty DMC form** | ⛔ ملف `.docx` غير موجود — تخطّي إرفاق · انتظر pax/dates |
| **أسعار** | ✅ مطابقة Supabase: $745/685/625 (15–19/20–29/30–40 pax، Jun–Oct 2026) |

---

## حالة SMTP

| البند | الحالة |
|-------|--------|
| **Auth** | ✅ LOGIN OK |
| **Send** | ✅ بعد إصلاح `formataddr` From |
| **553 root cause** | em dash خام في From → Zoho relay reject |
| **التوثيق** | `deliverables/email-smtp-fix-ar.md` |
| **اختبار** | `scripts/test_smtp_fix.py --send` |

---

## Batch 6 (18)

| # | Company | Email | Status |
|---|---------|-------|--------|
| 1–18 | (انظر `sales-outreach-batch6-targets-ar.md`) | various | ✅ **18/18 sent** via SMTP |

**Log:** `.tmp_batch6_sent.json`  
**Script:** `scripts/send_batch6_outreach.py`

---

## Batch 7 (45 = 19 + 26 — deduped)

**الموجة 1 (03:58–04:00): الوكالات الـ19 الموثّقة** من `b2b-database-master-verified.csv` — AFC Holidays، Travelon، Al Hashar، Sabsan، Mahira، Adinda Azzahra، Travel Knits، Aataa، Saraya، Wejhats، Tarteeb، ATT Oman، Taal، RAG، Holidaymakers، Dook، Shikhar، Hamidah، ARS — كلها ✅ sent (سجل `.tmp_batch7_sent.json`).

**الموجة 2 (04:15–04:16): 26 هدفاً إضافياً** أدناه. التقرير الكامل: `batch7-send-report-ar.md`.

| # | Company | Email | Status |
|---|---------|-------|--------|
| 1 | Rayna Tours (B2B desk) | b2b@raynab2b.com | ✅ sent |
| 2 | Energy Travel | info@energytravels.ae | ✅ sent |
| 3 | Orient Travel | info@orienttravels.com | ✅ sent |
| 4 | Orient Travel (Support) | support@orienttravels.com | ✅ sent |
| 5 | Aamal Travel (Outbound) | outbound@aamal-travel.com | ✅ sent |
| 6 | Veena World | travel@veenaworld.com | ✅ sent |
| 7 | Veena World (Inbound) | inbound@veenaworld.com | ✅ sent |
| 8 | SOTC (MICE Plus) | incentive.travel@sotc.in | ✅ sent |
| 9 | Panorama JTB (Tours) | tours@panorama-jtb.com | ✅ sent |
| 10 | Panorama JTB (Contact Center) | contactcenter@panorama-jtb.com | ✅ sent |
| 11 | Aviatour | aviatour@avia-tour.com | ✅ sent |
| 12 | Namira Tour | namiratour@yahoo.co.id | ✅ sent |
| 13 | Silk Road Holiday (SG) | hello@silkroadholiday.com | ✅ sent |
| 14 | Pattours | thienduongachau@gmail.com | ✅ sent |
| 15 | Pattours (Ops) | dieuhanh@thienduongachau.vn | ✅ sent |
| 16 | Setur | info@setur.com.tr | ✅ sent |
| 17 | Hana Tour | 15771233@hanatour.com | ✅ sent |
| 18 | Veena World (Corporate) | guestconnect@veenaworld.com | ✅ sent |
| 19 | Pattours (alt) | vietnampattours@gmail.com | ✅ sent |
| 20 | Aviatour (web) | aviaweb@avia-tour.com | ✅ sent |
| 21 | Ajwa Travel | info@ajwatravel.net | ✅ sent |
| 22 | ViaVacation | info@viavacation.my | ✅ sent |
| 23 | Dynasty Travel | enquiries@dynastytravel.com.sg | ✅ sent |
| 24 | Apple Vacations | enquiry@applevacations.my | ✅ sent |
| 25 | Jumbo Travel Kuwait | hello@jumbotravels.com | ✅ sent |
| 26 | Citron (Holidays desk) | holidays@citrontours.ae | ✅ sent |

**Log:** `.tmp_batch7_sent.json` | **Targets:** `deliverables/sales-outreach-batch7-targets-ar.md`

---

## السكربتات

| Script | JSON | Sent log |
|--------|------|----------|
| `send_batch4_outreach.py` | `.tmp_batch4_remaining.json` | `.tmp_batch4_sent.json` |
| `send_batch5_outreach.py` | `.tmp_batch5_remaining.json` | `.tmp_batch5_sent.json` |
| `send_batch6_outreach.py` | `.tmp_batch6_remaining.json` | `.tmp_batch6_sent.json` |
| `send_batch7_outreach.py` | `.tmp_batch7_remaining.json` | `.tmp_batch7_sent.json` |
| `send_batch9_tier_next_followup.py` | `.tmp_batch9_tier_next_followup.json` | `.tmp_batch9_tier_next_followup_sent.json` |
| `send_batch10_outreach.py` | `.tmp_batch10_emails.json` | `.tmp_batch10_sent.json` |
| `send_batch11_outreach.py` | `.tmp_batch11_emails.json` | `.tmp_batch11_sent.json` |

**Idempotent:** يتخطى أي email موجود في sent log — dedupe عبر `batch7_targets.collect_sent_emails()`.

---

## Browser fallback (غير مطلوب حالياً)

SMTP يعمل — **لا bulk browser**. إذا عاد 553: راجع `email-smtp-fix-ar.md` §6 + خطة 20+ رسالة في `deliverables/outreach-manual-send-checklist-ar.md`.

---

*Master status — 17 Jul 2026 — SMTP ✅ | Batch 9 FU 15/15 | Batch 10 RIGHT 18/18 (0 فشل) | التالي: ردود pax/dates → quote ≤24س*

---

## Batch 9 (email-first follow-ups) — 2026-07-17

| موجة | النتيجة |
|------|---------|
| Hot (Hayatun · SGTREK) | ✅ 2/2 |
| GCC 5 thread Reply | ✅ 5/5 |
| Tier NEXT (Siyana…CTC) | ✅ 8/8 |
| Dynasty DMC form attach | ⛔ تخطّي — لا ملف `.docx` |

**سجل:** `outreach-sent-log-batch9-ar.md`

## Batch 10 (RIGHT close cold) — 2026-07-17

| البند | القيمة |
|-------|--------|
| **المصدر** | `b2b-database-batch10-close-right.csv` (18 شركة ICP) |
| **النتيجة** | **18/18 ✅** · 0 فشل · PDF rate sheet · تأخير 45ث |
| **الأسواق** | UAE 5 · OM 2 · QA 1 · BH 1 · SG 1 · ID 1 · IN 4 · TR 3 |
| **سجل** | `outreach-sent-log-batch10-ar.md` · بحث: `b2b-database-batch10-research-log-ar.md` |
| **exclude** | ✅ 18 عنواناً أُضيفت (حتى #206) |

---

## Batch 8 (48 — مكتمل بالكامل، مُصحَّح بعد تدقيق فعلي للبريد)

> **الحالة:** ✅ **الموجة 1: 15/15 مُرسَل** (14 وصل + 1 ارتد) — 2026-07-09 21:32–22:45 Almaty (متصفح، يدوي)
> ✅ **الموجة 2: 33/33 مُرسَل** (24 وصل مؤكَّد + 7 ارتد + 2 متأخر/قيد إعادة المحاولة) — 2026-07-10 02:10–02:35 Almaty (SMTP، من جهاز المستخدم — ليس بيئة sandbox الخاصة بي)
> ⚠️ **تصحيح 2026-07-11:** السجل الأصلي للموجة 2 كان يدّعي "0 فشل" — هذا كان غير دقيق. راجعتُ صندوق الوارد الفعلي بناءً على طلب المستخدم ووجدت 7 ارتدادات نهائية + 2 تأخير لم تكن موثّقة. تفاصيل كاملة في outreach-sent-log-batch8-ar.md.

| البند | القيمة |
|-------|--------|
| **المصدر** | b2b-database-batch8-new.csv |
| **Tier A / B / C** | 31 / 13 / 4 |
| **طريقة الموجة 1** | Zoho Webmail عبر المتصفح يدوياً (بيئة sandbox الخاصة بي معزولة عن الشبكة الخارجية بالكامل) |
| **طريقة الموجة 2** | send_batch8_outreach.py عبر Zoho SMTP — نُفِّذ من جهاز المستخدم، حيث الإنترنت متاح فعلياً |
| **الموجة 1 (فيتنام 10 + UK 5)** | 15/15 قُبلت — 14 وصلت، 1 ارتدت (HaloBay، info@halobay.vn) |
| **الموجة 2 (#16–#48)** | 33/33 قُبلت — **24 وصلت مؤكَّد، 7 ارتدت، 2 متأخرة (تُعاد المحاولة حتى 2026-07-14)** |
| **إجمالي الحملة** | 48 قُبلت، **38 وصلت مؤكَّد**، **8 ارتدت نهائياً**، **2 معلّقة** |
| **قائمة الاستبعاد** | ✅ جميع الـ48 عنواناً في exclude_emails.txt (لا إعادة إرسال) |
| **السجل التفصيلي** | deliverables/outreach-sent-log-batch8-ar.md (يحتوي جدول الارتدادات السبعة بالتفصيل) |
| **الملف الآلي** | .tmp_batch8_sent.json (48 سجلاً، محدَّث بحالات sent/sent_bounced/sent_delayed) |
| **مراجعة قبل الإرسال (الموجة 1)** | ✅ كل رسالة من الـ15 رُوجعت بصرياً (نص + مرفق) قبل الإرسال |

**الارتدادات الثمانية (نهائية):** HaloBay Travel (W1)، Very Good Tour Korea، Jordan Tours & Travel، Petra Travel & Tourism (Jordan)، EGL Tours، Hayatun Tour، Nam Ho Travel، Mondial Voyages Maroc (W2).

**المتأخرة (لم تُحسم بعد):** Asia Exotic Expeditions (tours@asiaexotic.com)، Lef El Donia Travel (info@lefeldonia.com) — قيد إعادة المحاولة من Zoho حتى ~2026-07-14.

**Script:** `scripts/send_batch8_outreach.py` + `scripts/batch8_targets.py`

## Batch 7 FOLLOW-UP (net rates inline) — محاولة تشغيل 2026-07-09

> **الحالة: ⏸️ لم يُرسَل أي بريد — تم الإيقاف قبل الإرسال (بيئة التشغيل غير متوفرة)**

| البند | القيمة |
|-------|--------|
| الوقت | 2026-07-09 (تشغيل مجدوَل تلقائي) |
| `--dry-run` | ✅ نُفِّذ بنجاح — لا أخطاء |
| المستهدفون المعلَّقون | **42 / 45** (3 تم تخطيهم تلقائياً: #14 Holidaymakers، #40 Ajwa Travel، #42 Dynasty Travel — في قائمة الردود/bounce) |
| SMTP / الإرسال الفعلي | **لم يُنفَّذ** |
| السبب | التعليمات تطلب التشغيل عبر Desktop Commander (PowerShell على جهاز Windows) وليس بيئة Linux sandbox — أداة Desktop Commander لم تكن متصلة خلال هذا التشغيل غير التفاعلي (scheduled task)، ولا يوجد مستخدم حاضر للموافقة على مسار بديل |
| الإجراء المتخذ | لم يتم إرسال أي بريد فعلي ولم يتم لمس `.tmp_batch7_followup_sent.json` أو `.tmp_batch7_followup_remaining.json` — الحالة كما كانت |
| التالي | إعادة تشغيل المهمة عندما يكون Desktop Commander متصلاً، أو تشغيل الأوامر الثلاثة يدوياً من PowerShell:<br>`python scripts/send_batch7_followup.py --dry-run`<br>`python scripts/send_batch7_followup.py --only 1 --delay 0`<br>`python scripts/send_batch7_followup.py --delay 3` |
