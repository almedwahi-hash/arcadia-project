"""Generate Arcadia B2B Rate Sheet PDF with ReportLab (ASCII-only, Helvetica)."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "deliverables" / "pdfs" / "Arcadia-B2B-Rate-Sheet-Almaty.pdf"

NAVY = colors.HexColor("#0f2440")
GOLD = colors.HexColor("#c9a227")
MUTED = colors.HexColor("#5c6b7a")


def build_pdf(path: Path) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Arcadia B2B Rate Sheet Almaty",
        author="Arcadia Tourism Company",
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=NAVY,
        spaceAfter=4,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=NAVY,
        spaceBefore=14,
        spaceAfter=6,
        leftIndent=0,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.black,
    )
    muted = ParagraphStyle("Muted", parent=body, fontSize=9, textColor=MUTED)

    story = []

    story.append(Paragraph("Arcadia Tourism Company", title))
    story.append(
        Paragraph(
            "Licensed DMC - Kazakhstan and Central Asia | Almaty, Kazakhstan | arcadia-tour.com",
            muted,
        )
    )
    story.append(Spacer(1, 10))

    story.append(Paragraph("B2B Net Group Rates - Almaty 5 Days / 4 Nights", h2))
    story.append(
        Paragraph(
            "Ground only | June - October 2026 | Min 15 pax | Max 40 pax | "
            "Hotel: 4-star downtown (Resident City or equivalent)",
            muted,
        )
    )

    story.append(Paragraph("Net B2B Tier Pricing (DBL/TWN basis)", h2))
    pricing = [
        ["Pax Band", "Net PP (USD)", "Approx EUR", "Vehicle"],
        ["15 - 19", "$745", "EUR 685", "Coaster 20-seat"],
        ["20 - 29", "$685", "EUR 630", "Coaster / mid-bus"],
        ["30 - 40", "$625", "EUR 575", "Mercedes 49-seat"],
    ]
    t = Table(pricing, colWidths=[70, 80, 80, 120])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8dee6")),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#f5ecd4")),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Paragraph("Deposit 30% on confirmation | Balance due 14 days before arrival", muted))

    story.append(Paragraph("Standard 5-Day Almaty Group Programme", h2))
    program = [
        ["Day", "Programme"],
        [
            "D1",
            "Airport meet and greet, transfer to 4-star hotel, room check-in and rest",
        ],
        [
            "D2",
            "Medeu mountain, cable car to Shymbulak (3 stops), scenic views and activities, "
            "halal lunch, Arbat Street walk",
        ],
        [
            "D3",
            "Nature reserve entry (approx. $1/person), Ma-Arsan valley riverside walk, "
            "Bear Valley (Ayusai Visit Center)",
        ],
        [
            "D4",
            "Oi-Qaraghay resort day trip (40 km from Almaty), recreational activities, return to city",
        ],
        [
            "D5",
            "Green Bazaar (Zelyoni Bazar), Rakhat chocolate factory, Kok-Tobe cable car, "
            "hotel checkout, airport transfer, end of ground services",
        ],
    ]
    pt = Table(program, colWidths=[36, doc.width - 36])
    pt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 1), (0, -1), colors.HexColor("#f5ecd4")),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (1, 1), (1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8dee6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(pt)

    story.append(Paragraph("Optional Extra Tours (separate quote)", h2))
    for item in [
        "Charyn Canyon (Sharyn) - full day, approx. 3h drive each way - price on request",
        "Kolsai Lakes - full day, approx. 3h drive each way - price on request",
        "Kaindy Lake - full day extension - price on request",
        "Other optional excursions - quote on request",
    ]:
        story.append(Paragraph(f"- {item}", body))
    story.append(
        Paragraph(
            "Optional extras are not included in the standard net rates above. "
            "Confirm availability and supplement before booking.",
            muted,
        )
    )

    story.append(Paragraph("Inclusions", h2))
    for item in [
        "Daily group transport with professional driver",
        "Licensed Arabic-speaking guide - 8 hours/day",
        "4-star downtown Almaty hotel - DBL/TWN - 4 nights",
        "Daily breakfast + 2 halal lunches + 2 halal dinners",
        "Entrances: Kok-Tobe, Shymbulak / Medeu cable car (seasonal), Oi-Qaraghay resort, "
        "Bear Valley - as per standard programme above (Charyn, Kolsai, Kaindy are optional extras only)",
        "Airport transfers and check-in assistance",
        "24/7 WhatsApp group leader support",
    ]:
        story.append(Paragraph(f"- {item}", body))

    story.append(Paragraph("Not Included", h2))
    for item in [
        "International or domestic flights",
        "Visa fees (KZ e-visa approx. $80, or visa-free entry where applicable)",
        "Travel insurance, tips, personal expenses, optional activities",
        "Single room supplement ($48/night)",
    ]:
        story.append(Paragraph(f"- {item}", body))

    story.append(Paragraph("Child Policy", h2))
    child = [
        ["Category", "Policy"],
        ["0-1 years", "Free, no bed"],
        ["2-5 years", "35% of adult rate"],
        ["6-11 years", "65% of adult rate"],
        ["12+ years", "Full adult rate"],
        ["Single room", "$48 / night supplement"],
    ]
    ct = Table(child, colWidths=[90, doc.width - 90])
    ct.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8dee6")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(ct)

    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Mohammad Ali</b>", body))
    story.append(Paragraph("Business Development Manager, Arcadia Tourism Company", body))
    story.append(Paragraph("WhatsApp: +77051181845", body))
    story.append(Paragraph("Email: info@arcadia-tour.com", body))
    story.append(Paragraph("Web: https://arcadia-tour.com/", body))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "B2B net rates | subject to availability | quote valid 14 days | non-exclusive partner distribution",
            muted,
        )
    )

    doc.build(story)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(OUT)
    print(f"PDF written: {OUT}")
