import json, collections, requests, time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
d = json.load(open("crawl.json"))
crawled = {x["url"].rstrip("/") for x in d}
src = collections.defaultdict(set)
for x in d:
    for l in x.get("links", []): src[l].add(x["url"])
targets = sorted(src)
print("unique links:", len(targets))
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0 (compatible; ArcadiaAuditBot/1.0)"
def chk(u):
    try:
        r = S.head(u, timeout=20, allow_redirects=True)
        if r.status_code in (403, 405, 404, 400, 501):
            r = S.get(u, timeout=25, allow_redirects=True, stream=True); r.close()
        return {"url": u, "status": r.status_code, "final": r.url, "hops": len(r.history), "internal": urlparse(u).netloc.endswith("arcadia-tour.com"), "sources": sorted(src[u])[:5], "nsrc": len(src[u])}
    except Exception as e:
        return {"url": u, "status": "ERR", "err": str(e)[:80], "internal": urlparse(u).netloc.endswith("arcadia-tour.com"), "sources": sorted(src[u])[:5], "nsrc": len(src[u])}
out = []
with ThreadPoolExecutor(max_workers=10) as ex:
    for i, r in enumerate(ex.map(chk, targets), 1):
        out.append(r)
        if i % 200 == 0: print(i, flush=True)
json.dump(out, open("links.json", "w"), ensure_ascii=False, indent=1)
print("DONE", len(out))
