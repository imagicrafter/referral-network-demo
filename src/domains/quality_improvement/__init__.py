"""
Quality Improvement Analytics Domain.

Provides tools for tracking protocol adoption, best practice spread, and outcome
improvements across the hospital network. Analyzes how quality initiatives
propagate through referral and collaboration relationships.

CHA Programs Supported:
- IPSO Collaborative (Improving Sepsis Outcomes)
- CLABSI Prevention
- Pediatric Early Warning Score
- Safe Medication Administration
"""
from src.domains.quality_improvement.tools import TOOLS, TOOL_DEFINITIONS

__all__ = ["TOOLS", "TOOL_DEFINITIONS"]
