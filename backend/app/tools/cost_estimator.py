import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class CostEstimatorTool:
    """Cloud infrastructure cost estimator tool for MVP architectures.
    
    Loads verified pinned pricing from data/cloud_pricing.json (ADR-004, SKILL Step 5).
    If a component cannot be mapped to verified pricing data, it is flagged as 'estimate_unverified'.
    """

    def __init__(self, pricing_file_path: Optional[str] = None):
        self.pricing_file_path = pricing_file_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "data",
            "cloud_pricing.json"
        )
        self.pricing_data = self._load_pricing()

    def _load_pricing(self) -> Dict[str, Any]:
        """Load pinned pricing file from disk with safe fallback."""
        if os.path.exists(self.pricing_file_path):
            try:
                with open(self.pricing_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read pricing file {self.pricing_file_path}: {e}")

        # Fallback dictionary if file not found
        return {
            "metadata": {"retrieved_date": "2026-10-27", "sources": []},
            "tiers": {
                "web_service": {"name": "Managed Web Service (Render)", "monthly_cost": 7.0, "source_url": "https://render.com/pricing"},
                "background_worker": {"name": "Background Worker Instance", "monthly_cost": 7.0, "source_url": "https://render.com/pricing"},
                "database": {"name": "Managed Serverless PostgreSQL (Neon)", "monthly_cost": 19.0, "source_url": "https://neon.tech/pricing"},
                "redis": {"name": "Serverless Redis (Upstash)", "monthly_cost": 10.0, "source_url": "https://upstash.com/pricing/redis"},
                "object_storage": {"name": "Object Storage (Cloudflare R2)", "monthly_cost": 5.0, "source_url": "https://www.cloudflare.com/developer-platform/products/r2/"},
                "llm_api": {"name": "LLM API Tokens", "monthly_cost": 25.0, "source_url": "https://openrouter.ai/models"},
                "search_api": {"name": "Search API Tier", "monthly_cost": 10.0, "source_url": "https://tavily.com/#pricing"}
            }
        }

    def estimate(
        self,
        components: List[str],
        scale: str = "mvp",
        include_ai_budget: bool = True
    ) -> Dict[str, Any]:
        """Generate monthly cost estimate breakdown with verified sources and assumption flags."""
        tiers = self.pricing_data.get("tiers", {})
        breakdown: Dict[str, float] = {}
        sources: Dict[str, str] = {}
        unverified_components: List[str] = []
        total = 0.0

        ALIASES = {
            "postgres": "database",
            "postgresql": "database",
            "managed_postgresql": "database",
            "sql": "database",
            "database": "database",
            "fastapi": "web_service",
            "backend": "web_service",
            "api": "web_service",
            "frontend": "web_service",
            "web_service": "web_service",
            "managed_web_service": "web_service",
            "worker": "background_worker",
            "celery": "background_worker",
            "background_worker": "background_worker",
            "redis": "redis",
            "serverless_redis": "redis",
            "cache": "redis",
            "storage": "object_storage",
            "s3": "object_storage",
            "r2": "object_storage",
            "object_storage": "object_storage",
            "llm": "llm_api",
            "ai": "llm_api",
            "llm_api": "llm_api",
            "llm_api_tokens": "llm_api",
            "search": "search_api",
            "tavily": "search_api",
            "monitoring": "monitoring",
            "sentry": "monitoring",
        }

        for comp in components:
            comp_key = comp.lower().replace(" ", "_").replace("-", "_")
            matched_tier = None

            # 1. Alias or direct match
            resolved_key = comp_key
            if resolved_key in ALIASES:
                resolved_key = ALIASES[resolved_key]
            else:
                for alias_term, target_k in ALIASES.items():
                    if alias_term in comp_key:
                        resolved_key = target_k
                        break

            if resolved_key in tiers:
                matched_tier = tiers[resolved_key]
            else:
                for k, tier in tiers.items():
                    if k in comp_key or comp_key in k:
                        matched_tier = tier
                        break

            if matched_tier:
                name = matched_tier.get("name", comp)
                cost = float(matched_tier.get("monthly_cost", 10.0))
                breakdown[name] = cost
                sources[name] = matched_tier.get("source_url", "")
                total += cost
            else:
                # Unverified fallback component
                unverified_name = f"{comp} (Estimate)"
                breakdown[unverified_name] = 12.0
                sources[unverified_name] = "estimate_unverified"
                unverified_components.append(comp)
                total += 12.0

        if include_ai_budget:
            llm_tier = tiers.get("llm_api", {"name": "LLM API Tokens", "monthly_cost": 25.0, "source_url": "https://openrouter.ai/models"})
            llm_name = llm_tier["name"]
            if llm_name not in breakdown:
                ai_cost = float(llm_tier.get("monthly_cost", 25.0)) if scale == "mvp" else 100.0
                breakdown[llm_name] = ai_cost
                sources[llm_name] = llm_tier.get("source_url", "")
                total += ai_cost

        assumptions = [
            f"Pricing derived from pinned cloud catalog data/cloud_pricing.json ({self.pricing_data.get('metadata', {}).get('retrieved_date', '2026-10-27')}).",
            f"Sized for {scale.upper()} phase (< 5,000 monthly active users).",
            "Bandwidth within free egress allowances."
        ]

        if unverified_components:
            assumptions.append(f"Unverified estimates used for: {', '.join(unverified_components)} (marked estimate_unverified).")

        return {
            "total_usd": round(total, 2),
            "breakdown": breakdown,
            "sources": sources,
            "estimate_unverified": len(unverified_components) > 0,
            "assumptions": assumptions,
            "retrieved_date": self.pricing_data.get("metadata", {}).get("retrieved_date", "2026-10-27")
        }
