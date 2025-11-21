from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, 
                                Spacer, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from io import BytesIO
from datetime import datetime

def generate_assessment_pdf(assessment_data: dict) -> bytes:
    """
    Generate KI-Fit Assessment PDF with new structure
    """
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm,
        title=f"KI-Fit Result - {assessment_data.get('profile_name', 'Assessment')}"
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # === CUSTOM STYLES ===
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=26,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=30
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0f3460'),
        spaceAfter=12,
        spaceBefore=20,
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
    
    score_label_style = ParagraphStyle(
        'ScoreLabel',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_LEFT
    )
    
    # === 1. HEADLINE ===
    elements.append(Spacer(1, 1*cm))
    profile_name = assessment_data.get('profile_name', 'Ihre KI-Readiness')
    headline = f"Your KI-Fit Result: {profile_name}"
    elements.append(Paragraph(headline, title_style))
    elements.append(Spacer(1, 0.8*cm))
    
    # === 2. SUMMARY ===
    summary = assessment_data.get('profile_summary', 
        'Ihre KI-Readiness wurde erfolgreich bewertet. Diese Analyse zeigt Ihre aktuelle Position '
        'in Bezug auf digitale Transformation und KI-Integration. Basierend auf Ihren Antworten '
        'haben wir spezifische Empfehlungen und Handlungsschritte für Sie zusammengestellt.')
    
    summary_box = Table(
        [[Paragraph(summary, body_style)]],
        colWidths=[16*cm]
    )
    summary_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f4f8')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#0f3460')),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(summary_box)
    elements.append(Spacer(1, 0.8*cm))
    
    # === 3. SCORE OVERVIEW ===
    elements.append(Paragraph("Score Overview (0-100)", section_heading))
    
    # Get all scores
    scores = {
        'Digitalization Score': assessment_data.get('digitalization_score', 0),
        'Bottleneck Score': assessment_data.get('bottleneck_score', 0),
        'Automation Potential': assessment_data.get('automation_potential', 0),
        'Mindset Score': assessment_data.get('mindset_score', 0),
        'Investment Score': assessment_data.get('investment_score', 0),
        'Execution Capacity': assessment_data.get('execution_capacity', 0),
        'Urgency Score': assessment_data.get('urgency_score', 0)
    }
    
    # Create score bars
    for score_name, score_value in scores.items():
        # Determine color based on score
        if score_value >= 70:
            bar_color = colors.HexColor('#28a745')
        elif score_value >= 40:
            bar_color = colors.HexColor('#ffc107')
        else:
            bar_color = colors.HexColor('#dc3545')
        
        # Score bar visualization
        bar_width = (score_value / 100) * 12  # Max 12cm
        
        score_row = [
            [Paragraph(f"<b>{score_name}</b>", score_label_style),
             f"{score_value}"]
        ]
        
        score_table = Table(score_row, colWidths=[10*cm, 2*cm])
        score_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (1, 0), 12),
            ('TEXTCOLOR', (1, 0), (1, 0), bar_color),
        ]))
        elements.append(score_table)
        
        # Progress bar
        bar_data = [['']]
        bar_table = Table(bar_data, colWidths=[bar_width*cm], rowHeights=[0.6*cm])
        bar_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bar_color),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(bar_table)
        elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # === 4. TOP 3 QUICK WINS ===
    elements.append(Paragraph("Top 3 Quick Wins", section_heading))
    
    quick_wins = assessment_data.get('quick_wins', [
        'Implementierung einfacher Automatisierungstools',
        'Digitalisierung manueller Prozesse',
        'Einführung einer Cloud-basierten Lösung'
    ])
    
    for i, win in enumerate(quick_wins[:3], 1):
        if isinstance(win, dict):
            win_text = f"<b>{i}. {win.get('title', '')}</b><br/>{win.get('description', '')}"
        else:
            win_text = f"<b>{i}.</b> {win}"
        
        win_box = Table(
            [[Paragraph(win_text, body_style)]],
            colWidths=[16*cm]
        )
        win_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8f5e9')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#4caf50')),
        ]))
        elements.append(win_box)
        elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # === 5. TOP 3 AI AUTOMATION OPPORTUNITIES ===
    elements.append(Paragraph("Top 3 AI Automation Opportunities", section_heading))
    
    ai_opportunities = assessment_data.get('ai_opportunities', [
        'Automatisierte Kundenkommunikation mit Chatbots',
        'Prozessoptimierung durch KI-gestützte Analyse',
        'Predictive Analytics für bessere Entscheidungsfindung'
    ])
    
    for i, opportunity in enumerate(ai_opportunities[:3], 1):
        if isinstance(opportunity, dict):
            opp_text = f"<b>{i}. {opportunity.get('title', '')}</b><br/>{opportunity.get('description', '')}"
        else:
            opp_text = f"<b>{i}.</b> {opportunity}"
        
        opp_box = Table(
            [[Paragraph(opp_text, body_style)]],
            colWidths=[16*cm]
        )
        opp_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e3f2fd')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2196f3')),
        ]))
        elements.append(opp_box)
        elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Spacer(1, 0.5*cm))
    
    # === 6. USER'S BOTTLENECK (Q15) ===
    elements.append(Paragraph("Your Biggest Bottleneck", section_heading))
    
    bottleneck_text = assessment_data.get('q15_bottleneck', 
        'Keine spezifischen Engpässe angegeben.')
    
    bottleneck_box = Table(
        [[Paragraph(f"<i>\"{bottleneck_text}\"</i>", body_style)]],
        colWidths=[16*cm]
    )
    bottleneck_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff3e0')),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#ff9800')),
    ]))
    elements.append(bottleneck_box)
    elements.append(Spacer(1, 0.8*cm))
    
    # === 7. CTA SECTION - KI-KOMPASS RECOMMENDATION ===
    elements.append(Paragraph("Empfehlung: KI-Kompass", section_heading))
    
    # Determine recommendation strength
    ki_kompass_strength = assessment_data.get('ki_kompass_recommendation', 'Medium')
    
    if ki_kompass_strength == 'Strong':
        cta_color = colors.HexColor('#28a745')
        cta_text = """
        <b>Stark empfohlen!</b><br/><br/>
        Basierend auf Ihrer Bewertung empfehlen wir Ihnen dringend, den KI-Kompass zu nutzen. 
        Ihr Unternehmen hat großes Potenzial für KI-Integration und würde erheblich von einer 
        strukturierten Herangehensweise profitieren. Der KI-Kompass wird Ihnen helfen, Ihre 
        KI-Strategie zu entwickeln und schnell umsetzbare Ergebnisse zu erzielen.
        """
    elif ki_kompass_strength == 'Soft':
        cta_color = colors.HexColor('#17a2b8')
        cta_text = """
        <b>Zur Überlegung empfohlen</b><br/><br/>
        Der KI-Kompass könnte für Ihr Unternehmen interessant sein. Ihre aktuelle Situation 
        zeigt einige Bereiche, in denen KI-Unterstützung hilfreich sein könnte. Wir empfehlen, 
        sich über die Möglichkeiten zu informieren und zu prüfen, ob der KI-Kompass zu Ihren 
        aktuellen Zielen passt.
        """
    else:  # Medium
        cta_color = colors.HexColor('#ffc107')
        cta_text = """
        <b>Empfohlen</b><br/><br/>
        Der KI-Kompass ist für Ihr Unternehmen eine gute Wahl. Ihre Bewertung zeigt, dass Sie 
        von einer strukturierten KI-Implementierung profitieren würden. Der KI-Kompass bietet 
        Ihnen die nötigen Tools und Strategien, um Ihre digitale Transformation erfolgreich 
        voranzutreiben.
        """
    
    cta_box = Table(
        [[Paragraph(cta_text, body_style)]],
        colWidths=[16*cm]
    )
    cta_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ('BOX', (0, 0), (-1, -1), 3, cta_color),
    ]))
    elements.append(cta_box)
    
    # === FOOTER ===
    elements.append(Spacer(1, 1.5*cm))
    
    footer_text = f"""
    <para alignment="center">
    <font size="9" color="#666666">
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━<br/>
    Erstellt am: {datetime.now().strftime('%d. %B %Y')}<br/>
    Dieser Bericht wurde automatisch generiert und dient als strategische Entscheidungsgrundlage.<br/>
    © 2025 KI-Fit Assessment | Vertraulich & Persönlich
    </font>
    </para>
    """
    elements.append(Paragraph(footer_text, body_style))
    
    # Build PDF
    doc.build(elements)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


# Example usage
if __name__ == "__main__":
    sample_data = {
        'profile_name': 'Digitaler Vorreiter',
        'profile_summary': 'Ihr Unternehmen zeigt eine hohe Bereitschaft für KI-Integration mit starkem digitalem Fundament.',
        'digitalization_score': 75,
        'bottleneck_score': 60,
        'automation_potential': 85,
        'mindset_score': 80,
        'investment_score': 65,
        'execution_capacity': 70,
        'urgency_score': 75,
        'quick_wins': [
            'Implementierung von CRM-Automatisierung',
            'KI-gestützte E-Mail-Kampagnen',
            'Chatbot für Kundenservice'
        ],
        'ai_opportunities': [
            'Predictive Analytics für Vertrieb',
            'Automatisierte Dokumentenverarbeitung',
            'KI-basierte Personalisierung'
        ],
        'q15_bottleneck': 'Zeitmangel bei der Implementierung neuer Technologien und fehlendes technisches Know-how im Team.',
        'ki_kompass_recommendation': 'Strong'
    }
    
    pdf_bytes = generate_assessment_pdf(sample_data)
    
    with open('ki_fit_assessment.pdf', 'wb') as f:
        f.write(pdf_bytes)