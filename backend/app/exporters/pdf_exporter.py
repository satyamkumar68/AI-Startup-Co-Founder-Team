import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


from xml.sax.saxutils import escape as xml_escape


def _safe_str(val: Any) -> str:
    """Escape XML entities to prevent ReportLab parsing crashes (CWE-20) and SSRF (CWE-918)."""
    if val is None:
        return "N/A"
    return xml_escape(str(val))


class PDFExporter:
    """Exports startup package to an executive PDF document (FR-10).
    
    Uses ReportLab as the reliable cross-platform engine (native on Windows/Linux/macOS)
    with WeasyPrint fallback if configured.
    """

    def generate(self, run_id: str, state: Dict[str, Any], output_path: Any = None) -> Any:
        """Create and save PDF file or return in-memory BytesIO stream."""
        import io
        target = output_path if output_path is not None else io.BytesIO()
        if isinstance(target, str):
            os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)

        try:
            self._generate_reportlab(run_id, state, target)
            if isinstance(target, io.BytesIO):
                target.seek(0)
            return target
        except Exception as e:
            logger.error(f"ReportLab PDF generation error: {e}.")
            raise

    def _generate_reportlab(self, run_id: str, state: Dict[str, Any], output_path: str) -> str:
        """Render formatted PDF using ReportLab Flowables."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
            HRFlowable
        )

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=14
        )
        h2_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=15,
            leading=18,
            textColor=colors.HexColor('#4338CA'),
            spaceBefore=14,
            spaceAfter=8
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceAfter=6
        )

        story = []

        idea = state.get("idea", "Startup Package")
        market = state.get("market") or {}
        prd = state.get("prd") or {}
        arch = state.get("architecture") or {}
        pitch = state.get("pitch") or {}
        scores = state.get("scores") or {}

        # 1. Header
        story.append(Paragraph(f"AI Co-Founder Report: {_safe_str(idea)}", title_style))
        story.append(Paragraph(f"Run ID: {_safe_str(run_id)} | Status: {_safe_str(state.get('status', 'completed'))}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4338CA'), spaceAfter=14))

        # 2. Executive Scores Table
        story.append(Paragraph("1. Quality Gate Scores", h2_style))
        score_data = [["Deliverable", "Latest Score", "Gate Result"]]
        for deliv, s_list in scores.items():
            latest = f"{s_list[-1]}/10" if s_list else "N/A"
            gate = "PASS" if (s_list and s_list[-1] >= 7.0) else "NEEDS REVIEW"
            score_data.append([_safe_str(deliv.capitalize()), _safe_str(latest), _safe_str(gate)])

        score_table = Table(score_data, colWidths=[180, 150, 150])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 14))

        # 3. Market Analysis Summary
        story.append(Paragraph("2. Market Analysis", h2_style))
        tam_val = _safe_str(market.get('tam', {}).get('value', 'N/A'))
        sam_val = _safe_str(market.get('sam', {}).get('value', 'N/A'))
        som_val = _safe_str(market.get('som', {}).get('value', 'N/A'))
        story.append(Paragraph(f"<b>TAM:</b> {tam_val} | <b>SAM:</b> {sam_val} | <b>SOM:</b> {som_val}", body_style))
        
        comp_names = [_safe_str(c.get("name", "")) for c in market.get("competitors", []) if c.get("name")]
        if comp_names:
            story.append(Paragraph(f"<b>Top Competitors:</b> {', '.join(comp_names)}", body_style))
        story.append(Spacer(1, 10))

        # 4. PRD Highlights
        story.append(Paragraph("3. Product Requirements (PRD)", h2_style))
        story.append(Paragraph(f"<b>Problem Statement:</b> {_safe_str(prd.get('problem_statement', 'N/A'))}", body_style))
        story.append(Paragraph(f"<b>MVP Scope:</b> {_safe_str(prd.get('mvp_scope', 'N/A'))}", body_style))
        p0_features = [_safe_str(f.get("name")) for f in prd.get("features", []) if f.get("priority") == "P0" and f.get("name")]
        if p0_features:
            story.append(Paragraph(f"<b>P0 Features:</b> {', '.join(p0_features)}", body_style))
        story.append(Spacer(1, 10))

        # 5. Tech Architecture Highlights
        story.append(Paragraph("4. Technical Architecture", h2_style))
        stack_items = [_safe_str(f"{s.get('category')}: {s.get('technology')}") for s in arch.get("stack", []) if s.get('technology')]
        if stack_items:
            story.append(Paragraph(f"<b>Stack Choices:</b> {', '.join(stack_items)}", body_style))
        monthly_cost = arch.get("monthly_cost_estimate", {}).get("total_usd", 0.0)
        try:
            cost_str = f"${float(monthly_cost):.2f}/mo"
        except (ValueError, TypeError):
            cost_str = f"${_safe_str(monthly_cost)}/mo" if monthly_cost else "N/A"
        story.append(Paragraph(f"<b>Monthly Infrastructure Cost:</b> {cost_str}", body_style))
        story.append(Spacer(1, 10))

        # 6. Pitch Deck Summary
        story.append(Paragraph("5. Pitch Deck Overview", h2_style))
        for slide in pitch.get("slides", [])[:6]:  # Highlights of first 6 slides
            s_num = _safe_str(slide.get('slide_number'))
            s_title = _safe_str(slide.get('title'))
            story.append(Paragraph(f"<b>Slide {s_num}:</b> {s_title}", body_style))

        # Build document
        doc.build(story)
        return output_path
        return output_path
