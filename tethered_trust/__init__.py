"""Tethered Trust: fit, compatibility and recall checks for AI agents before they buy."""
from .client import TOOLS, TetheredTrust, TetheredTrustError
from .tools import SHOPPING_TOOLS, TOOL_DEFINITIONS, run_tool, to_anthropic_tools, to_langchain_tools, to_openai_tools

__version__ = "0.1.0"
__all__ = ["TetheredTrust", "TetheredTrustError", "TOOLS", "TOOL_DEFINITIONS", "SHOPPING_TOOLS",
           "to_openai_tools", "to_anthropic_tools", "to_langchain_tools", "run_tool"]
