from research_agent.callbacks import (
    GroundedSource,
    count_words,
    format_grounded_response,
)


def test_grounded_response_preserves_links_within_word_limit() -> None:
    body = " ".join(f"word-{index}" for index in range(400))
    sources = (
        GroundedSource("Official DNS standard", "https://www.rfc-editor.org/rfc/rfc1034"),
        GroundedSource("ICANN DNS guide", "https://www.icann.org/resources/pages/dns-2024-02-20-en"),
    )

    response, truncated = format_grounded_response(body, sources)

    assert truncated is True
    assert count_words(response) <= 300
    assert "https://www.rfc-editor.org/rfc/rfc1034" in response
    assert "https://www.icann.org/resources/pages/dns-2024-02-20-en" in response


def test_grounded_response_reports_missing_source_metadata() -> None:
    response, truncated = format_grounded_response("Brief researched answer.", ())

    assert truncated is False
    assert "Source verification unavailable" in response


def test_grounded_response_removes_repeated_full_answer() -> None:
    body = (
        "Prerequisites: know basic APIs. Module 1 explains MCP servers. "
        "Practice: list one useful tool. Ask for module 2."
    )

    response, changed = format_grounded_response(f"{body}\n{body}", ())

    assert changed is True
    assert response.count("Prerequisites:") == 1


def test_grounded_response_replaces_model_generated_source_list() -> None:
    body = """Module 1 explains the protocol.

**Sources for this module:**
* Unlinked source
* Another source

Ask for module 2."""
    sources = (GroundedSource("Official MCP docs", "https://modelcontextprotocol.io"),)

    response, changed = format_grounded_response(body, sources)

    assert changed is True
    assert "Unlinked source" not in response
    assert "Ask for module 2." in response
    assert "[Official MCP docs](https://modelcontextprotocol.io)" in response
