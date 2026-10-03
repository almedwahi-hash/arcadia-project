import json,collections,re
d=json.load(open("crawl.json")); L=json.load(open("links.json"))
ok=[p for p in d if p.get("status")==200]
print("crawled:",len(d),"| 200:",len(ok),"| non-200:",[(p["url"][24:80],p.get("status"),p.get("error","")[:30]) for p in d if p.get("status")!=200])
idx=[p for p in ok if "noindex" not in (p.get("robots") or "")]
print("indexable:",len(idx),"| noindex:",len(ok)-len(idx))
def show(name,items,fmt=lambda p:p["url"][24:90]):
    print(f"\n## {name}: {len(items)}")
    for p in items[:25]: print("  ",fmt(p))
show("title missing",[p for p in idx if not p.get("title")])
show("title >60",[p for p in idx if len(p.get("title",""))>60],lambda p:f'{len(p["title"])} {p["url"][24:70]} | {p["title"][:60]}')
show("desc missing",[p for p in idx if not p.get("meta_desc")])
show("desc >165",[p for p in idx if len(p.get("meta_desc",""))>165],lambda p:f'{len(p["meta_desc"])} {p["url"][24:80]}')
show("h1 count !=1",[p for p in idx if len(p.get("h1",[]))!=1],lambda p:f'{len(p["h1"])} {p["url"][24:80]}')
show("canonical != url",[p for p in idx if p.get("canonical") and p["canonical"].rstrip("/")!=p["url"].rstrip("/")],lambda p:f'{p["url"][24:70]} -> {p["canonical"][24:70]}')
show("no hreflang pair",[p for p in idx if len(p.get("hreflang",{}))<2],lambda p:f'{p["url"][24:80]} {list(p.get("hreflang",{}).keys())}')
show("thin <300 words (non-ukraine)",[p for p in idx if (p.get("words") or 0)<300 and not re.search(r'ukrain|kyiv|odessa|kiev|%d8%a3%d9%88%d9%83%d8%b1%d8%a7%d9%86%d9%8a%d8%a7',p["url"],re.I)],lambda p:f'{p["words"]} {p["url"][24:90]}')
show("img without alt",[p for p in idx if p.get("img_noalt",0)>0],lambda p:f'{p["img_noalt"]}/{p["img_total"]} {p["url"][24:80]}')
show("old phone visible",[p for p in idx if p.get("new_wa")])
show("schema invalid",[p for p in idx if "INVALID_JSON" in p.get("schema",[])])
show("slow ttfb >2s",sorted([p for p in idx if p.get("ttfb",0)>2],key=lambda p:-p["ttfb"]),lambda p:f'{p["ttfb"]}s {p["url"][24:80]}')
titles=collections.Counter(p.get("title") for p in idx); show("duplicate titles",[{"url":t} for t,c in titles.items() if c>1],lambda p:p["url"][:90])
descs=collections.Counter(p.get("meta_desc") for p in idx); show("duplicate descriptions",[{"url":t} for t,c in descs.items() if c>1 and t],lambda p:p["url"][:120])
bad=[l for l in L if l.get("status") not in (200,) ]
internal=[l for l in bad if l.get("internal")]; external=[l for l in bad if not l.get("internal")]
print(f"\n## broken/odd links: internal {len(internal)}, external {len(external)}")
for l in sorted(internal,key=lambda x:-x["nsrc"])[:40]: print("  ",l["status"],l["nsrc"],"src |",l["url"][24:100],"| from:",l["sources"][0][24:80])
print("  -- external:")
for l in sorted(external,key=lambda x:-x["nsrc"])[:25]: print("  ",l["status"],l["nsrc"],"src |",l["url"][:90],"| from:",l["sources"][0][24:80])
red=[l for l in L if l.get("status")==200 and l.get("hops",0)>0 and l.get("internal")]
print(f"\n## internal links that redirect (fixable to direct): {len(red)}")
for l in sorted(red,key=lambda x:-x["nsrc"])[:30]: print("  ",l["nsrc"],"src |",l["url"][24:100],"->",l["final"][24:100])
