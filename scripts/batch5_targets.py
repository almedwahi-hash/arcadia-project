# -*- coding: utf-8 -*-
"""Build batch5 JSON from markdown."""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "deliverables" / "sales-outreach-batch5-targets-ar.md"
OUT = ROOT / ".tmp_batch5_remaining.json"
GCC_OUT = ROOT / ".tmp_batch5_gcc_followups.json"
WEB = "https://arcadia-tour.com/"

def strip_md(s: str) -> str:
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return s.strip()

def parse_templates(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for seg in ("A", "B", "C"):
        m = re.search(r"### Segment " + seg + r".*?(### Segment |## 5\.|\Z)", text, re.S)
        if not m:
            continue
        sub = re.search(r"\*\*Subject:\*\*\s*(.+?)\s*\n\n(.*?)(?=\n---|\n###|\Z)", m.group(0), re.S)
        if sub:
            body = re.sub(r"^```\n?|```\s*$", "", sub.group(2).strip()).strip()
            out[seg] = {"subject": sub.group(1).strip(), "body": body}
    m = re.search(r"### Segment C.*?India.*?\*\*Subject:\*\*\s*(.+?)\s*\n\n(.*?)(?=\n---|\n## |\Z)", text, re.S)
    if m:
        body = re.sub(r"^```\n?|```\s*$", "", m.group(2).strip()).strip()
        out["C_IN"] = {"subject": m.group(1).strip(), "body": body}
    return out

def parse_rows(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        if not line.strip().startswith("|") or "@" not in line:
            continue
        cells = [strip_md(c.strip()) for c in line.strip().strip("|").split("|")]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        rows.append({"num": int(cells[0]), "company": cells[1], "email": cells[3].lower(), "pitch": cells[5], "segment": cells[6].upper()})
    return rows

def dear(company: str) -> str:
    name = re.sub(r"\s*\([^)]*\)", "", company).strip()
    name = re.sub(r"\s+(alt|CS|Agent desk).*$", "", name, flags=re.I).strip()
    return f"Dear {name} Team,"

def personalize(body: str, company: str) -> str:
    lines = body.splitlines()
    d = dear(company)
    for i, line in enumerate(lines):
        if line.startswith("Dear ") and "Team," in line:
            lines[i] = d
            break
    else:
        lines = [d, ""] + lines
    text = "\n".join(lines)
    if WEB not in text:
        text += f"\n\n{WEB}\n"
    return text

def template_key(row: dict) -> str:
    if row["segment"] == "D":
        return "C"
    if row["segment"] == "C" and row["num"] in (1, 2):
        return "C_IN"
    return row["segment"] if row["segment"] in "ABC" else "C"

def build_batch5() -> list[dict]:
    text = MD.read_text(encoding="utf-8")
    tpls = parse_templates(text)
    items = []
    for row in parse_rows(text):
        key = template_key(row)
        tpl = tpls.get(key) or tpls["C"]
        items.append({"num": row["num"], "company": row["company"], "email": row["email"], "segment": row["segment"], "subject": tpl["subject"], "body": personalize(tpl["body"], row["company"])})
    return items

GCC = [
    ("gcc-citron", "Citron Tours", "info@citrontours.ae", "6-day Almaty group packages"),
    ("gcc-tabeer", "Tabeer Tours", "inquiries@tabeertours.com", "Kazakhstan and Russia holiday packages"),
    ("gcc-alqaed", "Alqaed Travel", "info@alqaedtravel.com", "KZ/UZ/RU package tours"),
    ("gcc-arabian-sky", "Arabian Sky Travels", "info@arabianskytravels.com", "CIS multi-country group departures"),
    ("gcc-aamal", "Aamal Travel", "sales@aamal-travel.com", "Russia group packages with KZ/UZ add-ons"),
]

def build_gcc() -> list[dict]:
    subj = "Follow-up: B2B Kazakhstan Ground Partner | Arcadia Tourism (Almaty)"
    items = []
    for i, (gid, co, em, angle) in enumerate(GCC, 1):
        body = f"""Dear {co} Team,

Following up on our B2B note from last week — sharing updated Kazakhstan group ground rates for Q3-Q4 2026.

Arcadia Tourism Company — Almaty DMC (10+ years, 7,500+ Arabic/GCC clients):
- Net B2B ground rates for groups (15-40 pax)
- Arabic-speaking guides and halal meal coordination
- Direct hotel contracts in Almaty and Silk Road sites

Your focus on {angle} matches our daily operations.

Attached: B2B rate sheet (Almaty). We can send a sample 5-6 day itinerary on request.

WhatsApp: +77051181845
info@arcadia-tour.com
{WEB}

Best regards,
Mohammad Ali
Business Development Manager
Arcadia Tourism Company
Almaty, Kazakhstan
"""
        items.append({"num": 100 + i, "id": gid, "company": co, "email": em, "subject": subj, "body": body, "kind": "gcc_followup"})
    return items

def write_json() -> tuple[int, int]:
    b = build_batch5()
    g = build_gcc()
    OUT.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    GCC_OUT.write_text(json.dumps(g, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(b), len(g)

if __name__ == "__main__":
    n, m = write_json()
    print(f"batch5={n} gcc={m}")
