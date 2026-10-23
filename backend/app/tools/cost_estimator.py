from typing import List, Dict, Any


class CostEstimatorTool:
    """Cloud infrastructure cost estimator tool for MVP architectures.
    
    Provides standardized cost calculations across managed services (AWS, Render,
    Supabase, Neon, Upstash, Redis Cloud) for predictable budgeting (ADR-004, REQUIREMENTS.md).
    """

    DEFAULT_BENCHMARKS = {
        "web_service": {"name": "Managed Web Service (e.g., Render/Railway)", "cost": 15.0},
        "background_worker": {"name": "Background Worker Instance", "cost": 15.0},
        "database": {"name": "Managed PostgreSQL (Neon / Supabase)", "cost": 25.0},
        "redis": {"name": "Managed Redis (Upstash / Redis Cloud)", "cost": 10.0},
        "object_storage": {"name": "S3 / Cloudflare R2 Storage", "cost": 5.0},
        "llm_api": {"name": "LLM API Usage (5,000 requests/mo)", "cost": 25.0},
        "search_api": {"name": "Web Search API tier", "cost": 10.0},
    }

    def estimate(
        self,
        components: List[str],
        scale: str = "mvp",
        include_ai_budget: bool = True
    ) -> Dict[str, Any]:
        """Generate monthly cost estimate breakdown."""
        breakdown: Dict[str, float] = {}
        total = 0.0

        for comp in components:
            comp_key = comp.lower().replace(" ", "_")
            if comp_key in self.DEFAULT_BENCHMARKS:
                item = self.DEFAULT_BENCHMARKS[comp_key]
                breakdown[item["name"]] = item["cost"]
                total += item["cost"]
            else:
                breakdown[comp] = 12.0
                total += 12.0

        if include_ai_budget and "LLM API Usage (5,000 requests/mo)" not in breakdown:
            ai_cost = 25.0 if scale == "mvp" else 100.0
            breakdown["LLM API Tokens"] = ai_cost
            total += ai_cost

        assumptions = [
            "Assumes managed cloud tiers (e.g. Render, Supabase, Upstash) for minimal DevOps overhead.",
            f"Sized for {scale.upper()} phase (< 5,000 monthly active users).",
            "Bandwidth within free egress allowances."
        ]

        return {
            "total_usd": round(total, 2),
            "breakdown": breakdown,
            "assumptions": assumptions
        }
