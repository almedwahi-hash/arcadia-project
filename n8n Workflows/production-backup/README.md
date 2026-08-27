# Production Workflow Export — مطلوب قبل تعديل Laila

**الحالة:** ⚠️ **لم يُرفع export الإنتاج بعد**

## المطلوب من المالك / n8n

1. افتح n8n → Workflows
2. لكل workflow Active يحتوي "Arcadia" أو "Laila":
   - Export JSON
3. احفظ هنا:

```
n8n Workflows/production-backup/
  Arcadia - Laila Telegram V5.2026-08-27.json   ← إلزامي قبل أي تعديل
  Arcadia - Follow-up Cron (3h-24h).json
  Arcadia - Admin Commands.json
  (أي workflow Arcadia آخر Active)
```

4. انسخ النسخة الحالية إلى:
```
n8n Workflows/Arcadia - Laila Telegram V5.json
```

## بعد الرفع

- [ ] تأكيد مسار Pricing Engine (RPC vs webhook)
- [ ] تطبيق `deliverables/arcadia-phase1-laila-integration-ar.md`
- [ ] تعيين Error Workflow → `Arcadia - Central Error Handler.json`

---

*لا تعدّل production Laila حتى يوجد ملف backup في هذا المجلد.*
