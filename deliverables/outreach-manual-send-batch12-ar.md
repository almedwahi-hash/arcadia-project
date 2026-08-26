# إرسال Batch 12 يدوياً — Zoho Mail

> **السبب:** SMTP secret (`ZOHO_SMTP_PASS`) لم يُضف — المسار اليدوي عبر Zoho Web  
> **From:** info@arcadia-tour.com  
> **التاريخ:** 25 أغسطس 2026  
> **العدد:** 8 شركات GCC

---

## خطوات سريعة

1. افتح https://mail.zoho.eu → **info@arcadia-tour.com**
2. لكل شركة أدناه: **New Mail** → To → Subject → Body → **Attach** `deliverables/pdfs/Arcadia-B2B-Rate-Sheet-Almaty.pdf` → Send
3. تحقق من مجلد **Sent**
4. حدّث `deliverables/exclude_emails.txt` بإضافة البريد بعد الإرسال

---

## القائمة

| # | الشركة | To | Subject |
|---|--------|-----|---------|
| 1 | Rio Travels | info@riotravels.ae | B2B partnership — Kazakhstan group ground \| Arcadia × Rio Travels |
| 2 | Deira Travel | info@deiratravel.com | B2B partnership — Kazakhstan group ground \| Arcadia × Deira Travel |
| 3 | Target Travel Qatar | info@targettravelsqatar.com | B2B partnership — Kazakhstan group ground \| Arcadia × Target Travel Qatar |
| 4 | Majan Travel | wings@majantravel.com | B2B partnership — Kazakhstan group ground \| Arcadia × Majan Travel |
| 5 | Go Kite Travel Oman | info@om.gokite.travel | B2B partnership — Kazakhstan group ground \| Arcadia × Go Kite Travel Oman |
| 6 | Almurtahel Travel | info@almurtahel.sa | شراكة B2B — مجموعات كازاخستان \| أركاديا × Almurtahel Travel |
| 7 | Travel 196 Flags | bookings@travel196flags.com | B2B partnership — Kazakhstan group ground \| Arcadia × Travel 196 Flags |
| 8 | Farhat Tours | enquiry@farhattravel.com | B2B partnership — Kazakhstan group ground \| Arcadia × Farhat Tours & Travel |

**نصوص كاملة:** `.tmp_batch12_emails.json` (حقل `body` لكل شركة)

---

## بعد الإرسال

```bash
# أضف كل بريد إلى exclude (سطر واحد لكل بريد)
# ثم حدّث outreach-master-status-ar.md
```

**CTA في كل رسالة:** pax + dates → written quote ≤24h

---

*بديل لاحقاً: أضف `ZOHO_SMTP_PASS` في Environment secrets → `python3 scripts/send_batch12_outreach.py`*
