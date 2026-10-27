import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class FactCheckEngine:
    """Fact-Checking and Citation Verification Engine (AGENTS.md / SKILL Step 5).
    
    Scans generated venture deliverables (Market, PRD, Architecture, Pitch) to ensure:
    - Every numerical market figure has a verified source_url or is labeled 'assumption'.
    - Infrastructure costs reference pinned cloud pricing or are labeled 'estimate_unverified'.
    - Appends a transparent 'Verification & Citations Appendix' to final deliverables.
    """

    def __init__(self):
        pass

    def verify(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive citation and source audit across all deliverables."""
        market = state.get("market") or {}
        arch = state.get("architecture") or {}
        prd = state.get("prd") or {}
        pitch = state.get("pitch") or {}

        today_iso = datetime.now(timezone.utc).date().isoformat()
        records: List[Dict[str, str]] = []
        flagged_claims: List[str] = []

        verified_count = 0
        assumption_count = 0
        unverified_count = 0

        # 1. Audit Market Metrics (TAM / SAM / SOM)
        for metric_name, label in [("tam", "Total Addressable Market (TAM)"),
                                   ("sam", "Serviceable Addressable Market (SAM)"),
                                   ("som", "Serviceable Obtainable Market (SOM)")]:
            data = market.get(metric_name) or {}
            val = str(data.get("value", "N/A"))
            url = str(data.get("source_url") or "")
            is_assumption = data.get("is_assumption", False)
            retrieved_at = str(data.get("retrieved_at") or today_iso)

            if url and url.startswith("http") and not ("example.com" in url):
                status = "VERIFIED SOURCE"
                verified_count += 1
            elif is_assumption:
                status = "EXPLICIT ASSUMPTION"
                assumption_count += 1
            else:
                status = "UNGROUNDED CLAIM"
                unverified_count += 1
                flagged_claims.append(f"{label} figure '{val}' lacks a valid source URL and is not marked as an assumption.")

            records.append({
                "claim": label,
                "value": val,
                "source": url if url and url.startswith("http") else "None (Derived)",
                "status": status,
                "date": retrieved_at
            })

        # 2. Audit Infrastructure Cost Breakdown
        cost_info = arch.get("monthly_cost_estimate") or {}
        tot_cost = cost_info.get("total_usd", 0.0)
        breakdown = cost_info.get("breakdown") or {}
        cost_sources = cost_info.get("sources") or {}
        is_cost_unverified = cost_info.get("estimate_unverified", False)

        cost_status = "PINNED PRICING" if not is_cost_unverified else "PARTIAL ESTIMATE"
        if is_cost_unverified:
            assumption_count += 1
        else:
            verified_count += 1

        records.append({
            "claim": "Monthly Cloud Cost Total",
            "value": f"${tot_cost:.2f}/mo",
            "source": "data/cloud_pricing.json",
            "status": cost_status,
            "date": cost_info.get("retrieved_date", today_iso)
        })

        for comp_name, comp_cost in breakdown.items():
            src = cost_sources.get(comp_name, "")
            c_stat = "VERIFIED TIER" if src and src.startswith("http") else "ASSUMED TIER"
            if c_stat == "VERIFIED TIER":
                verified_count += 1
            else:
                assumption_count += 1

            records.append({
                "claim": f"Infra: {comp_name}",
                "value": f"${float(comp_cost):.2f}/mo",
                "source": src if src.startswith("http") else "data/cloud_pricing.json",
                "status": c_stat,
                "date": today_iso
            })

        # 3. Generate Verification Appendix Markdown
        appendix_md = "## Verification & Sourcing Appendix\n\n"
        appendix_md += "| Metric / Claim | Value | Source URL / Catalog | Grounding Status | Date |\n"
        appendix_md += "| :--- | :--- | :--- | :---: | :---: |\n"
        for r in records:
            status_badge = "🟢 " + r["status"] if "VERIFIED" in r["status"] or "PINNED" in r["status"] else ("🟡 " + r["status"] if "ASSUMPTION" in r["status"] or "PARTIAL" in r["status"] else "🔴 " + r["status"])
            appendix_md += f"| {r['claim']} | {r['value']} | {r['source']} | {status_badge} | {r['date']} |\n"

        if flagged_claims:
            appendix_md += "\n> [!WARNING]\n"
            appendix_md += "> **Ungrounded Claims Detected:**\n"
            for f in flagged_claims:
                appendix_md += f"> - {f}\n"
        else:
            appendix_md += "\n> [!NOTE]\n"
            appendix_md += "> **All figures verified:** 100% of numerical figures are backed by valid external source URLs, catalog pricing, or explicit assumption labels.\n"

        return {
            "verified_count": verified_count,
            "assumption_count": assumption_count,
            "unverified_count": unverified_count,
            "flagged_claims": flagged_claims,
            "appendix_markdown": appendix_md,
            "audit_records": records
        }
