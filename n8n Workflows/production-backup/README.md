# Production Workflow Export — مطلوب قبل تعديل Laila

**الحالة:** ⚠️ **لم يُرفع export الإنتاج بعد** (Cloud Agent لا يملك وصول n8n مباشر)

## الطريقة أ — Export يدوي (n8n UI)

1. افتح n8n → Workflows
2. لكل workflow Active يحتوي "Arcadia" أو "Laila":
   - Export JSON
3. احفظ هنا:

```
n8n Workflows/production-backup/
  Arcadia - Laila Telegram V5.2026-08-27.json   ← إلزامي
  Arcadia - Follow-up Cron (3h-24h).2026-08-27.json
  Arcadia - Admin Commands.2026-08-27.json
  (أي workflow Pricing منفصل إن وُجد)
```

## الطريقة ب — n8n API (تلقائي — المفضّل)

أضف secrets في Cloud Environment:
- `N8N_API_URL` — مثل `https://YOUR-INSTANCE.app.n8n.cloud/api/v1`
- `N8N_API_KEY` — من n8n → Settings → API

```bash
# اكتشاف + export + import + tests (بدون activate production)
python3 scripts/n8n_phase1_operational.py run-all
```

## بعد الرفع — تسلسل Import في n8n

1. `Arcadia - Central Error Handler.json` (**بدون** errorWorkflow على نفسه)
2. `Arcadia - Phase1 Inbound Pipeline.json`
3. `Arcadia - Phase1 Outbound Log.json`
4. `Arcadia - Phase1 Pricing Action Log.json`
5. شغّل:
   ```bash
   python3 scripts/patch_laila_phase1.py
   ```
6. Import `Arcadia - Laila Telegram V5 Phase1 Working.json`
7. Wire Execute Workflow nodes → sub-workflows المستوردة
8. Error Handler على Follow-up + Admin:
   ```bash
   python3 scripts/patch_workflow_error_handler.py --all-backups
   ```
9. اختبار Error Handler: `Arcadia - Phase1 Error Handler Test.json` (مرة واحدة ثم disable)

## Pricing canonical entry point

**`quote_options`** — لا تستخدم `quote_package` مباشرة (overload ambiguity في Postgres).

---

*لا تعدّل production Laila حتى يوجد ملف backup في هذا المجلد.*
