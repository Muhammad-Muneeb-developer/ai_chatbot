from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, 
                                Spacer, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from io import BytesIO
from datetime import datetime

def generate_assessment_pdf(assessment_data: dict) -> bytes:
    """
    Generate a highly professional German AI Readiness Assessment PDF
    This is the main function called from your views
    Updated for new database structure
    """
    return generate_professional_pdf(assessment_data)


def generate_professional_pdf(assessment_data: dict) -> bytes:
    """
    Generate a highly professional German AI Readiness Assessment PDF
    Updated for new database structure
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm,
        title=f"KI-Readiness Bewertung - {assessment_data.get('company_name', 'Unternehmen')}"
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Professional Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=32
    )
    
    subtitle_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#16213e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=18
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#0f3460'),
        spaceAfter=15,
        spaceBefore=25,
        fontName='Helvetica-Bold'
    )
    
    subsection_heading = ParagraphStyle(
        'SubsectionHeading',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=colors.HexColor('#16213e'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        textColor=colors.HexColor('#2d2d2d')
    )
    
    highlight_style = ParagraphStyle(
        'Highlight',
        parent=body_style,
        fontSize=12,
        leading=18,
        textColor=colors.HexColor('#0f3460'),
        fontName='Helvetica-Bold'
    )
    
    # === TITLE PAGE ===
    elements.append(Spacer(1, 1.5*cm))
    elements.append(Paragraph("KI-READINESS BEWERTUNG", title_style))
    elements.append(Paragraph("Professionelle Analyse & Strategische Handlungsempfehlungen", subtitle_style))
    elements.append(Spacer(1, 1*cm))
    
    # Company Info Box
    company_info = f"""
    <b>Unternehmen:</b> {assessment_data.get('company_name', 'N/A')}<br/>
    <b>Branche:</b> {assessment_data.get('industry') or 'Nicht angegeben'}<br/>
    <b>Unternehmensgröße:</b> {assessment_data.get('company_size') or 'Nicht angegeben'}<br/>
    <b>Bewertungsdatum:</b> {datetime.now().strftime('%d. %B %Y')}
    """
    
    info_table_data = [[Paragraph(company_info, body_style)]]
    info_table = Table(info_table_data, colWidths=[16*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#0f3460')),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 1.5*cm))
    
    # === SCORE DISPLAY ===
    score = assessment_data.get('calculated_score', 0)
    score_level = assessment_data.get('score_level', 'N/A')
    
    # Determine color based on new scale
    if score >= 70:
        score_color = colors.HexColor('#28a745')  # Green - Hoch
    elif score >= 40:
        score_color = colors.HexColor('#17a2b8')  # Blue - Mittel
    else:
        score_color = colors.HexColor('#ffc107')  # Yellow - Niedrig
    
    score_heading = Paragraph("IHRE KI-READINESS BEWERTUNG", section_heading)
    elements.append(score_heading)
    
    score_display = f"""
    <para alignment="center">
        <font size="60" color="{score_color.hexval()}"><b>{score}</b></font><br/>
        <font size="20" color="#666666">/100 Punkte</font><br/>
        <font size="16" color="{score_color.hexval()}"><b>{score_level}</b></font>
    </para>
    """
    
    score_table = Table([[Paragraph(score_display, body_style)]], colWidths=[16*cm])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('BOX', (0, 0), (-1, -1), 3, score_color),
        ('TOPPADDING', (0, 0), (-1, -1), 30),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(score_table)
    elements.append(PageBreak())
    
    # === EXECUTIVE SUMMARY ===
    analysis = assessment_data.get('chatgpt_analysis', {})
    
    elements.append(Paragraph("EXECUTIVE SUMMARY", section_heading))
    summary_text = analysis.get('executive_summary', 'Analyse wird durchgeführt.')
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # === STRENGTHS ===
    elements.append(Paragraph("IHRE STÄRKEN", section_heading))
    strengths = analysis.get('strengths', [])
    
    for strength in strengths:
        strength_box = Table(
            [[Paragraph(f"<b>✓</b> {strength}", body_style)]],
            colWidths=[16*cm]
        )
        strength_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#4caf50')),
        ]))
        elements.append(strength_box)
        elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # === IMPROVEMENT AREAS ===
    elements.append(Paragraph("VERBESSERUNGSBEREICHE", section_heading))
    weaknesses = analysis.get('weaknesses', [])
    
    for weakness in weaknesses:
        weakness_box = Table(
            [[Paragraph(f"<b>→</b> {weakness}", body_style)]],
            colWidths=[16*cm]
        )
        weakness_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3e0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#ff9800')),
        ]))
        elements.append(weakness_box)
        elements.append(Spacer(1, 0.3*cm))
    
    elements.append(PageBreak())
    
    # === RECOMMENDED USE CASES ===
    elements.append(Paragraph("EMPFOHLENE KI-ANWENDUNGSFÄLLE", section_heading))
    use_cases = analysis.get('recommended_use_cases', [])
    
    for i, use_case in enumerate(use_cases, 1):
        if isinstance(use_case, dict):
            title = use_case.get('title', f'Use Case {i}')
            description = use_case.get('description', '')
            impact = use_case.get('impact', '')
            effort = use_case.get('effort', 'Mittel')
            priority = use_case.get('priority', 'Mittel')
            
            use_case_content = f"""
            <b>{i}. {title}</b><br/>
            {description}<br/>
            <b>Impact:</b> {impact}<br/>
            <b>Aufwand:</b> {effort} | <b>Priorität:</b> {priority}
            """
        else:
            use_case_content = f"<b>{i}.</b> {use_case}"
        
        use_case_box = Table(
            [[Paragraph(use_case_content, body_style)]],
            colWidths=[16*cm]
        )
        use_case_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2196f3')),
        ]))
        elements.append(use_case_box)
        elements.append(Spacer(1, 0.4*cm))
    
    elements.append(PageBreak())
    
    # === QUICK WINS ===
    elements.append(Paragraph("QUICK WINS - SOFORT UMSETZBAR", section_heading))
    quick_wins = analysis.get('quick_wins', [])
    
    for i, win in enumerate(quick_wins, 1):
        if isinstance(win, dict):
            win_title = win.get('title', f'Quick Win {i}')
            win_desc = win.get('description', '')
            timeframe = win.get('timeframe', '')
            benefit = win.get('expected_benefit', '')
            
            win_content = f"""
            <b>🚀 {win_title}</b><br/>
            {win_desc}<br/>
            <b>Zeitrahmen:</b> {timeframe}<br/>
            <b>Erwarteter Nutzen:</b> {benefit}
            """
        else:
            win_content = f"<b>🚀 Quick Win {i}</b><br/>{win}"
        
        win_box = Table(
            [[Paragraph(win_content, body_style)]],
            colWidths=[16*cm]
        )
        win_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f3e5f5')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#9c27b0')),
        ]))
        elements.append(win_box)
        elements.append(Spacer(1, 0.4*cm))
    
    elements.append(PageBreak())
    
    # === STRATEGIC ROADMAP ===
    elements.append(Paragraph("STRATEGISCHE ROADMAP", section_heading))
    strategic_steps = analysis.get('strategic_steps', [])
    
    for i, step in enumerate(strategic_steps, 1):
        if isinstance(step, dict):
            phase = step.get('phase', f'Phase {i}')
            description = step.get('description', '')
            timeframe = step.get('timeframe', '')
            actions = step.get('key_actions', [])
            
            actions_text = '<br/>'.join([f"• {action}" for action in actions]) if actions else ''
            
            step_content = f"""
            <b>{phase}</b><br/>
            {description}<br/>
            <b>Zeitrahmen:</b> {timeframe}<br/>
            <b>Kernaktionen:</b><br/>
            {actions_text}
            """
        else:
            step_content = f"<b>Phase {i}</b><br/>{step}"
        
        step_box = Table(
            [[Paragraph(step_content, body_style)]],
            colWidths=[16*cm]
        )
        step_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#607d8b')),
        ]))
        elements.append(step_box)
        elements.append(Spacer(1, 0.4*cm))
    
    # === BUDGET & NEXT ACTIONS ===
    elements.append(Spacer(1, 0.5*cm))
    
    budget_rec = analysis.get('budget_recommendation', '')
    if budget_rec:
        elements.append(Paragraph("BUDGET-EMPFEHLUNG", subsection_heading))
        elements.append(Paragraph(budget_rec, highlight_style))
        elements.append(Spacer(1, 0.5*cm))
    
    next_actions = analysis.get('next_actions', [])
    if next_actions:
        elements.append(Paragraph("NÄCHSTE KONKRETE SCHRITTE", subsection_heading))
        for action in next_actions:
            elements.append(Paragraph(f"→ {action}", body_style))
        elements.append(Spacer(1, 0.5*cm))
    
    # === FOOTER ===
    elements.append(Spacer(1, 1*cm))
    
    footer_text = """
    <para alignment="center">
    <font size="9" color="#666666">
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>
    Dieser Bericht wurde automatisch generiert und dient als strategische Entscheidungsgrundlage.<br/>
    Für eine detaillierte Beratung und individuelle Unterstützung stehen wir Ihnen gerne zur Verfügung.<br/>
    © 2025 KI-Readiness Assessment | Vertraulich & Persönlich
    </font>
    </para>
    """
    elements.append(Paragraph(footer_text, body_style))
    
    # Build PDF
    doc.build(elements)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content