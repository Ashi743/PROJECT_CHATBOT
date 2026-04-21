from langchain_core.tools import tool
import os
import requests
from typing import Optional

@tool
def web_search(query: str, num_results: int = 5, search_depth: str = "basic") -> str:
    """
    Search the web using Tavily API for real-time information.
    Use when user asks about current events, recent news, or up-to-date information.

    Args:
        query: Search query (e.g., "latest AI news", "how to make pasta")
        num_results: Number of results to return (1-10, default: 5)
        search_depth: "basic" for quick results or "advanced" for detailed search

    Examples:
    - "Search for latest news about AI"
    - "Find information about climate change"
    - "What's new in technology"
    """
    try:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return "Error: TAVILY_API_KEY not set in .env file. Get a free key at https://tavily.com/"

        # Validate inputs
        if not query or not query.strip():
            return "Error: Please provide a search query."

        num_results = max(1, min(int(num_results), 10))  # Clamp between 1-10

        # Tavily API endpoint
        url = "https://api.tavily.com/search"

        # Request payload
        payload = {
            "api_key": api_key,
            "query": query.strip(),
            "max_results": num_results,
            "search_depth": search_depth,
            "include_answer": True,
            "include_raw_content": False,
        }

        # Make API request
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code != 200:
            error_msg = response.json().get("error", "Unknown error")
            return f"Error: API request failed ({response.status_code}). {error_msg}"

        data = response.json()

        # Check if we got results
        if not data.get("results"):
            return f"No results found for: '{query}'"

        # Build output
        output = []
        output.append(f"Search Results for: '{query}'")
        output.append("=" * 60)

        # Add answer if available
        if data.get("answer"):
            output.append(f"\nQuick Answer:\n{data['answer']}\n")

        # Add search results
        output.append(f"Top {len(data['results'])} Results:")
        output.append("-" * 60)

        for i, result in enumerate(data["results"], 1):
            title = result.get("title", "No title")
            url_str = result.get("url", "")
            snippet = result.get("content", "No description")

            output.append(f"\n{i}. {title}")
            output.append(f"   URL: {url_str}")
            output.append(f"   Summary: {snippet[:200]}..." if len(snippet) > 200 else f"   Summary: {snippet}")

        return "\n".join(output)

    except requests.exceptions.Timeout:
        return "Error: Search request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Error: Network error during search. {str(e)}"
    except ValueError as e:
        return f"Error: Invalid parameter. {str(e)}"
    except Exception as e:
        return f"Web search error: {str(e)}"
