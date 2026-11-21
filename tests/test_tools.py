from google.adk.tools.google_search_tool import GoogleSearchTool

from research_agent.tools import get_research_tools


def test_research_tool_set_is_google_search_only() -> None:
    tools = get_research_tools()

    assert isinstance(tools, tuple)
    assert len(tools) == 1
    assert isinstance(tools[0], GoogleSearchTool)
    assert tools[0].name == "google_search"
