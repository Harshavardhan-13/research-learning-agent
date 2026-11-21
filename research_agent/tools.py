"""Read-only tools available to the research agent."""

from __future__ import annotations

from typing import Final

from google.adk.tools import google_search
from google.adk.tools.base_tool import BaseTool

_RESEARCH_TOOLS: Final[tuple[BaseTool, ...]] = (google_search,)


def get_research_tools() -> tuple[BaseTool, ...]:
    """Return the immutable, read-only tool set for the agent."""
    return _RESEARCH_TOOLS
