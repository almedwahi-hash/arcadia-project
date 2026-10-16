"""Fix redirecting internal links inside post content AND Elementor widget data.

Unlike fix_redirect_links.py (plain string replace), this parses _elementor_data as JSON and
compares every href/url after decoding, so it matches links however they are stored
(raw Arabic, percent-encoded, \\uXXXX-escaped, absolute or root-relative).

Usage (from the repo root):
    python tools/seo/fix_links_structured.py deliverables/pending-redirect-links-2026-10-02.json           # show counts only
    python tools/seo/fix_links_structured.py deliverables/pending-redirect-links-2026-10-02.json --apply   # write
    python tools/seo/fix_links_structured.py <plan.json> --apply --only 155                               # one page

Plan format: [{"type": "pages", "id": 155, "links": [{"old": "/decoded/old/path", "new": "/decoded/new/path/"}]}]
Reading the editable content needs auth even without --apply (~/.netrc or ~/_netrc).
After applying to Elementor pages: Elementor -> Tools -> Regenerate, then purge caches.
"""
import json, os, re, sys, time
from urllib.parse import unquote, urlsplit

HOSTS = ("arcadia-tour.com", "www.arcadia-tour.com")
HREF = re.compile(r'''(href\s*=\s*)(["'])(.*?)\2''', re.S)


def norm(h):
    """Decoded path of an internal link, or None for external/other links."""
    h = h.strip()
    u = urlsplit(h)
    if u.scheme and u.scheme not in ("http", "https"): return None
    if u.netloc and u.netloc.lower() not in HOSTS: return None
    if not u.netloc and not h.startswith("/"): return None
    if u.query or u.fragment: return None
    return unquote(u.path)


def fix_html(s, mapping, counter):
    def rep(m):
        new = mapping.get(norm(m.group(3)))
        if new is None: return m.group(0)
        counter[0] += 1
        return m.group(1) + m.group(2) + new + m.group(2)
    return HREF.sub(rep, s)


def walk(node, mapping, counter):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "url" and isinstance(v, str) and mapping.get(norm(v)) is not None:
                node[k] = mapping[norm(v)]; counter[0] += 1
            elif isinstance(v, str):
                if "href" in v: node[k] = fix_html(v, mapping, counter)
            else:
                walk(v, mapping, counter)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, str):
                if "href" in v: node[i] = fix_html(v, mapping, counter)
            else:
                walk(v, mapping, counter)


def fix_elementor(el, mapping):
    """el is the _elementor_data string; returns (new_string, replacements)."""
    data = json.loads(el); counter = [0]
    walk(data, mapping, counter)
    return (json.dumps(data) if counter[0] else el), counter[0]


def main():
    import requests
    args = sys.argv[1:]
    plan = json.load(open(args[0], encoding="utf-8"))
    apply = "--apply" in args
    only = int(args[args.index("--only") + 1]) if "--only" in args else None
    BK = "deliverables/backups/" + os.path.splitext(os.path.basename(args[0]))[0]
    S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0 (compatible; ArcadiaAuditBot/1.0)"
    for it in plan:
        if only and it["id"] != only: continue
        mapping = {l["old"]: l["new"] for l in it["links"]}
        url = f"https://arcadia-tour.com/wp-json/wp/v2/{it['type']}/{it['id']}"
        r = S.get(url, params={"context": "edit", "_fields": "id,content,meta"}, timeout=90)
        if r.status_code != 200:
            print("SKIP", it["id"], "cannot read:", r.status_code, r.text[:120]); continue
        d = r.json(); raw = d["content"]["raw"]; el = (d.get("meta") or {}).get("_elementor_data") or ""
        c = [0]; new_raw = fix_html(raw, mapping, c)
        new_el, n_el = fix_elementor(el, mapping) if el else ("", 0)
        print(it["type"], it["id"], f"planned {len(mapping)} | content {c[0]} | elementor {n_el}", "" if apply else "(dry run)")
        if not apply or not (c[0] or n_el): continue
        os.makedirs(BK, exist_ok=True)
        bk = f"{BK}/{it['type']}-{it['id']}.json"
        if not os.path.exists(bk):
            json.dump({"content": raw, "_elementor_data": el}, open(bk, "w", encoding="utf-8"), ensure_ascii=False)
        payload = {"content": new_raw}
        if n_el: payload["meta"] = {"_elementor_data": new_el}
        r = S.post(url, json=payload, timeout=120)
        if r.status_code != 200:
            print("  FAIL", r.status_code, r.text[:200]); continue
        saved = (r.json().get("meta") or {}).get("_elementor_data") or ""
        left = fix_elementor(saved, mapping)[1] if saved else 0
        print("  saved; old links still in elementor data:", left)
        time.sleep(1)


if __name__ == "__main__":
    main()
