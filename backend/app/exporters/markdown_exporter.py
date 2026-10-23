import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone


def _clean_md_cell(val: Any) -> str:
    """Escape pipe characters and collapse newlines for Markdown table alignment."""
    if val is None:
        return ""
    return str(val).replace("|", "\\|").replace("\r\n", " ").replace("\n", " ").strip()


def _sanitize_url(url: Any) -> str:
    """Allow only safe web protocols (http, https) to prevent javascript: XSS in Markdown links."""
    if not url or not isinstance(url, str):
        return "#"
    clean = url.strip()
    if clean.lower().startswith(("http://", "https://")):
        return clean
    return "#"


class MarkdownExporter:
    """Exports entire startup package to structured, publication-ready Markdown (FR-10)."""

    def generate(self, run_id: str, state: Dict[str, Any]) -> str:
        """Render complete Markdown document from workflow state."""
        idea = state.get("idea", "Startup Idea")
        market = state.get("market") or {}
        prd = state.get("prd") or {}
        arch = state.get("architecture") or {}
        pitch = state.get("pitch") or {}
        scores = state.get("scores") or {}
        debate_log = state.get("debate_log") or []
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        md_lines = [
            f"# Startup Package: {idea}",
            f"\n**Run ID:** `{run_id}` | **Generated:** {created_at} | **Status:** {state.get('status', 'completed')}\n",
            "---\n",
            "## Table of Contents",
            "1. [Executive Summary & Scores](#1-executive-summary--scores)",
            "2. [Market Analysis](#2-market-analysis)",
            "3. [Product Requirements Document (PRD)](#3-product-requirements-document-prd)",
            "4. [Technical Architecture](#4-technical-architecture)",
            "5. [Pitch Deck (10-12 Slides)](#5-pitch-deck)",
            "6. [Peer Debate & Critique Transcript](#6-peer-debate--critique-transcript)",
            "\n---\n",
            "## 1. Executive Summary & Scores\n",
            "| Deliverable | Evaluation Score | Gate Status |",
            "|---|---|---|"
        ]

        for deliverable, score_list in scores.items():
            deliv_clean = _clean_md_cell(deliverable.capitalize())
            if score_list:
                latest_score = score_list[-1]
                gate_status = "PASS" if latest_score >= 7.0 else "NEEDS REVIEW"
                md_lines.append(f"| {deliv_clean} | {latest_score}/10 | {gate_status} |")
            else:
                md_lines.append(f"| {deliv_clean} | N/A | PENDING |")

        # 2. Market Analysis
        tam_src = _sanitize_url(market.get('tam', {}).get('source_url'))
        sam_src = _sanitize_url(market.get('sam', {}).get('source_url'))
        som_src = _sanitize_url(market.get('som', {}).get('source_url'))

        md_lines.extend([
            "\n---\n",
            "## 2. Market Analysis\n",
            f"- **Total Addressable Market (TAM):** {market.get('tam', {}).get('value', 'N/A')} *(Source: [{tam_src}]({tam_src}))*",
            f"- **Serviceable Addressable Market (SAM):** {market.get('sam', {}).get('value', 'N/A')} *(Source: [{sam_src}]({sam_src}))*",
            f"- **Serviceable Obtainable Market (SOM):** {market.get('som', {}).get('value', 'N/A')} *(Source: [{som_src}]({som_src}))*\n",
            "### Competitor Landscape\n",
            "| Competitor | Description | Strengths | Weaknesses |",
            "|---|---|---|---|"
        ])
        for comp in market.get("competitors", []):
            name = _clean_md_cell(comp.get("name", "N/A"))
            desc = _clean_md_cell(comp.get("description", "N/A"))
            strengths = _clean_md_cell(", ".join(comp.get("strengths", [])))
            weaknesses = _clean_md_cell(", ".join(comp.get("weaknesses", [])))
            md_lines.append(f"| {name} | {desc} | {strengths} | {weaknesses} |")

        md_lines.extend([
            "\n### Market Trends",
            *[f"- {trend}" for trend in market.get("trends", [])],
            "\n### Key Market Risks",
            *[f"- {risk}" for risk in market.get("risks", [])],
            "\n### Citations & Sources",
            *[f"- [{_sanitize_url(src)}]({_sanitize_url(src)})" for src in market.get("sources", [])]
        ])

        # 3. PRD
        md_lines.extend([
            "\n---\n",
            "## 3. Product Requirements Document (PRD)\n",
            f"### Core Problem Statement\n> {prd.get('problem_statement', 'N/A')}\n",
            f"### MVP Scope Boundary (<= 8 Weeks, 2 Devs)\n{prd.get('mvp_scope', 'N/A')}\n",
            "### User Personas\n"
        ])
        for p in prd.get("personas", []):
            md_lines.extend([
                f"#### Persona: {p.get('name', 'N/A')} ({p.get('role', 'N/A')})",
                "**Pain Points:**",
                *[f"- {pt}" for pt in p.get("pain_points", [])],
                "**Goals:**",
                *[f"- {g}" for g in p.get("goals", [])],
                ""
            ])

        md_lines.extend([
            "### Prioritized Feature Backlog (Max 8 P0)\n",
            "| Priority | Feature | Description |",
            "|---|---|---|"
        ])
        for f in prd.get("features", []):
            f_prio = _clean_md_cell(f.get("priority"))
            f_name = _clean_md_cell(f.get("name"))
            f_desc = _clean_md_cell(f.get("description", ""))
            md_lines.append(f"| **{f_prio}** | {f_name} | {f_desc} |")

        md_lines.extend([
            "\n### Core User Stories",
            *[f"- {story}" for story in prd.get("user_stories", [])],
            "\n### Success Metrics & KPIs",
            *[f"- {metric}" for metric in prd.get("success_metrics", [])]
        ])

        # 4. Architecture
        md_lines.extend([
            "\n---\n",
            "## 4. Technical Architecture\n",
            "### Technology Stack & Justifications\n",
            "| Category | Technology | Justification |",
            "|---|---|---|"
        ])
        for s in arch.get("stack", []):
            s_cat = _clean_md_cell(s.get("category"))
            s_tech = _clean_md_cell(s.get("technology"))
            s_just = _clean_md_cell(s.get("justification"))
            md_lines.append(f"| {s_cat} | **{s_tech}** | {s_just} |")

        md_lines.extend([
            "\n### System Architecture Diagram\n",
            "```mermaid",
            arch.get("diagram_mermaid", "flowchart TD\n    Client --> API --> DB"),
            "```\n",
            f"### Monthly Cloud Infrastructure Cost Estimate: ${arch.get('monthly_cost_estimate', {}).get('total_usd', 'N/A')}/mo\n",
            "| Item | Estimated Monthly Cost |",
            "|---|---|"
        ])
        for item, cost in arch.get("monthly_cost_estimate", {}).get("breakdown", {}).items():
            md_lines.append(f"| {item} | ${cost:.2f} |")

        md_lines.extend([
            f"\n### Scalability Pathway\n{arch.get('scalability_notes', 'N/A')}\n",
            "### Technical Risks",
            *[f"- {r}" for r in arch.get("risks", [])]
        ])

        # 5. Pitch Deck Slides
        md_lines.extend([
            "\n---\n",
            "## 5. Pitch Deck (10-12 Slides)\n"
        ])
        for slide in pitch.get("slides", []):
            s_num = slide.get("slide_number", "")
            title = slide.get("title", "")
            bullets = slide.get("bullets", [])
            notes = slide.get("speaker_notes", "")
            md_lines.extend([
                f"### Slide {s_num}: {title}\n",
                *[f"- {b}" for b in bullets],
                f"\n> **Speaker Notes:** {notes}\n"
            ])

        # 6. Debate Transcript
        md_lines.extend([
            "\n---\n",
            "## 6. Peer Debate & Critique Transcript\n"
        ])
        if debate_log:
            for entry in debate_log:
                r_num = entry.get("round", 1)
                from_a = entry.get("from_agent", "Agent")
                to_a = entry.get("to_agent", "Agent")
                m_type = entry.get("type", "message")
                content = entry.get("content", {})
                md_lines.extend([
                    f"#### Round {r_num}: {from_a} $\\rightarrow$ {to_a} ({m_type.upper()})\n",
                    f"```json\n{content if isinstance(content, str) else str(content)}\n```\n"
                ])
        else:
            md_lines.append("*No debate rounds recorded.*")

        return "\n".join(md_lines)

    def export_to_file(self, run_id: str, state: Dict[str, Any], output_path: str) -> str:
        """Write Markdown deliverable to disk."""
        content = self.generate(run_id, state)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path
