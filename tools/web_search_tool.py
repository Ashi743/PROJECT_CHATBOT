from langchain_core.tools import tool
from ddgs import DDGS
from typing import Optional

@tool
def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo for real-time information.
    Use when user asks about current events, recent news, or up-to-date information.

    Args:
        query: Search query (e.g., "latest AI news", "how to make pasta")
        num_results: Number of results to return (1-10, default: 5)

    Examples:
    - "Search for latest news about AI"
    - "Find information about climate change"
    - "What's new in technology"
    """
    try:
        # Validate inputs
        if not query or not query.strip():
            return "Error: Please provide a search query."

        num_results = max(1, min(int(num_results), 10))  # Clamp between 1-10

        # DuckDuckGo search
        ddgs = DDGS()
        results = ddgs.text(query.strip(), max_results=num_results)

        if not results:
            return f"No results found for: '{query}'"

        # Build output
        output = []
        output.append(f"Search Results for: '{query}'")
        output.append("=" * 60)

        # Add search results
        output.append(f"Top {len(results)} Results:")
        output.append("-" * 60)

        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url_str = result.get("href", "")
            snippet = result.get("body", "No description")

            output.append(f"\n{i}. {title}")
            output.append(f"   URL: {url_str}")
            output.append(f"   Summary: {snippet[:200]}..." if len(snippet) > 200 else f"   Summary: {snippet}")

        return "\n".join(output)

    except Exception as e:
        return f"Web search error: {str(e)}"
