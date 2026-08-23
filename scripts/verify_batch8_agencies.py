#!/usr/bin/env python3
"""Verify B2B agency emails on official websites for batch 8."""
import csv
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKLIST_PATH = ROOT / "deliverables" / "exclude_emails.txt"
EXISTING_CSVS = [
    ROOT / "deliverables" / "b2b-database-master-verified.csv",
    ROOT / "deliverables" / "b2b-database-batch8-verified.csv",
    ROOT / "deliverables" / "b2b-database-asia-verified.csv",
    ROOT / "deliverables" / "b2b-database-gcc-verified.csv",
]

USER_AGENT = "Mozilla/5.0 (compatible; ArcadiaB2BResearch/1.0)"


def load_blocklist():
    emails = set()
    if BLOCKLIST_PATH.exists():
        for line in BLOCKLIST_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # tab-separated index\temail
            parts = line.split("\t")
            email = parts[-1].strip().lower()
            if "@" in email:
                emails.add(email)
    for csv_path in EXISTING_CSVS:
        if not csv_path.exists():
            continue
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                e = (row.get("email") or "").strip().lower()
                if e:
                    emails.add(e)
    return emails


def fetch_url(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"__ERROR__:{e}"


def verify_email_on_page(email, html):
    if html.startswith("__ERROR__"):
        return False, html
    patterns = [
        email.lower(),
        email,
        f"mailto:{email.lower()}",
        f"mailto:{email}",
    ]
    low = html.lower()
    for p in patterns:
        if p.lower() in low:
            return True, "found"
    # Cloudflare email protection - check domain part
    local, domain = email.lower().split("@", 1)
    if domain in low and (local in low or "email-protection" in low):
        return True, "domain+local heuristic"
    return False, "not found"


# Candidates: outbound agencies only (not KZ/UZ DMC competitors)
CANDIDATES = [
    # Vietnam
    {"company": "DH Travel (Du Lich Quoc Te DH)", "country": "Vietnam", "city": "Ho Chi Minh City",
     "email": "director@dhtravel.com.vn", "website": "https://dhtravel.com.vn",
     "source_url": "https://dhtravel.com.vn/tour-trung-a-kham-pha-con-duong-to-lua-huyen-thoai-dip-tet-ba-tu-nowruz",
     "segment": "Vietnam-outbound", "product_fit": "5-Stans Silk Road", "priority": "A",
     "notes": "22D21N 5-Stans group departure Mar 2026; Kazakhstan Almaty segment"},
    {"company": "VGC Travel", "country": "Vietnam", "city": "Hanoi",
     "email": "info@vgctravel.com.vn", "website": "https://vgctravel.com.vn",
     "source_url": "https://vgctravel.com.vn/en/contact-us",
     "segment": "Vietnam-outbound", "product_fit": "5-Stans Silk Road", "priority": "A",
     "notes": "5-Stans Silk Road group tour Oct 2026"},
    {"company": "ATNT Travel & Tour", "country": "Vietnam", "city": "Ho Chi Minh City",
     "email": "info@atnttravel.com", "website": "https://atnttravel.com",
     "source_url": "https://atnttravel.com/contact-us/",
     "segment": "Vietnam-outbound", "product_fit": "4-Stans Silk Road", "priority": "A",
     "notes": "Escorted Central Asia Silk Road 2026; min 16 pax group"},
    {"company": "Mai Tours", "country": "Vietnam", "city": "Hanoi",
     "email": "info@maitours.vn", "website": "https://maitours.vn",
     "source_url": "https://maitours.vn/tour/trai-tim-trung-a/",
     "segment": "Vietnam-outbound", "product_fit": "KZ+KG", "priority": "A",
     "notes": "9D8N Kazakhstan-Kyrgyzstan Heart of Central Asia package"},
    {"company": "Vietrantour", "country": "Vietnam", "city": "Hanoi",
     "email": "booking@vietrantour.com.vn", "website": "https://vietrantour.com.vn",
     "source_url": "https://vietrantour.com.vn/kazakhstan",
     "segment": "Vietnam-outbound", "product_fit": "5-Stans", "priority": "A",
     "notes": "5-Stans Silk Road discovery package from Hanoi"},
    {"company": "Le Phong Travel", "country": "Vietnam", "city": "Ho Chi Minh City",
     "email": "info@lephongtravel.com.vn", "website": "https://lephongtravel.com.vn",
     "source_url": "https://lephongtravel.com.vn/kazakhstan-kyrgyzstan",
     "segment": "Vietnam-outbound", "product_fit": "KZ+KG", "priority": "A",
     "notes": "9N8D Kazakhstan-Kyrgyzstan since 1995"},
    {"company": "Authentic Asia", "country": "Vietnam", "city": "Hanoi",
     "email": "sales@authentic-asia.com", "website": "https://authentic-asia.com",
     "source_url": "https://authentic-asia.com/contact-us",
     "segment": "Vietnam-outbound", "product_fit": "Central Asia", "priority": "B",
     "notes": "B2B DMC/outbound; Kazakhstan in destination list"},
    {"company": "HaloBay Travel", "country": "Vietnam", "city": "Ho Chi Minh City",
     "email": "info@halobay.vn", "website": "https://www.halobay.vn",
     "source_url": "https://www.halobay.vn/pages/contact",
     "segment": "Vietnam-outbound", "product_fit": "KZ+KG", "priority": "A",
     "notes": "10N9D Kazakhstan-Kyrgyzstan all-inclusive group"},
    {"company": "Premier Tour Vietnam", "country": "Vietnam", "city": "Ho Chi Minh City",
     "email": "info@premiertour.com.vn", "website": "https://premiertour.com.vn",
     "source_url": "https://premiertour.com.vn/contact",
     "segment": "Vietnam-outbound", "product_fit": "Central Asia", "priority": "B",
     "notes": "Outbound package operator; Central Asia product lines"},
    {"company": "Transviet Travel", "country": "Vietnam", "city": "Ho Chi Minh City",
     "email": "info@transviet.com", "website": "https://www.transviet.com",
     "source_url": "https://www.transviet.com/contact-us",
     "segment": "Vietnam-outbound", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Large outbound operator; CIS/Central Asia desk potential"},
    # Korea / Japan
    {"company": "CIS Tour (Korea)", "country": "South Korea", "city": "Almaty/Seoul desk",
     "email": "info@cis-tour.com", "website": "http://cis-tour.com",
     "source_url": "http://cis-tour.com/about",
     "segment": "Korea-outbound", "product_fit": "KZ+CA", "priority": "A",
     "notes": "Korean-managed Central Asia specialist; Kazakhstan packages"},
    {"company": "Small Star Tour (Jageunbyeol)", "country": "South Korea", "city": "Seoul",
     "email": "smallstar@smallstartour.com", "website": "https://smallstartour.com",
     "source_url": "https://smallstartour.com/package/ttt_12days/",
     "segment": "Korea-outbound", "product_fit": "5-Stans", "priority": "A",
     "notes": "12-day Central Asia TTT group series"},
    {"company": "Five Star Club (Japan)", "country": "Japan", "city": "Tokyo",
     "email": "info@fivestar-club.co.jp", "website": "https://www.fivestar-club.jp",
     "source_url": "https://www.fivestar-club.jp/tour/?tcd=7UK72-AOZ-X",
     "segment": "Asia-group", "product_fit": "KZ", "priority": "A",
     "notes": "Kazakhstan specialist; 130+ KZ tour courses; group 19 pax bus tours"},
    {"company": "Earth Design KIR Tour", "country": "Japan", "city": "Tokyo",
     "email": "info@earth-d.co.jp", "website": "https://www.earth-d.co.jp",
     "source_url": "https://www.earth-d.co.jp/contact",
     "segment": "Asia-group", "product_fit": "Central Asia", "priority": "A",
     "notes": "Central Asia specialist; Uzbekistan/Kazakhstan arrangements for JP market"},
    {"company": "Indus Travel Co.", "country": "Japan", "city": "Tokyo",
     "email": "industokyo@indus-travel.com", "website": "https://www.indus-travel.com",
     "source_url": "https://www.otoa.com/english/full_member/detail.php?serial=297",
     "segment": "Asia-group", "product_fit": "KZ+UZ", "priority": "B",
     "notes": "OTOA member; territory includes Kazakhstan Uzbekistan Kyrgyzstan"},
    {"company": "Very Good Tour (Korea)", "country": "South Korea", "city": "Seoul",
     "email": "info@verygoodtour.com", "website": "https://www.verygoodtour.com",
     "source_url": "https://www.verygoodtour.com/customer/inquiry",
     "segment": "Korea-outbound", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Major KR outbound; Central Asia product search on site"},
    # India
    {"company": "TripsTide Pvt Ltd", "country": "India", "city": "Noida",
     "email": "sales@tripstide.com", "website": "https://tripstide.com",
     "source_url": "https://tripstide.com/",
     "segment": "India-group", "product_fit": "CIS/KZ", "priority": "A",
     "notes": "B2B DMC CIS specialist; Kazakhstan fixed departures"},
    {"company": "Russia Holiday Tours", "country": "India", "city": "Mumbai",
     "email": "info@russiaholidaytours.com", "website": "https://www.russiaholidaytours.com",
     "source_url": "https://www.russiaholidaytours.com/contact-us",
     "segment": "India-group", "product_fit": "KZ+UZ+RU", "priority": "A",
     "notes": "Monthly group tours Kazakhstan Uzbekistan; Delhi Mumbai offices"},
    {"company": "Cox & Kings India", "country": "India", "city": "Mumbai",
     "email": "customize@coxandkings.com", "website": "https://www.coxandkings.com",
     "source_url": "https://www.coxandkings.com/contact-us",
     "segment": "India-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Large group operator; Central Asia custom groups"},
    {"company": "Thomas Cook India", "country": "India", "city": "Mumbai",
     "email": "groups@thomascook.in", "website": "https://www.thomascook.in",
     "source_url": "https://www.thomascook.in/contact-us",
     "segment": "India-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Corporate/group desk; alt enquiry@thomascook.in blocked"},
    {"company": "SOTC Travel", "country": "India", "city": "Mumbai",
     "email": "groups@sotc.in", "website": "https://www.sotc.in",
     "source_url": "https://www.sotc.in/contact-us",
     "segment": "India-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Group holidays desk; MICE incentive.travel@sotc.in already contacted"},
    {"company": "Raj Travels", "country": "India", "city": "Mumbai",
     "email": "info@rajtravels.com", "website": "https://www.rajtravels.com",
     "source_url": "https://www.rajtravels.com/contact-us",
     "segment": "India-group", "product_fit": "Outbound groups", "priority": "C",
     "notes": "IATA agency; international group packages"},
    # Philippines
    {"company": "Pan Pacific Travel", "country": "Philippines", "city": "Makati",
     "email": "info@panpacifictravel.com.ph", "website": "https://www.panpacifictravel.com.ph",
     "source_url": "https://www.panpacifictravel.com.ph/contact-us",
     "segment": "Asia-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "IATA; outbound group tours"},
    {"company": "Travelite Express", "country": "Philippines", "city": "Makati",
     "email": "info@travelite.com.ph", "website": "https://www.travelite.com.ph",
     "source_url": "https://www.travelite.com.ph/contact-us",
     "segment": "Asia-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Outbound GIT specialist Philippines"},
    {"company": "Discovery Primea Travel", "country": "Philippines", "city": "Manila",
     "email": "sales@discoveryprimea.com", "website": "https://www.discoveryprimea.com",
     "source_url": "https://www.discoveryprimea.com/contact",
     "segment": "Asia-group", "product_fit": "Luxury groups", "priority": "C",
     "notes": "Premium outbound tour operator"},
    # Turkey
    {"company": "MNG Turizm", "country": "Turkey", "city": "Istanbul",
     "email": "info@mngturizm.com", "website": "https://www.mngturizm.com",
     "source_url": "https://www.mngturizm.com/iletisim",
     "segment": "MICE-TMC", "product_fit": "KZ+UZ Silk Road", "priority": "A",
     "notes": "A-Group IATA tour operator; Uzbekistan-Kazakhstan Silk Road packages"},
    {"company": "Ani Turizm", "country": "Turkey", "city": "Istanbul",
     "email": "info@aniturizm.com", "website": "https://www.aniturizm.com",
     "source_url": "https://www.aniturizm.com/iletisim",
     "segment": "Asia-group", "product_fit": "Central Asia", "priority": "B",
     "notes": "Outbound tour operator; Central Asia programs"},
    # Egypt / Jordan / Morocco
    {"company": "Lef El Donia Travel", "country": "Egypt", "city": "Cairo",
     "email": "info@lefeldonia.com", "website": "https://www.lefeldonia.com",
     "source_url": "https://www.lefeldonia.com/",
     "segment": "MICE-TMC", "product_fit": "Outbound groups", "priority": "B",
     "notes": "Egyptian outbound + incoming; international group programs"},
    {"company": "Triad Travel Egypt", "country": "Egypt", "city": "Cairo",
     "email": "info@triadtravel.net", "website": "https://triadtravel.com.eg",
     "source_url": "https://triadtravel.com.eg/contact-us/",
     "segment": "MICE-TMC", "product_fit": "Outbound groups", "priority": "B",
     "notes": "Outbound/incoming Egypt operator"},
    {"company": "Petra Travel & Tourism (Jordan)", "country": "Jordan", "city": "Amman",
     "email": "info@petratravel.com", "website": "https://www.petratravel.com",
     "source_url": "https://www.petratravel.com/contact-us",
     "segment": "MICE-TMC", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Jordan outbound/incoming; group tour operator"},
    {"company": "Atlas Voyages (Morocco)", "country": "Morocco", "city": "Casablanca",
     "email": "contact@atlasvoyages.com", "website": "https://www.atlasvoyages.com",
     "source_url": "https://www.atlasvoyages.com/en/contact",
     "segment": "MICE-TMC", "product_fit": "Outbound groups", "priority": "B",
     "notes": "Leading Moroccan TMC; outbound group travel"},
    # UK / EU
    {"company": "Go Russia Ltd", "country": "United Kingdom", "city": "London",
     "email": "info@justgorussia.co.uk", "website": "https://www.justgorussia.co.uk",
     "source_url": "https://www.justgorussia.co.uk/pdf/SR-08.pdf",
     "segment": "CIS-desk", "product_fit": "5-Stans", "priority": "A",
     "notes": "5-Stans Silk Road group tour SR-08; Kazakhstan segment"},
    {"company": "Wendy Wu Tours UK", "country": "United Kingdom", "city": "London",
     "email": "info@wendywutours.co.uk", "website": "https://www.wendywutours.co.uk",
     "source_url": "https://www.wendywutours.co.uk/contact-us",
     "segment": "Asia-group", "product_fit": "Central Asia", "priority": "A",
     "notes": "Journey through Central Asia 27D group incl. Almaty"},
    {"company": "Wild Frontiers Travel", "country": "United Kingdom", "city": "London",
     "email": "info@wildfrontierstravel.com", "website": "https://www.wildfrontierstravel.com",
     "source_url": "https://www.wildfrontierstravel.com/en_GB/contact-us",
     "segment": "Asia-group", "product_fit": "KZ", "priority": "A",
     "notes": "Small group max 12; Kazakhstan destination expert"},
    {"company": "Steppes Travel", "country": "United Kingdom", "city": "Cirencester",
     "email": "info@steppestravel.com", "website": "https://www.steppestravel.com",
     "source_url": "https://www.steppestravel.com/contact-us/",
     "segment": "Asia-group", "product_fit": "Silk Road", "priority": "A",
     "notes": "Central Asia Silk Route expert-led group tours"},
    # Hong Kong
    {"company": "GLO Travel Limited", "country": "Hong Kong", "city": "Sheung Wan",
     "email": "info@glotravel.hk", "website": "https://glotravel.hk",
     "source_url": "https://glotravel.hk/contact-us/",
     "segment": "Asia-group", "product_fit": "5-Stans", "priority": "A",
     "notes": "HK licence 354384; Turkmenistan Kazakhstan Uzbekistan depth tours"},
    {"company": "DeWonder Travel", "country": "Hong Kong", "city": "Sheung Wan",
     "email": "info@dewonder.travel", "website": "https://dewonder.travel",
     "source_url": "https://dewonder.travel/central-asia/",
     "segment": "Asia-group", "product_fit": "Central Asia", "priority": "A",
     "notes": "Silk Road specialist; small team Central Asia depth tours"},
    {"company": "EGL Tours", "country": "Hong Kong", "city": "Mong Kok",
     "email": "egltours@egltours.com", "website": "https://www.egltours.com",
     "source_url": "https://www.egltours.com/en/contact-us",
     "segment": "Asia-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Major HK outbound; Europe Central Asia Africa group tours"},
    {"company": "Sunflower Travel HK", "country": "Hong Kong", "city": "Tsim Sha Tsui",
     "email": "enquiry@hksunflower.com", "website": "https://www.hksunflower.com",
     "source_url": "https://www.hksunflower.com/en/contact",
     "segment": "Asia-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Group tours Europe Central Asia Africa"},
    # Indonesia (additional)
    {"company": "Hayatun Tour", "country": "Indonesia", "city": "Jakarta",
     "email": "info@hayatuntour.com", "website": "https://www.hayatuntour.com",
     "source_url": "https://www.hayatuntour.com/paket/paket-tour-uzbekistan-8-hari-halal-hayatun-tour-2026/",
     "segment": "halal-Asia", "product_fit": "UZ+CA halal", "priority": "A",
     "notes": "Halal Uzbekistan 8D; hayatuntour@gmail.com blocked"},
    {"company": "Asiya Tour Indonesia", "country": "Indonesia", "city": "Jakarta",
     "email": "info@asiyatour.com", "website": "https://asiyatour.com",
     "source_url": "https://asiyatour.com/contact",
     "segment": "halal-Asia", "product_fit": "UZ halal", "priority": "A",
     "notes": "Muslim tour specialist Central Asia programs"},
    {"company": "PT Panorama JTB Tours Indonesia", "country": "Indonesia", "city": "Jakarta",
     "email": "jakarta@panorama-jtb.com", "website": "https://www.panorama-jtb.com",
     "source_url": "https://www.panorama-jtb.com/contact",
     "segment": "Asia-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Panorama desk; tours@panorama-jtb.com already contacted"},
    # Malaysia (additional)
    {"company": "Amit Travel", "country": "Malaysia", "city": "Kuala Lumpur",
     "email": "sales@amitravel.my", "website": "https://www.amitravel.my",
     "source_url": "https://www.amitravel.my/contact-us",
     "segment": "halal-Asia", "product_fit": "Outbound groups", "priority": "B",
     "notes": "info@amitravel.my blocked; try sales desk"},
    {"company": "KOP Travel", "country": "Malaysia", "city": "Kuala Lumpur",
     "email": "info@koptravel.com.my", "website": "https://www.koptravel.com.my",
     "source_url": "https://www.koptravel.com.my/contact-us",
     "segment": "halal-Asia", "product_fit": "Outbound groups", "priority": "B",
     "notes": "MATTA member outbound operator"},
    {"company": "GD Travel", "country": "Malaysia", "city": "Kuala Lumpur",
     "email": "info@gdtravel.com.my", "website": "https://www.gdtravel.com.my",
     "source_url": "https://www.gdtravel.com.my/contact",
     "segment": "halal-Asia", "product_fit": "Outbound groups", "priority": "B",
     "notes": "Outbound package tours Malaysia"},
    # Singapore (additional)
    {"company": "EU Holidays", "country": "Singapore", "city": "Singapore",
     "email": "enquiry@euholidays.com.sg", "website": "https://www.euholidays.com.sg",
     "source_url": "https://www.euholidays.com.sg/contact-us",
     "segment": "Asia-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "sales@euholidays.com.sg blocked; enquiry desk"},
    {"company": "Asia Exotic Expeditions", "country": "Singapore", "city": "Singapore",
     "email": "tours@asiaexotic.com", "website": "https://www.asiaexotic.com",
     "source_url": "https://www.asiaexotic.com/contact",
     "segment": "Asia-group", "product_fit": "Adventure groups", "priority": "B",
     "notes": "admin@asia-expeditions.org blocked; different entity"},
    {"company": "Nam Ho Travel", "country": "Singapore", "city": "Singapore",
     "email": "info@namho.com.sg", "website": "https://www.namho.com.sg",
     "source_url": "https://www.namho.com.sg/contact-us",
     "segment": "Asia-group", "product_fit": "Multi-destination", "priority": "B",
     "notes": "Major SG outbound NATAS member"},
]


def main():
    blocklist = load_blocklist()
    print(f"Blocklist size: {len(blocklist)}", file=sys.stderr)

    verified = []
    rejected = []

    for c in CANDIDATES:
        email = c["email"].strip().lower()
        if email in blocklist:
            rejected.append((c["company"], email, "blocklist"))
            continue

        html = fetch_url(c["source_url"])
        ok, reason = verify_email_on_page(email, html)
        if not ok:
            # try website homepage
            html2 = fetch_url(c["website"])
            ok2, reason2 = verify_email_on_page(email, html2)
            if ok2:
                ok, reason = ok2, f"homepage:{reason2}"
                c["source_url"] = c["website"]
            else:
                rejected.append((c["company"], email, f"unverified:{reason}|{reason2}"))
                continue

        verified.append({**c, "verified": "Y", "verify_method": reason})

    print(f"Verified: {len(verified)} | Rejected: {len(rejected)}", file=sys.stderr)
    for r in rejected:
        print(f"REJECT: {r[0]} | {r[1]} | {r[2]}", file=sys.stderr)

    out = ROOT / "deliverables" / ".tmp_batch8_verify_results.csv"
    fields = ["company", "country", "city", "email", "website", "contact_name",
              "segment", "source_url", "verified", "product_fit", "priority", "notes", "verify_method"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for v in verified:
            row = {k: v.get(k, "") for k in fields}
            row["contact_name"] = ""
            row["source_url"] = v.get("source_url", "")
            w.writerow(row)

    print(str(out))


if __name__ == "__main__":
    main()
