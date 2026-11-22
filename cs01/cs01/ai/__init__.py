"""
cs01.ai — Local LLM Integration for Qwen 2.5 Coder.
Zero cloud egress · Local-first execution.
"""

from .client import LocalLLMClient
from .narrator import generate_executive_dpo_brief, explain_finding_in_depth

__all__ = ["LocalLLMClient", "generate_executive_dpo_brief", "explain_finding_in_depth"]
