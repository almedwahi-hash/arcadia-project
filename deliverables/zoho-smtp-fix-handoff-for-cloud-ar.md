# Zoho SMTP Fix — Handoff for Cloud Agent

## EN — Cloud Agent Prompt (read first)

**Goal:** Fix Zoho SMTP relay so B2B bulk outreach works again via Python scripts (not browser).

**Error:** `553 Sender is not allowed to relay emails on smtppro.zoho.eu:465`

**Resolution (2026-07-05):** Root cause was **code-side**, not Zoho admin. (1) `send_batch6_outreach.py` forced `smtp.zoho.eu` → `smtppro.zoho.eu` — removed; use `SMTP_HOST=smtp.zoho.eu`. (2) Em dash in From display name caused RFC2047 encoding of entire From header — fixed with `formataddr` + `Header` on name only. Batch 6: **18/18 sent**. Same fixes applied to `send_batch5_outreach.py`. No Zoho account changes required.

**Symptoms:** SMTP LOGIN succeeds; self-send to `info@arcadia-tour.com` OK; external B2B sends fail with 553.

**What worked:** Batch 4 sent 16/16 via `scripts/send_batch4_outreach.py` on 25 Jun 2026 — relay broke later (or App Password is from wrong Zoho account).

**Your job:**
1. Human/Zoho-side: log in as `info@arcadia-tour.com` at mail.zoho.eu → enable SMTP outbound → create NEW App Password while logged in as info@ → org admin relay if needed.
2. Update `.env` at repo root: `SMTP_HOST`, `SMTP_PORT=465`, `SMTP_USER=info@arcadia-tour.com`, `SMTP_PASS=<new app password>`. Try `smtppro.zoho.eu` then `smtp.zoho.eu`.
3. Verify from project root:
   - `python scripts/send_batch6_outreach.py --only 1 --delay 0`
   - `python scripts/send_batch5_outreach.py --dry-run`
4. After fix: run full batch6 (18 pending in `.tmp_batch6_remaining.json`).

**Do NOT:** browser bulk automation (`send_batch5_zoho_browser.py`, Playwright); App Password from accounts.zoho.eu personal/admin — must be from mail.zoho.eu as info@.

**Read:** `deliverables/email-send-stable-path-ar.md`, `deliverables/outreach-master-status-ar.md`, `scripts/send_batch4_outreach.py`, `scripts/send_batch6_outreach.py`.

---

# إصلاح Zoho SMTP — تسليم لـ Cloud Agent | أركاديا

> **للمالك:** هذا المستند يشرح المشكلة وخطوات الإصلاح بالعربية. Cloud Agent يقرأ القسم الإنجليزي أعلاه ثم ينفّذ الخطوات هنا معك أو نيابةً عنك.

**التاريخ:** 4 يوليو 2026 — **مُحدَّث 5 يوليو 2026**  
**الحالة:** ✅ **مُحلّ — 18/18 دفعة 6** (السبب: كود، ليس Zoho admin)  
**المرجع السريع:** `deliverables/outreach-master-status-ar.md`

---

## ✅ الحل (5 يوليو 2026)

| السبب | الإصلاح |
|-------|---------|
| السكربت يفرض `smtppro.zoho.eu` بدل `smtp.zoho.eu` | حذف إعادة الكتابة؛ `.env`: `SMTP_HOST=smtp.zoho.eu` |
| الشرطة الطويلة (—) في From تُرمّز الرأس كاملاً بـ RFC2047 | `formataddr` + `Header` — ترميز الاسم فقط |
| `--only` يمسح `.tmp_batch6_remaining.json` | `all_emails` قبل الفلترة في `save_remaining` |

**لم يلزم:** App Password جديد، تفعيل SMTP في Zoho Admin، أو relay org.

---

## 1. الخطأ

```
553 Sender is not allowed to relay emails on smtppro.zoho.eu:465
```

**المعنى ببساطة:** خادم Zoho قبل تسجيل الدخول (LOGIN) لكن **رفض إرسال بريد إلى عناوين خارجية** — يعتبر أن الحساب لا يملك صلاحية «relay» للخارج.

---

## 2. الأعراض (ما يحدث فعلياً)

| الخطوة | النتيجة |
|--------|---------|
| اتصال SMTP + LOGIN | ✅ **ناجح** |
| إرسال إلى `info@arcadia-tour.com` (نفس الحساب) | ✅ **ناجح** |
| إرسال إلى عناوين B2B خارجية (مثل `info@siyanatours.com`) | ❌ **فشل 553** |

**آخر تجربة (4 يوليو 2026):** رسالة تجريبية #1 (Siyana Travel) فشلت بـ 553 — تم **إيقاف الإرسال الجماعي فوراً**. التفاصيل في `deliverables/outreach-sent-log-batch6-ar.md`.

---

## 3. ما كان يعمل سابقاً

| البند | التفاصيل |
|-------|----------|
| **الدفعة 4** | ✅ **16/16** مُرسَل عبر SMTP |
| **التاريخ** | 25 يونيو 2026 |
| **السكربت** | `scripts/send_batch4_outreach.py` |
| **السجل** | `deliverables/outreach-sent-log-batch4-ar.md` |
| **الخادم آنذاك** | `smtp.zoho.eu:465` (و/أو `smtppro.zoho.eu`) |

**الاستنتاج:** الإعداد كان صحيحاً ثم **انكسر relay** أو **App Password أصبح من حساب خاطئ** (حساب شخصي/admin بدل صندوق info@).

---

## 4. الأسباب الجذرية المحتملة (راجع الكل)

### 4.1 App Password من الحساب الخاطئ

- ❌ **خطأ شائع:** إنشاء كلمة مرور التطبيق من `accounts.zoho.eu` (حساب شخصي أو admin عام).
- ✅ **الصحيح:** تسجيل الدخول إلى **`mail.zoho.eu` كـ `info@arcadia-tour.com`** ثم: **Security → Application-specific passwords**.

كلمة مرور admin **لا تمنح** صلاحية relay لصندوق info@.

### 4.2 SMTP الصادر معطّل لصندوق البريد

في إعدادات صندوق `info@`:
- **Settings → Mail → IMAP/POP Access**
- يجب تفعيل **SMTP** (الإرسال عبر SMTP/IMAP).

بدون ذلك: LOGIN قد ينجح لكن relay الخارجي يُرفض.

### 4.3 عدم تطابق From / Envelope

السكربتات تستخدم:
- **From:** `info@arcadia-tour.com`
- **SMTP_USER:** يجب أن يكون **نفس العنوان** `info@arcadia-tour.com`

إذا كان `SMTP_USER` مختلفاً (مثل admin@ أو alias) → 553.

### 4.4 `smtp.zoho.eu` مقابل `smtppro.zoho.eu`

- **`info@arcadia-tour.com`** صندوق **منظمة (org mailbox)** على Zoho EU.
- غالباً يحتاج **`smtppro.zoho.eu:465`** وليس `smtp.zoho.eu` فقط.
- الدفعة 4 نجحت بـ SMTP؛ الدفعات اللاحقة فشلت — جرّب **كلا الخادمين** بعد إصلاح App Password وSMTP.

---

## 5. خطوات الإصلاح (Cloud Agent / المالك)

### المرحلة أ — في Zoho (إنسان أو Cloud مع وصول المتصفح)

1. **افتح** [https://mail.zoho.eu](https://mail.zoho.eu)
2. **سجّل الدخول كـ** `info@arcadia-tour.com` (ليس حساب admin الشخصي)
3. **Settings → Mail → IMAP/POP Access**
   - فعّل **IMAP** إن لزم
   - فعّل **SMTP** (الإرسال الصادر)
4. **إن كان الحساب ضمن منظمة Zoho Mail:**
   - افتح **Zoho Admin Console** (admin.zoho.eu)
   - **Mail → Mail Settings → SMTP Relay** (أو ما يعادله)
   - اسمح لـ `info@arcadia-tour.com` بالإرسال SMTP الخارجي
5. **أنشئ App Password جديد:**
   - وأنت مسجّل **كـ info@**
   - **Security → Application-specific passwords**
   - اسم مقترح: `Arcadia outreach SMTP`
   - **انسخ كلمة المرور فوراً** (لا تُعرض مرة ثانية)

### المرحلة ب — تحديث `.env` في المشروع

**المسار:** `C:\Users\Dell\Desktop\arcadia-project\.env`

```env
SMTP_HOST=smtp.zoho.eu
SMTP_PORT=465
SMTP_USER=info@arcadia-tour.com
SMTP_PASS=<كلمة مرور التطبيق الجديدة من info@>
```

**ملاحظات:**
- **الخادم الصحيح لهذا الحساب:** `smtp.zoho.eu:465` (وليس `smtppro.zoho.eu` — كان يسبب 553).
- **لا ترفع `.env` إلى Git** — الملف في `.gitignore`.
- السكربتات تقبل أيضاً: `ZOHO_SMTP_HOST`, `ZOHO_SMTP_PASS`, إلخ.

### المرحلة ج — اختبار من جذر المشروع

```powershell
cd C:\Users\Dell\Desktop\arcadia-project
```

**اختبار SMTP سريع (اختياري):**
```powershell
python scripts/test_smtp_fix.py
```

---

## 6. أوامر التحقق (انسخ والصق)

**من جذر المشروع** `C:\Users\Dell\Desktop\arcadia-project`:

```powershell
python scripts/send_batch6_outreach.py --only 1 --delay 0
```

**المتوقع بعد الإصلاح:** رسالة #1 إلى Siyana Travel (`info@siyanatours.com`) تُرسل **بدون 553** — تحقق من مجلد **Sent** في Zoho.

```powershell
python scripts/send_batch5_outreach.py --dry-run
```

**المتوقع:** معاينة فقط — لا إرسال — للتأكد أن السكربت يقرأ `.env` والقوائم بشكل صحيح.

---

## 7. بعد نجاح الإصلاح — تشغيل الدفعة 6

| البند | القيمة |
|-------|--------|
| **المتبقي** | **18** رسالة |
| **الملف** | `.tmp_batch6_remaining.json` |
| **سجل المُرسَل** | `.tmp_batch6_sent.json` (يُحدَّث تلقائياً) |
| **السكربت** | `scripts/send_batch6_outreach.py` |
| **السجل النصي** | `deliverables/outreach-sent-log-batch6-ar.md` |

**تسلسل آمن:**

```powershell
# 1) رسالة واحدة — تحقق Sent في Zoho
python scripts/send_batch6_outreach.py --only 1 --delay 0

# 2) إن نجحت — باقي الدفعة (تأخير 3–15 ثانية بين الرسائل)
python scripts/send_batch6_outreach.py
```

**حدّث بعد الانتهاء:** `deliverables/outreach-master-status-ar.md` و `deliverables/outreach-sent-log-batch6-ar.md`.

---

## 8. ممنوع

| ❌ لا تفعل | السبب |
|-----------|--------|
| `send_batch5_zoho_browser.py` | أتمتة متصفح — فشلت سابقاً (`no to input`, locks) |
| Playwright / Chrome CDP للـ bulk | غير مستقر — راجع `deliverables/email-send-stable-path-ar.md` |
| App Password من `accounts.zoho.eu` (حساب شخصي/admin) | لا يصلح relay لـ info@ |
| إرسال bulk متوازٍ أو أكثر من جلسة Python على Zoho | خطر حظر / سجلات متضاربة |
| `--force` على سكربتات الإرسال | يتجاهل سجل المُرسَل — تجنّبه |

**المسار الوحيد للإرسال الجماعي:** SMTP + `send_batch*_outreach.py`.

---

## 9. ملفات يجب قراءتها

| الملف | الغرض |
|-------|--------|
| `deliverables/email-send-stable-path-ar.md` | المسار المستقر — SMTP فقط للـ bulk |
| `deliverables/outreach-master-status-ar.md` | حالة جميع الدفعات |
| `scripts/send_batch4_outreach.py` | مرجع الإعداد الذي نجح (16/16) |
| `scripts/send_batch6_outreach.py` | السكربت الحالي للدفعة 6 (18 معلّقة) |
| `deliverables/outreach-sent-log-batch6-ar.md` | سجل فشل 553 الأخير |
| `scripts/test_smtp_fix.py` | اختبار LOGIN + self-send سريع |

---

## 10. ملخص للمالك

1. **المشكلة كانت في السكربت** — ليس relay Zoho ولا App Password خاطئ.
2. **الحل:** `smtp.zoho.eu` + ترميز From صحيح — **18/18 دفعة 6 نجحت** بدون تغيير حساب Zoho.
3. **batch5:** نفس الإصلاحات في `send_batch5_outreach.py` للإرسالات المستقبلية.
4. **لا browser automation** للإرسال الجماعي.

---

*Handoff v2 — 2026-07-05 — resolved code-side; Arcadia Tourism B2B outreach*
