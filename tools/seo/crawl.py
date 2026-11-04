import json, re, sys, os, time, hashlib
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse, urldefrag
import requests
from bs4 import BeautifulSoup

BASE = "https://arcadia-tour.com"
UA = "Mozilla/5.0 (compatible; ArcadiaAuditBot/1.0; +https://arcadia-tour.com/)"
S = requests.Session(); S.headers["User-Agent"] = UA
os.makedirs("pages", exist_ok=True)
urls = [l.strip() for l in open("all_urls.txt") if l.strip()]

def fetch(u):
    t0 = time.time()
    try:
        r = S.get(u, timeout=40, allow_redirects=True)
    except Exception as e:
        return {"url": u, "error": str(e)}
    d = {"url": u, "status": r.status_code, "final": r.url, "redirects": [h.status_code for h in r.history],
         "ttfb": round(r.elapsed.total_seconds(), 2), "size": len(r.content), "ctype": r.headers.get("content-type",""),
         "cf": r.headers.get("cf-cache-status",""), "xrobots": r.headers.get("x-robots-tag","")}
    if "html" not in d["ctype"]: return d
    html = r.text
    fn = "pages/" + hashlib.md5(u.encode()).hexdigest() + ".html"
    open(fn, "w", encoding="utf-8").write(html); d["file"] = fn
    soup = BeautifulSoup(html, "lxml")
    t = soup.find("title"); d["title"] = t.get_text(strip=True) if t else ""
    m = soup.find("meta", attrs={"name": "description"}); d["meta_desc"] = m.get("content","").strip() if m else ""
    m = soup.find("meta", attrs={"name": "robots"}); d["robots"] = m.get("content","") if m else ""
    c = soup.find("link", rel="canonical"); d["canonical"] = c.get("href","") if c else ""
    d["hreflang"] = {l.get("hreflang"): l.get("href") for l in soup.find_all("link", rel="alternate") if l.get("hreflang")}
    d["lang"] = (soup.html.get("lang") if soup.html else "") or ""
    d["h1"] = [h.get_text(" ", strip=True)[:120] for h in soup.find_all("h1")]
    d["h2_count"] = len(soup.find_all("h2"))
    og = soup.find("meta", property="og:image"); d["og_image"] = og.get("content","") if og else ""
    imgs = soup.find_all("img"); d["img_total"] = len(imgs)
    d["img_noalt"] = sum(1 for i in imgs if not (i.get("alt") or "").strip())
    d["img_lazy"] = sum(1 for i in imgs if i.get("loading") == "lazy")
    d["img_webp"] = sum(1 for i in imgs if ".webp" in (i.get("src") or "").lower())
    schemas = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            j = json.loads(s.string or "")
            items = j.get("@graph", [j]) if isinstance(j, dict) else j
            for it in items:
                if isinstance(it, dict): schemas.append(it.get("@type"))
        except Exception: schemas.append("INVALID_JSON")
    d["schema"] = schemas
    body_text = soup.get_text(" ", strip=True)
    d["words"] = len(re.findall(r"\w+", body_text))
    d["old_wa"] = ("77064007561" in html)
    d["new_wa"] = ("77051181845" in html)
    d["scripts"] = len(soup.find_all("script", src=True)); d["css"] = len(soup.find_all("link", rel="stylesheet"))
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#", "whatsapp:", "sms:")): continue
        full, _ = urldefrag(urljoin(r.url, href))
        links.add(full)
    d["links"] = sorted(links)
    d["internal_links"] = sum(1 for l in links if urlparse(l).netloc.endswith("arcadia-tour.com"))
    d["external_links"] = len(links) - d["internal_links"]
    return d

out = []
with ThreadPoolExecutor(max_workers=6) as ex:
    for i, d in enumerate(ex.map(fetch, urls), 1):
        out.append(d)
        if i % 50 == 0: print(i, "done", flush=True)
json.dump(out, open("crawl.json", "w"), ensure_ascii=False, indent=1)
print("TOTAL", len(out))
