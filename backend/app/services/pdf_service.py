"""
Madhyastha — PDF Service
ReportLab-based PDF generation for agreements, awards, and briefs
"""
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("madhyastha.pdf")

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not installed. PDF generation disabled.")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "pdfs")


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_agreement_pdf(agreement_data: dict, filename: str = None) -> str:
    """Generate a mediation settlement agreement PDF"""
    ensure_output_dir()
    if not filename:
        filename = f"agreement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not REPORTLAB_AVAILABLE:
        # Create a placeholder file
        with open(filepath, "w") as f:
            f.write("PDF generation requires ReportLab. Install with: pip install reportlab")
        return filepath

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                           leftMargin=1.5*cm, rightMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'],
                                  fontSize=18, textColor=HexColor('#1a365d'),
                                  spaceAfter=20)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'],
                                    fontSize=13, textColor=HexColor('#2d3748'),
                                    spaceBefore=15, spaceAfter=8)
    body_style = ParagraphStyle('CustomBody', parent=styles['Normal'],
                                 fontSize=11, leading=16, alignment=TA_JUSTIFY)
    citation_style = ParagraphStyle('Citation', parent=styles['Normal'],
                                     fontSize=10, textColor=HexColor('#4a5568'),
                                     italic=True, alignment=TA_CENTER, spaceBefore=20)

    elements = []
    elements.append(Paragraph("MADHYASTHA", ParagraphStyle('Brand', parent=styles['Normal'],
                    fontSize=10, textColor=HexColor('#667eea'), alignment=TA_CENTER)))
    elements.append(Spacer(1, 5))
    elements.append(Paragraph(agreement_data.get("title", "Mediation Settlement Agreement"), title_style))
    elements.append(Paragraph(f"Reference: {agreement_data.get('reference_number', 'N/A')} | Date: {agreement_data.get('date', 'N/A')}", citation_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#667eea')))
    elements.append(Spacer(1, 15))

    for section in agreement_data.get("sections", []):
        elements.append(Paragraph(section.get("heading", ""), heading_style))
        content = section.get("content", "").replace("\n", "<br/>")
        elements.append(Paragraph(content, body_style))
        elements.append(Spacer(1, 8))

    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#667eea')))
    note = agreement_data.get("enforcement_note", "")
    if note:
        elements.append(Paragraph(note, citation_style))

    doc.build(elements)
    logger.info(f"Agreement PDF generated: {filepath}")
    return filepath


def generate_award_pdf(award_data: dict, filename: str = None) -> str:
    """Generate an arbitration award PDF"""
    ensure_output_dir()
    if not filename:
        filename = f"award_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not REPORTLAB_AVAILABLE:
        with open(filepath, "w") as f:
            f.write("PDF generation requires ReportLab.")
        return filepath

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                           leftMargin=1.5*cm, rightMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('AwardTitle', parent=styles['Title'],
                                  fontSize=18, textColor=HexColor('#742a2a'))
    heading_style = ParagraphStyle('AwardHeading', parent=styles['Heading2'],
                                    fontSize=13, textColor=HexColor('#2d3748'))
    body_style = ParagraphStyle('AwardBody', parent=styles['Normal'],
                                 fontSize=11, leading=16, alignment=TA_JUSTIFY)

    elements.append(Paragraph("MADHYASTHA — ARBITRATION AWARD", title_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=2, color=HexColor('#742a2a')))
    elements.append(Spacer(1, 15))

    for key, val in award_data.items():
        if key in ("award_type", "amount", "currency", "payment_timeline_days",
                   "installments", "enforcement_clause", "reasoning"):
            label = key.replace("_", " ").title()
            elements.append(Paragraph(f"<b>{label}:</b> {val}", body_style))
            elements.append(Spacer(1, 5))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "<i>This award is issued under Section 31 of the Arbitration and Conciliation Act, 1996, "
        "and is enforceable as a decree of court under Section 36.</i>",
        ParagraphStyle('LegalNote', parent=styles['Normal'], fontSize=10,
                       textColor=HexColor('#4a5568'), alignment=TA_CENTER)))

    doc.build(elements)
    logger.info(f"Award PDF generated: {filepath}")
    return filepath


def generate_brief_pdf(brief_data: dict, filename: str = None) -> str:
    """Generate an arbitration brief PDF"""
    ensure_output_dir()
    if not filename:
        filename = f"brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not REPORTLAB_AVAILABLE:
        with open(filepath, "w") as f:
            f.write("PDF generation requires ReportLab.")
        return filepath

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                           leftMargin=1.5*cm, rightMargin=1.5*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('BriefTitle', parent=styles['Title'],
                                  fontSize=16, textColor=HexColor('#1a365d'))
    heading_style = ParagraphStyle('BriefHeading', parent=styles['Heading2'],
                                    fontSize=12, textColor=HexColor('#2d3748'))
    body_style = ParagraphStyle('BriefBody', parent=styles['Normal'],
                                 fontSize=10, leading=14, alignment=TA_JUSTIFY)

    elements.append(Paragraph("MADHYASTHA — ARBITRATION BRIEF", title_style))
    elements.append(Paragraph(f"Case: {brief_data.get('case_id', 'N/A')} | Date: {brief_data.get('prepared_date', 'N/A')}",
                    ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#1a365d')))
    elements.append(Spacer(1, 10))

    for section in brief_data.get("sections", []):
        elements.append(Paragraph(f"{section.get('number', '')}. {section.get('heading', '')}", heading_style))
        content = section.get("content", "").replace("\n", "<br/>")
        elements.append(Paragraph(content, body_style))
        elements.append(Spacer(1, 8))

    doc.build(elements)
    logger.info(f"Brief PDF generated: {filepath}")
    return filepath


def generate_petition_pdf(dispute_data: dict, filename: str = None) -> str:
    """Generate a pre-filled court petition PDF"""
    ensure_output_dir()
    if not filename:
        filename = f"petition_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not REPORTLAB_AVAILABLE:
        with open(filepath, "w") as f:
            f.write("PDF generation requires ReportLab.")
        return filepath

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph("IN THE COURT OF CIVIL JUDGE", styles['Title']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Case: {dispute_data.get('title', 'N/A')}", styles['Heading2']))
    elements.append(Paragraph(f"Type: {dispute_data.get('dispute_type', 'Civil')}", styles['Normal']))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("PETITION FOR ENFORCEMENT", styles['Heading2']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        "The petitioner respectfully submits that AI-mediated settlement and binding arbitration "
        "were attempted through the Madhyastha platform. The respondent has failed to comply "
        "with the arbitration award. This petition seeks enforcement under Section 36 of the "
        "Arbitration and Conciliation Act, 1996.", styles['Normal']))
    doc.build(elements)
    logger.info(f"Petition PDF generated: {filepath}")
    return filepath
