import pytest

from research_agent.config import ConfigurationError, Settings, load_settings


def test_load_settings_uses_safe_defaults() -> None:
    assert load_settings({}) == Settings(
        model="gemini-3.1-pro-preview",
        log_level="INFO",
    )


def test_load_settings_accepts_environment_overrides() -> None:
    settings = load_settings(
        {
            "RESEARCH_AGENT_MODEL": "gemini-2.5-pro",
            "RESEARCH_AGENT_LOG_LEVEL": "debug",
        }
    )

    assert settings == Settings(model="gemini-2.5-pro", log_level="DEBUG")


@pytest.mark.parametrize(
    ("environment", "message"),
    [
        ({"RESEARCH_AGENT_MODEL": "not-a-gemini-model"}, "Gemini model"),
        ({"RESEARCH_AGENT_LOG_LEVEL": "VERBOSE"}, "must be one of"),
    ],
)
def test_load_settings_rejects_invalid_values(
    environment: dict[str, str], message: str
) -> None:
    with pytest.raises(ConfigurationError, match=message):
        load_settings(environment)
