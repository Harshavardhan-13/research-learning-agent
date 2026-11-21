"""Google ADK root agent definition."""

from google.adk import Agent
from google.genai import types

from .callbacks import enforce_grounded_response
from .config import load_settings
from .logging_config import configure_logging
from .policy import RESEARCH_INSTRUCTION
from .tools import get_research_tools

settings = load_settings()
logger = configure_logging(settings.log_level)

root_agent = Agent(
    name="personal_research_agent",
    model=settings.model,
    description=(
        "A read-only learning agent that researches trustworthy web sources and "
        "teaches one concise module at a time."
    ),
    instruction=RESEARCH_INSTRUCTION,
    tools=list(get_research_tools()),
    generate_content_config=types.GenerateContentConfig(temperature=1.0),
    after_model_callback=enforce_grounded_response,
)

logger.info(
    "agent_initialized",
    extra={
        "context": {
            "model": settings.model,
            "tool_count": len(get_research_tools()),
        }
    },
)
