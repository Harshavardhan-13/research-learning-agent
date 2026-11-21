import json
import logging

from research_agent.logging_config import JsonFormatter


def test_json_formatter_emits_structured_context() -> None:
    record = logging.LogRecord(
        name="research_agent.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="research_completed",
        args=(),
        exc_info=None,
    )
    record.context = {"source_count": 3}

    payload = json.loads(JsonFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "research_agent.test"
    assert payload["event"] == "research_completed"
    assert payload["context"] == {"source_count": 3}
    assert payload["timestamp"].endswith("+00:00")
