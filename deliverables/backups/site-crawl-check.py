# Visitor-side crawl of every sitemap URL: status, titles, descriptions, H1, alt, og:image, schema,
# hreflang pairing, internal links, WhatsApp numbers. Run with:
#   PYTHONIOENCODING=utf-8 python site-crawl-check.py
import re, json, html, time, urllib.request, urllib.parse as p, concurrent.futures as cf, collections, sys
sys.stdout.reconfigure(encoding='utf-8')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'}
A = 'https://arcadia-tour.com/'


def get(u, t=60):
    t0 = time.time()
    r = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t)
    body = r.read().decode('utf-8', 'replace')
    return r.status, r.geturl(), r.headers.get('cf-cache-status'), body, time.time() - t0


rb = get(A + 'robots.txt')[3]
star = re.search(r'User-agent:\s*\*\s*\n((?:(?!User-agent:).*\n?)*)', rb, flags=re.I)
print('robots: sitemap line', bool(re.search(r'Sitemap:', rb)), '| "User-agent: *" blocks all', bool(star and re.search(r'^Disallow: /\s*$', star.group(1), re.M)))
idx = get(A + 'sitemap_index.xml')[3]
sms = re.findall(r'<loc>([^<]+)</loc>', idx)
urls = []
for sm in sms:
    urls += re.findall(r'<url>\s*<loc>([^<]+)</loc>', get(sm)[3])
urls = list(dict.fromkeys(html.unescape(u) for u in urls))
norm = lambda u: p.unquote(u).rstrip('/')
LEAK = re.compile('(?:target|rel|style|aria-label|href|class)=(?:”|″|")')
KB = re.compile('(?:الكويت|البحرين|Kuwait|Bahrain)[^.؟!?]{0,80}(?:التأشيرة الإلكترونية|e-visa)|(?:التأشيرة الإلكترونية|e-visa)[^.؟!?]{0,80}(?:الكويت|البحرين|Kuwait|Bahrain)')
CARDS = re.compile('(بطاقات الائتمان|البطاقات الائتمانية|[Cc]redit cards)[^.؟!?]{0,60}(مقبولة|تُقبل|accepted)')
UKW = ['ukrain', 'أوكراني', 'kyiv', 'kiev', 'odes', 'real-estate', 'للبيع', 'for-sale', 'lviv', 'الكربات', 'carpath', 'yaremche', 'cottage', 'land-', 'الغرب', 'kharkiv', 'خاركوف', 'جيتومير', 'zhytomyr', 'كامنيتز', 'نيكلايف', 'فيلكفا', 'walnut', 'oil', 'chips', 'kadorr', 'أوديسا', 'كييف', 'old-post']
uk = lambda u: any(k in p.unquote(u).lower() for k in UKW)
S = lambda u: p.unquote(u)[24:72]


def one(u):
    try:
        st, fin, cs, h, dt = get(u)
    except Exception as e:
        return {'url': u, 'err': str(e)[:60]}
    m = re.search(r'<main.*?</main>', h, flags=re.S)
    b = m.group(0) if m else h
    txt = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S))))
    t = re.search(r'<title>(.*?)</title>', h, flags=re.S)
    d = re.search(r'name="description" content="([^"]*)"', h)
    title = html.unescape(t.group(1)).strip() if t else ''
    links = dict((l, hf) for hf, l in re.findall(r'<link rel="alternate" href="([^"]+)" hreflang="([^"]+)"', h))
    wa = collections.Counter(re.findall(r'wa\.me/(\d{9,15})', h))
    return {
        'url': u, 'st': st, 'redir': norm(fin) != norm(u), 'cs': cs, 'dt': dt, 'h1': len(re.findall(r'<h1\b', h)),
        'title': title, 'desc': html.unescape(d.group(1)) if d else '',
        'noindex': bool(re.search(r'name="robots" content="[^"]*noindex', h)),
        'canon': (re.search(r'rel="canonical" href="([^"]+)"', h) or [None, ''])[1],
        'noalt': len([x for x in re.findall(r'<img\b[^>]*>', b) if not re.search(r'alt="[^"]+"', x)]),
        'hl': links, 'leak': len(LEAK.findall(txt)), 'og': bool(re.search(r'property="og:image"', h)),
        'schema': len(re.findall(r'application/ld\+json', h)), 'faq': len(re.findall(r'"@type":\s*"FAQPage"', h)),
        'php': bool(re.search(r'Parse error|Fatal error|<b>Warning</b>|<b>Notice</b>', h)), 'size': len(h),
        'int': sorted({norm(html.unescape(x)) for x in re.findall(r'<a\b[^>]*?href="(https://arcadia-tour\.com[^"#?]*)', b)}),
        'kb': bool(KB.search(txt)) and bool(re.search('روسيا|Russia', txt)) and not re.search('Ukrain|أوكراني', txt[:4000]),
        'cards': bool(CARDS.search(txt)) and bool(re.search('روسيا|موسكو|Russia|Moscow', title)),
        'wa': dict(wa),
    }


with cf.ThreadPoolExecutor(6) as ex:
    res = list(ex.map(one, urls))
json.dump(res, open('crawl.json', 'w', encoding='utf-8'), ensure_ascii=False)
ok = [r for r in res if 'err' not in r]
print('sitemaps', len(sms), 'urls', len(urls), '| ar', sum('/en/' not in u for u in urls), 'en', sum('/en/' in u for u in urls), '| errors', [r for r in res if 'err' in r][:3])
print('status', dict(collections.Counter(r['st'] for r in ok)), 'cache', dict(collections.Counter(r['cs'] for r in ok)), 'redirected', [S(r['url']) for r in ok if r['redir']], 'php errors', sum(r['php'] for r in ok))
dts = sorted(r['dt'] for r in ok)
print('response time: median %.2fs, 90%% %.2fs, max %.2fs' % (dts[len(dts) // 2], dts[int(len(dts) * 0.9)], dts[-1]))
live = [r for r in ok if not r['redir']]
print('h1!=1', [(r['h1'], S(r['url'])) for r in live if r['h1'] != 1][:5], '| no title', sum(not r['title'] for r in live), 'no desc', sum(not r['desc'] for r in live), 'noindex', sum(r['noindex'] for r in live), 'canon mismatch', [S(r['url']) for r in live if norm(r['canon']) != norm(r['url'])][:5])
tc = collections.Counter(r['title'] for r in live)
dc = collections.Counter(r['desc'] for r in live)
print('dup titles', [(t[:40], c) for t, c in tc.items() if c > 1][:4], 'dup descs', [(t[:40], c) for t, c in dc.items() if c > 1][:4])
print('title>65 non-uk', [(len(r['title']), S(r['url'])) for r in live if len(r['title']) > 65 and not uk(r['url'])], '| desc>160 non-uk', [(len(r['desc']), S(r['url'])) for r in live if len(r['desc']) > 160 and not uk(r['url'])])
print('noalt non-uk', sum(r['noalt'] for r in live if not uk(r['url'])), '| leaks', [S(r['url']) for r in live if r['leak']], '| no og:image (non-uk, non-archive)', [S(r['url']) for r in live if not r['og'] and not uk(r['url']) and '/category/' not in r['url']], '| no schema', sum(not r['schema'] for r in live), '| pages with FAQ schema', sum(1 for r in live if r['faq']), '| duplicate FAQ schema', [S(r['url']) for r in live if r['faq'] > 1])
print('kuwait/bahrain e-visa (Russia)', [S(r['url']) for r in live if r['kb'] and 'uzbek' not in r['url']], '| cards accepted (Russia pages)', [S(r['url']) for r in live if r['cards']])
byu = {norm(r['url']): r for r in ok}
bad = []
paired = 0
for r in live:
    hl = r['hl']
    if not hl:
        continue
    paired += 1
    other = hl.get('en') if '/en/' not in r['url'] else hl.get('ar')
    if not other:
        bad.append((S(r['url']), 'no other'))
        continue
    if norm(other) not in byu:
        continue
    o = byu[norm(other)]['hl']
    back = o.get('ar') if '/en/' not in r['url'] else o.get('en')
    if norm(back or '') != norm(r['url']):
        bad.append((S(r['url']), 'no return'))
print('hreflang paired', paired, 'unpaired', len(live) - paired, 'problems', bad)
allint = set(l for r in ok for l in r['int'])
unk = [l for l in allint if l not in byu and '/wp-content/' not in l and '/category/' not in l and '/tag/' not in l]


def chk(l):
    try:
        r = urllib.request.urlopen(urllib.request.Request(p.quote(l, safe=':/%') + '/', headers=UA), timeout=40)
        return l, r.status, norm(r.geturl()) != l
    except Exception as e:
        return l, str(e)[:30], False


with cf.ThreadPoolExecutor(6) as ex:
    cr = list(ex.map(chk, unk))
print('internal targets outside sitemap', len(unk), 'broken', [(c[1], c[0][24:70]) for c in cr if c[1] != 200], 'redirecting', [c[0][24:70] for c in cr if c[1] == 200 and c[2]])
allnums = collections.Counter()
pages_with = collections.Counter()
for r in ok:
    for n, c in r['wa'].items():
        allnums[n] += c
        pages_with[n] += 1
print('WhatsApp numbers (occurrences, pages):', {n: (c, pages_with[n]) for n, c in allnums.items()})
print('pages with other numbers:', [(S(r['url']), r['wa']) for r in ok if any(n != '77064007561' for n in r['wa']) and not uk(r['url'])][:12])
nowa = [S(r['url']) for r in ok if not r['wa'] and not uk(r['url']) and '/category/' not in r['url']]
print('non-Ukraine pages without a WhatsApp link:', len(nowa), nowa[:30])
