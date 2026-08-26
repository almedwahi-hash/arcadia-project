# كيف نوصل Cloud Agent بالبريد (Zoho) — دليل لـ Cloud

> **لمن؟** الشخص الذي يملك دخول Zoho + Cursor (Cloud)  
> **لماذا؟** حتى يقدر Cloud Agent يرسل outreach B2B تلقائياً بدون متصفح يدوي  
> **التاريخ:** 26 أغسطس 2026

---

## الفكرة باختصار

Cloud Agent = موظف على سيرفر Cursor.  
**لا يرى متصفحك الشخصي.** يحتاج مفتاح إرسال بريد (App Password) محفوظ كـ **Secret** في بيئة الـ Agent.

بعد إضافة السرّ، الأمر:
```bash
python3 scripts/send_batch12_outreach.py
```
يرسل من `info@arcadia-tour.com` مباشرة عبر SMTP.

---

## الطريقة الصحيحة (موصى بها) — 5 دقائق

### أ) في Zoho — إنشاء App Password

1. افتح: https://mail.zoho.eu  
2. سجّل دخول كـ **`info@arcadia-tour.com`** (مهم: نفس صندوق الإرسال)  
3. اذهب إلى: **Settings → Security → Application-specific passwords**  
   (أو من الحساب: https://accounts.zoho.eu → Security → App Passwords)  
4. أنشئ كلمة مرور جديدة باسم: `Cursor Cloud Agent`  
5. **انسخ الكلمة فوراً** (تظهر مرة واحدة فقط)

> ⚠️ لا تستخدم كلمة مرور تسجيل الدخول العادية.  
> ⚠️ يجب إنشاؤها وأنت داخل حساب `info@` وليس حساب شخصي آخر.

### ب) في Cursor — حفظ الـ Secret

1. افتح بيئة الـ Agent:  
   https://cursor.com/dashboard/cloud-agents/environments/e/ed4e05fc-a0bd-11f1-b532-320a589b8025  
2. أو من Agent → **Environment / Secrets**  
3. أضف Secret باسم أحد هذين (يكفي واحد):

| الاسم | القيمة |
|--------|--------|
| `ZOHO_SMTP_PASS` | (App Password من Zoho) |

اختياري للتأكيد:
| الاسم | القيمة |
|--------|--------|
| `SMTP_HOST` | `smtp.zoho.eu` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | `info@arcadia-tour.com` |

4. اضغط **Save**  
5. أعد تشغيل Cloud Agent (أو أرسل رسالة جديدة: «كمل الإرسال»)

### ج) تحقق سريع (Cloud Agent يعملها)

```bash
python3 scripts/send_batch12_outreach.py --dry-run   # معاينة 8 رسائل
python3 scripts/send_batch12_outreach.py             # إرسال فعلي
```

**From:** info@arcadia-tour.com  
**SMTP:** smtp.zoho.eu:465  
**PDF مرفق:** deliverables/pdfs/Arcadia-B2B-Rate-Sheet-Almaty.pdf  
**Batch جاهز:** deliverables/b2b-database-batch12-gcc-new.csv (8 شركات GCC)

---

## لماذا فشلنا سابقاً؟

| المحاولة | النتيجة |
|----------|---------|
| Secret `ZOHO_SMTP_PASS` | المستخدم تخطّاه → لا إرسال SMTP |
| دخول من متصفح الجهاز الشخصي | Cloud Agent لا يراه |
| دخول في متصفح Cloud (side panel) | يعمل فقط إذا اكتمل Sign in داخل تلك النافذة |

**الخلاصة:** أفضل وأثبت = App Password في Secrets. لا يعتمد على نافذة متصفح.

---

## رسالة جاهزة تنسخها لـ Cloud

```
مرحباً Cloud —

نحتاج توصيل Cloud Agent ببريد أركاديا للإرسال التلقائي (Batch 12 GCC — 8 شركات جاهزة).

المطلوب منك (مرة واحدة):
1) ادخل mail.zoho.eu كـ info@arcadia-tour.com
2) Settings → Security → Application-specific passwords
3) أنشئ App Password باسم: Cursor Cloud Agent
4) في Cursor Environment Secrets أضف:
   ZOHO_SMTP_PASS = (الكلمة التي نسختها)
   اختياري: SMTP_HOST=smtp.zoho.eu ، SMTP_PORT=465 ، SMTP_USER=info@arcadia-tour.com
5) احفظ ثم أخبر الـ Agent: «كمل إرسال Batch 12»

السكربت الجاهز: scripts/send_batch12_outreach.py
البيئة: https://cursor.com/dashboard/cloud-agents/environments/e/ed4e05fc-a0bd-11f1-b532-320a589b8025

لا ترسل يدوياً — بعد الـ Secret الـ Agent يرسل الكل.
```

---

## بعد التوصيل — ماذا يفعل الـ Agent؟

1. يقرأ الأهداف من `b2b-database-batch12-gcc-new.csv`  
2. يرسل 8 رسائل (تأخير ~45 ثانية بين كل رسالة)  
3. يرفق Rate Sheet PDF  
4. يحدّث سجل الإرسال + `exclude_emails.txt`  
5. يتابع batches جديدة (GCC / Asia) بنفس الطريقة

---

*مرجع تقني إضافي: `deliverables/zoho-smtp-fix-handoff-for-cloud-ar.md` · `deliverables/email-send-stable-path-ar.md`*
