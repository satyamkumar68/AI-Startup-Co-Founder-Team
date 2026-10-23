import io
import csv
from typing import Dict, Any, Optional


def sanitize_csv_cell(value: Any) -> Any:
    """Neutralize spreadsheet formula injection (CWE-1236 / OWASP).
    
    Prepends a single quote to strings starting with formula trigger characters
    ('=', '+', '-', '@', '\t', '\r') so spreadsheet software treats them strictly as text.
    Numeric types (int, float) and booleans are preserved.
    """
    if value is None:
        return ""
    if isinstance(value, (int, float, bool)):
        return value
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


class CSVExporter:
    """Exports startup venture package to structured tabular CSV."""

    def generate(self, run_id: str, state: Dict[str, Any], output_path: Optional[str] = None) -> Any:
        """Render complete CSV document from workflow state.
        
        If output_path is provided, writes to disk and returns path.
        Otherwise, returns io.BytesIO buffer positioned at start.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        def write_safe_row(cells: list) -> None:
            writer.writerow([sanitize_csv_cell(c) for c in cells])

        idea = state.get("idea", "Startup Package")
        status = state.get("status", "completed")
        market = state.get("market") or {}
        prd = state.get("prd") or {}
        arch = state.get("architecture") or {}
        pitch = state.get("pitch") or {}
        scores = state.get("scores") or {}

        # ----------------------------------------------------------------------
        # Header / Metadata
        # ----------------------------------------------------------------------
        write_safe_row(["=== VENTURE SUMMARY & METADATA ==="])
        write_safe_row(["Run ID", run_id])
        write_safe_row(["Startup Idea", idea])
        write_safe_row(["Status", status])
        writer.writerow([])

        # ----------------------------------------------------------------------
        # 1. Quality Gate Scores
        # ----------------------------------------------------------------------
        write_safe_row(["=== 1. QUALITY GATE EVALUATIONS ==="])
        write_safe_row(["Deliverable", "Latest Score", "Max Score", "Gate Result"])
        for deliv, s_list in scores.items():
            latest = s_list[-1] if s_list else "N/A"
            gate = "PASS" if (s_list and s_list[-1] >= 7.0) else "NEEDS REVIEW"
            write_safe_row([deliv.capitalize(), latest, "10", gate])
        writer.writerow([])

        # ----------------------------------------------------------------------
        # 2. Market Sizing
        # ----------------------------------------------------------------------
        write_safe_row(["=== 2. MARKET SIZING (TAM / SAM / SOM) ==="])
        write_safe_row(["Metric", "Estimated Value", "Unit", "Citation Source URL"])
        for metric_key, label in [("tam", "Total Addressable Market (TAM)"),
                                  ("sam", "Serviceable Addressable Market (SAM)"),
                                  ("som", "Serviceable Obtainable Market (SOM)")]:
            m_data = market.get(metric_key, {})
            val = m_data.get("value", "N/A")
            unit = m_data.get("unit", "USD")
            src = m_data.get("source_url", "N/A")
            write_safe_row([label, val, unit, src])
        writer.writerow([])

        # ----------------------------------------------------------------------
        # 3. Competitor Intelligence
        # ----------------------------------------------------------------------
        write_safe_row(["=== 3. COMPETITOR INTELLIGENCE MATRIX ==="])
        write_safe_row(["Competitor Name", "Description", "Key Strengths", "Key Weaknesses"])
        for comp in market.get("competitors", []):
            name = comp.get("name", "N/A")
            desc = comp.get("description", "N/A")
            strengths = " | ".join(comp.get("strengths", []))
            weaknesses = " | ".join(comp.get("weaknesses", []))
            write_safe_row([name, desc, strengths, weaknesses])
        writer.writerow([])

        # ----------------------------------------------------------------------
        # 4. Product Requirements (PRD) Feature Backlog
        # ----------------------------------------------------------------------
        write_safe_row(["=== 4. PRODUCT FEATURE BACKLOG (PRD) ==="])
        write_safe_row(["Priority", "Feature Name", "Description"])
        for feat in prd.get("features", []):
            write_safe_row([
                feat.get("priority", "P0"),
                feat.get("name", "N/A"),
                feat.get("description", "")
            ])
        writer.writerow([])

        # ----------------------------------------------------------------------
        # 5. User Stories & Acceptance
        # ----------------------------------------------------------------------
        write_safe_row(["=== 5. USER STORIES & SUCCESS METRICS ==="])
        write_safe_row(["Type", "Detail"])
        for story in prd.get("user_stories", []):
            write_safe_row(["User Story", story])
        for metric in prd.get("success_metrics", []):
            write_safe_row(["KPI / Metric", metric])
        writer.writerow([])

        # ----------------------------------------------------------------------
        # 6. Tech Architecture Stack
        # ----------------------------------------------------------------------
        write_safe_row(["=== 6. TECHNICAL ARCHITECTURE STACK ==="])
        write_safe_row(["Category", "Technology", "Architectural Justification"])
        for s in arch.get("stack", []):
            write_safe_row([
                s.get("category", "General"),
                s.get("technology", "N/A"),
                s.get("justification", "")
            ])
        writer.writerow([])

        # ----------------------------------------------------------------------
        # 7. Monthly Cloud Infrastructure Cost Breakdown
        # ----------------------------------------------------------------------
        write_safe_row(["=== 7. CLOUD INFRASTRUCTURE RUN RATE ==="])
        write_safe_row(["Component", "Estimated Monthly Cost (USD)"])
        cost_est = arch.get("monthly_cost_estimate", {})
        for item, cost in cost_est.get("breakdown", {}).items():
            write_safe_row([item, f"${cost:.2f}" if isinstance(cost, (int, float)) else str(cost)])
        total_usd = cost_est.get("total_usd", 0.0)
        write_safe_row(["TOTAL MONTHLY RUN RATE", f"${total_usd:.2f}" if isinstance(total_usd, (int, float)) else str(total_usd)])
        writer.writerow([])

        # ----------------------------------------------------------------------
        # 8. Pitch Deck Slide Inventory
        # ----------------------------------------------------------------------
        write_safe_row(["=== 8. PITCH DECK SLIDES (10-12 SLIDES) ==="])
        write_safe_row(["Slide Number", "Title", "Body Bullets", "Speaker Notes"])
        for slide in pitch.get("slides", []):
            write_safe_row([
                slide.get("slide_number", ""),
                slide.get("title", ""),
                " \n".join(slide.get("bullets", [])),
                slide.get("speaker_notes", "")
            ])

        csv_content = output.getvalue()
        output.close()

        if output_path:
            import os
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
                f.write(csv_content)
            return output_path

        # Return in-memory BytesIO encoded in UTF-8 with BOM for Excel compatibility
        bytes_io = io.BytesIO(csv_content.encode("utf-8-sig"))
        bytes_io.seek(0)
        return bytes_io
