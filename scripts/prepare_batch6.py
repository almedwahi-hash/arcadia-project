# -*- coding: utf-8 -*-
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTNERS = ROOT / "deliverables" / "b2b-partner-targets.md"
BATCH5 = ROOT / ".tmp_batch5_remaining.json"
OUT_MD = ROOT / "deliverables" / "sales-outreach-batch6-targets-ar.md"

def parse_partner_rows(text: str) -> list[dict]:
    rows: list[dict] = []
    for line in text.splitlines():
        if not line.strip().startswith("|") or "@" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", line)
        if not emails:
            continue
        email = emails[0].lower()
        if "arcadia" in email:
            continue
        company = re.sub(r"\*\*([^*]+)\*\*", r"\1", cells[1] if len(cells) > 1 else cells[0])
        company = re.sub(r"\*\*", "", company).strip()
        if not company or company in ("Company", "--------"):
            continue
        rows.append({"company": company, "email": email, "note": cells[-1] if cells else ""})
    seen: set[str] = set()
    uniq: list[dict] = []
    for r in rows:
        if r["email"] in seen:
            continue
        seen.add(r["email"])
        uniq.append(r)
    return uniq

def main() -> None:
    batch5_emails: set[str] = set()
    if BATCH5.exists():
        batch5_emails = {x["email"].lower() for x in json.loads(BATCH5.read_text(encoding="utf-8"))}
    candidates = parse_partner_rows(PARTNERS.read_text(encoding="utf-8"))
    picked: list[dict] = []
    for r in candidates:
        if r["email"] in batch5_emails:
            continue
        if any(x in r["email"] for x in ("noreply", "careers", "hr@", "jobs@")):
            continue
        picked.append(r)
        if len(picked) >= 18:
            break

    lines = [
        "# Batch 6 — B2B targets (prepared)",
        "",
        "> Status: `prepared` — not sent yet.",
        f"> Prepared: 2026-06-25 | Count: {len(picked)}",
        "",
        "| # | Company | Email | Note |",
        "|---|---------|-------|------|",
    ]
    for i, r in enumerate(picked, 1):
        note = re.sub(r"\*\*", "", r.get("note", ""))[:80]
        lines.append(f"| {i} | **{r['company']}** | **{r['email']}** | {note} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(len(picked))

if __name__ == "__main__":
    main()
