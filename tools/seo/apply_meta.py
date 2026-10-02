"""Apply Yoast title/description (and optionally featured image) updates from a JSON plan.

Usage (from the repo root):
    python tools/seo/apply_meta.py deliverables/pending-meta-updates-2026-10-02.json            # dry run
    python tools/seo/apply_meta.py deliverables/pending-meta-updates-2026-10-02.json --apply     # write
    python tools/seo/apply_meta.py <plan.json> --apply --only desc      # desc | title | image
    python tools/seo/apply_meta.py <plan.json> --apply --batch 2        # items 11-20

Plan format: [{"type": "posts"|"pages", "id": 123, "title": "...", "desc": "...", "featured_media": 456}, ...]
Auth comes from ~/.netrc (or ~/_netrc on Windows); requests reads it automatically.
"""
import json, os, sys, time
import requests

BASE = "https://arcadia-tour.com/wp-json/wp/v2"
KEYS = {"title": "_yoast_wpseo_title", "desc": "_yoast_wpseo_metadesc"}

args = sys.argv[1:]
plan_path = args[0]
apply = "--apply" in args
only = args[args.index("--only") + 1] if "--only" in args else None
batch = int(args[args.index("--batch") + 1]) if "--batch" in args else None

plan = json.load(open(plan_path, encoding="utf-8"))
if batch: plan = plan[(batch - 1) * 10: batch * 10]
BK = "deliverables/backups/" + os.path.splitext(os.path.basename(plan_path))[0]
if apply: os.makedirs(BK, exist_ok=True)
S =requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0 (compatible; ArcadiaAuditBot/1.0)"

for it in plan:
    url = f"{BASE}/{it['type']}/{it['id']}"
    payload = {}
    meta = {KEYS[k]: it[k] for k in KEYS if it.get(k) and only in (None, k)}
    if meta: payload["meta"] = meta
    if it.get("featured_media") and only in (None, "image"): payload["featured_media"] = it["featured_media"]
    if not payload: continue
    if not apply:
        print("DRY", it["type"], it["id"], json.dumps(payload, ensure_ascii=False)); continue
    r = S.get(url, params={"context": "edit", "_fields": "id,link,meta,featured_media"}, timeout=60)
    if r.status_code != 200:
        print("SKIP", it["id"], "cannot read for backup:", r.status_code, r.text[:120]); continue
    cur = r.json()
    bk = f"{BK}/{it['type']}-{it['id']}.json"
    if not os.path.exists(bk):
        old = {"id": cur["id"], "link": cur["link"], "featured_media": cur.get("featured_media"),
               "meta": {k: (cur.get("meta") or {}).get(k) for k in KEYS.values()}}
        json.dump(old, open(bk, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    r = S.post(url, json=payload, timeout=120)
    if r.status_code == 200:
        j = r.json(); got = j.get("meta") or {}
        ok = all(got.get(k) == v for k, v in meta.items()) and (
            "featured_media" not in payload or j.get("featured_media") == payload["featured_media"])
        print("OK " if ok else "NOT-SAVED", it["type"], it["id"], j.get("link"))
    else:
        print("FAIL", it["type"], it["id"], r.status_code, r.text[:200])
    time.sleep(1)
