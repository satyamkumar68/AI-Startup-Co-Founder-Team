import os
import io
from typing import Dict, Any, List, Union
from backend.app.exporters.markdown_exporter import MarkdownExporter
from backend.app.exporters.pptx_exporter import PPTXExporter
from backend.app.exporters.pdf_exporter import PDFExporter
from backend.app.exporters.csv_exporter import CSVExporter
from backend.app.core.config import settings


class ExportManager:
    """Coordinates multi-format document exporting (PDF, PPTX, Markdown, CSV)."""

    def __init__(self, exports_dir: str = settings.EXPORTS_DIR):
        self.exports_dir = exports_dir
        self.md_exporter = MarkdownExporter()
        self.pptx_exporter = PPTXExporter()
        self.pdf_exporter = PDFExporter()
        self.csv_exporter = CSVExporter()

    def export_in_memory(self, run_id: str, state: Dict[str, Any], file_format: str) -> io.BytesIO:
        """Export state deliverables directly to an in-memory BytesIO buffer (no disk writes)."""
        fmt = file_format.lower()
        if fmt in ["csv"]:
            return self.csv_exporter.generate(run_id, state, output_path=None)
        elif fmt in ["md", "markdown"]:
            md_str = self.md_exporter.generate(run_id, state)
            buf = io.BytesIO(md_str.encode("utf-8"))
            buf.seek(0)
            return buf
        elif fmt in ["pptx"]:
            return self.pptx_exporter.generate(run_id, state, output_path=None)
        elif fmt in ["pdf"]:
            return self.pdf_exporter.generate(run_id, state, output_path=None)
        else:
            raise ValueError(f"Unsupported export format: {file_format}")

    def export(self, run_id: str, state: Dict[str, Any], file_format: str = "all") -> Dict[str, str]:
        """Export state deliverables to requested format ('pdf', 'pptx', 'md', 'csv', or 'all').
        
        Returns:
            Dictionary mapping format name to generated file path.
        """
        import re
        if ".." in run_id or "/" in run_id or "\\" in run_id:
            raise ValueError(f"Path traversal detected for run_id: {run_id}")

        safe_run_id = re.sub(r"[^a-zA-Z0-9_\-]", "", run_id)
        if not safe_run_id:
            raise ValueError(f"Invalid run_id for export: {run_id}")

        base_dir = os.path.abspath(self.exports_dir)
        run_export_dir = os.path.abspath(os.path.join(base_dir, safe_run_id))
        if not run_export_dir.startswith(base_dir):
            raise ValueError(f"Path traversal detected for run_id: {run_id}")

        os.makedirs(run_export_dir, exist_ok=True)
        results: Dict[str, str] = {}

        fmt = file_format.lower()

        if fmt in ["md", "markdown", "all"]:
            md_path = os.path.join(run_export_dir, f"{safe_run_id}_report.md")
            self.md_exporter.export_to_file(safe_run_id, state, md_path)
            results["md"] = md_path

        if fmt in ["pptx", "all"]:
            pptx_path = os.path.join(run_export_dir, f"{safe_run_id}_pitch.pptx")
            self.pptx_exporter.generate(safe_run_id, state, pptx_path)
            results["pptx"] = pptx_path

        if fmt in ["pdf", "all"]:
            pdf_path = os.path.join(run_export_dir, f"{safe_run_id}_report.pdf")
            self.pdf_exporter.generate(safe_run_id, state, pdf_path)
            results["pdf"] = pdf_path

        if fmt in ["csv", "all"]:
            csv_path = os.path.join(run_export_dir, f"{safe_run_id}_data.csv")
            self.csv_exporter.generate(safe_run_id, state, csv_path)
            results["csv"] = csv_path

        return results
