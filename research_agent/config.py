"""Environment-backed configuration for the research agent."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

_DEFAULT_MODEL = "gemini-3.1-pro-preview"
_DEFAULT_LOG_LEVEL = "INFO"
_ALLOWED_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class ConfigurationError(ValueError):
    """Raised when agent configuration is invalid."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated settings that are safe to log."""

    model: str
    log_level: str


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Load agent settings without reading or storing credentials."""
    source = os.environ if environ is None else environ
    model = source.get("RESEARCH_AGENT_MODEL", _DEFAULT_MODEL).strip()
    log_level = source.get("RESEARCH_AGENT_LOG_LEVEL", _DEFAULT_LOG_LEVEL).upper()

    if not model.startswith("gemini-"):
        raise ConfigurationError(
            "RESEARCH_AGENT_MODEL must be a Gemini model identifier."
        )
    if log_level not in _ALLOWED_LOG_LEVELS:
        allowed = ", ".join(sorted(_ALLOWED_LOG_LEVELS))
        raise ConfigurationError(
            f"RESEARCH_AGENT_LOG_LEVEL must be one of: {allowed}."
        )

    return Settings(model=model, log_level=log_level)
