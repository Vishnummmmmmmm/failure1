from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime

# PulseSphere brand colours
COLOR_PRIMARY    = HexColor('#0A0A0F')   # near-black bg
COLOR_ACCENT     = HexColor('#00E5FF')   # neon cyan
COLOR_RED        = HexColor('#FF3B3B')   # crisis red
COLOR_YELLOW     = HexColor('#FFB800')   # watch yellow
COLOR_GREEN      = HexColor('#00FF87')   # low green
COLOR_SURFACE    = HexColor('#1A1A2E')   # card bg
COLOR_TEXT       = HexColor('#E0E0E0')   # body text

def generate_weekly_pdf(
    brand_name: str,
    cvi_history: list[dict],    # [{score, level, recorded_at}]
    alerts: list[dict],          # [{severity, cvi_score, triggered_at}]
    playbooks: list[dict],       # [{actions, press_statement, rating}]
    org_logo_url: str = None
) -> bytes:
    """
    TC17: Returns valid PDF bytes. Content-Type application/pdf.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Header ────────────────────────────────────────────────
    header_style = ParagraphStyle(
        'Header',
        fontSize=22, leading=28,
        textColor=COLOR_ACCENT,
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    )
    sub_style = ParagraphStyle(
        'Sub',
        fontSize=10, leading=14,
        textColor=COLOR_TEXT,
        fontName='Helvetica'
    )
    label_style = ParagraphStyle(
        'Label',
        fontSize=8, leading=12,
        textColor=HexColor('#888888'),
        fontName='Helvetica-Bold'
    )
    value_style = ParagraphStyle(
        'Value',
        fontSize=18, leading=22,
        textColor=COLOR_ACCENT,
        fontName='Helvetica-Bold'
    )

    story.append(Paragraph('PULSESPHERE', header_style))
    story.append(Paragraph(f'Weekly Crisis Intelligence Report — {brand_name}', sub_style))
    story.append(Paragraph(f'Generated: {datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")}', label_style))
    story.append(HRFlowable(width='100%', thickness=1, color=COLOR_ACCENT, spaceAfter=8))
    story.append(Spacer(1, 6*mm))

    # ── Summary Stats Row ─────────────────────────────────────
    peak_cvi     = max((r['score'] for r in cvi_history), default=0)
    avg_cvi      = round(sum(r['score'] for r in cvi_history) / max(len(cvi_history), 1), 1)
    total_alerts = len(alerts)
    critical_alerts = sum(1 for a in alerts if a.get('severity') == 'CRITICAL')

    stats_data = [
        [Paragraph('PEAK CVI', label_style),     Paragraph('AVG CVI', label_style),
         Paragraph('TOTAL ALERTS', label_style), Paragraph('CRITICAL', label_style)],
        [Paragraph(str(peak_cvi), value_style),  Paragraph(str(avg_cvi), value_style),
         Paragraph(str(total_alerts), value_style), Paragraph(str(critical_alerts), value_style)],
    ]
    stats_table = Table(stats_data, colWidths=[45*mm]*4)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_SURFACE),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [COLOR_SURFACE, COLOR_SURFACE]),
        ('BOX',         (0,0), (-1,-1), 0.5, COLOR_ACCENT),
        ('INNERGRID',   (0,0), (-1,-1), 0.25, HexColor('#333355')),
        ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 8*mm))

    # ── CVI Trend Chart ───────────────────────────────────────
    story.append(Paragraph('CVI TREND — LAST 7 DAYS', label_style))
    story.append(Spacer(1, 3*mm))

    if len(cvi_history) >= 2:
        drawing = Drawing(180*mm, 50*mm)
        lp = LinePlot()
        lp.x = 5; lp.y = 5
        lp.width  = 170*mm
        lp.height = 40*mm
        scores = [r['score'] for r in cvi_history[-30:]]
        lp.data = [list(enumerate(scores))]
        lp.lines[0].strokeColor  = COLOR_ACCENT
        lp.lines[0].strokeWidth  = 1.5
        lp.joinedLines = 1
        drawing.add(lp)
        story.append(drawing)
    else:
        story.append(Paragraph('Insufficient data for trend chart (need 2+ snapshots)', sub_style))

    story.append(Spacer(1, 8*mm))

    # ── Alert Log ─────────────────────────────────────────────
    story.append(Paragraph('ALERT LOG', label_style))
    story.append(Spacer(1, 3*mm))

    if alerts:
        alert_rows = [[Paragraph('SEVERITY', label_style), Paragraph('CVI', label_style), Paragraph('TRIGGERED', label_style)]]
        for a in alerts[:10]:
            sev = a.get('severity', '?')
            sev_color = {'CRITICAL': COLOR_RED, 'HIGH': COLOR_RED,
                         'MEDIUM': COLOR_YELLOW, 'WATCH': COLOR_GREEN}.get(sev, COLOR_TEXT)
            alert_rows.append([
                Paragraph(f'<font color="#{sev_color.hexval()[1:]}"><b>{sev}</b></font>', sub_style),
                Paragraph(str(round(a.get('cvi_score', 0), 1)), sub_style),
                Paragraph(str(a.get('triggered_at', ''))[:16], sub_style)
            ])
        alert_table = Table(alert_rows, colWidths=[45*mm, 30*mm, 105*mm])
        alert_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,0),  COLOR_SURFACE),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#111120'), COLOR_SURFACE]),
            ('BOX',         (0,0), (-1,-1), 0.5, HexColor('#333355')),
            ('INNERGRID',   (0,0), (-1,-1), 0.25, HexColor('#222244')),
            ('TOPPADDING',  (0,0), (-1,-1), 3),
            ('BOTTOMPADDING',(0,0),(-1,-1), 3),
        ]))
        story.append(alert_table)
    else:
        story.append(Paragraph('No alerts triggered this week. CVI remained below 40.', sub_style))

    story.append(Spacer(1, 8*mm))

    # ── Latest Playbook Summary ────────────────────────────────
    if playbooks:
        pb = playbooks[0]
        story.append(Paragraph('LATEST CRISIS PLAYBOOK', label_style))
        story.append(Spacer(1, 3*mm))
        for action in pb.get('actions', [])[:3]:
            story.append(Paragraph(
                f"<b>Step {action.get('step','?')} [{action.get('urgency','?')}]</b> — {action.get('action','')}",
                sub_style
            ))
            story.append(Spacer(1, 2*mm))
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph('PRESS STATEMENT', label_style))
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(pb.get('press_statement', '')[:600], sub_style))

    # ── Footer ────────────────────────────────────────────────
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=HexColor('#333355')))
    story.append(Paragraph(
        'PulseSphere Crisis Intelligence Platform · Confidential · Not for distribution',
        ParagraphStyle('Footer', fontSize=7, textColor=HexColor('#555577'),
                       fontName='Helvetica', alignment=TA_CENTER)
    ))

    doc.build(story)
    return buffer.getvalue()
