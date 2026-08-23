# المسار المستقر لإرسال outreach | أركاديا

> **قاعدة:** إرسال جماعي = SMTP فقط. لا أتمتة متصفح للـ bulk.

## المسار الرئيسي (الوحيد للـ bulk)

**From:** info@arcadia-tour.com  
**SMTP:** smtp.zoho.eu:465 + App Password في `.env`  
**السكربت:** `scripts/send_batch5_outreach.py` (Batch 5 + GCC) — `scripts/send_batch6_outreach.py` (Batch 6)

| خطوة | أمر |
|------|-----|
| 1 | `--dry-run` |
| 2 | `--only <num>` رسالة واحدة → تحقق Sent |
| 3 | تشغيل كامل للمتبقي (يتخطى `.tmp_batch5_sent.json`) |

**بين الرسائل:** 3–15 ثانية (افتراضي `--delay 3`).

## بديل يدوي (fallback)

1. Zoho Mail → **Новое письмо**
2. To → Subject → Body من `.tmp_batch5_remaining.json`
3. **Отправить** → تحقق **Отправленные**
4. حدّث `.tmp_batch5_sent.json` + `outreach-sent-log-batch5-ar.md`

قائمة المتبقي: `deliverables/outreach-manual-send-batch5-ar.md`

## ممنوع للإرسال الجماعي

- `send_batch5_zoho_browser.py`
- Playwright / Chrome CDP / `--limit` متوازٍ
- أكثر من عملية Python على نفس جلسة Zoho

## لماذا؟

| الطريقة | المشكلة |
|---------|---------|
| SMTP (صحيح) | Batch 4: 16/16 ✅ |
| SMTP (553) | خادم/From خاطئ — يُصلَح بـ smtp.zoho.eu + formataddr للاسم |
| Browser | no compose، browser closed، locks، سجلات متضاربة |

---
*2026-06-26 — مسار واحد: SMTP + send_batch5_outreach.py*
