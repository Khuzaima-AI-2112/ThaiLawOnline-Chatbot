"""Optional Notion client for supplementary Thai legal facts.

Queries a Notion database for additional legal information that supplements
the primary Vortex DB. Disabled by default via NOTION_ENABLED=false.
"""

from ..config import NOTION_API_KEY, NOTION_DATABASE_ID, NOTION_ENABLED


async def search_notion(query: str, max_results: int = 5) -> list[dict]:
    """Search Notion database for relevant legal facts.

    Args:
        query: User's search query.
        max_results: Maximum number of results to return.

    Returns:
        List of dicts with 'content' and 'source' keys. Empty if Notion is disabled.
    """
    if not NOTION_ENABLED:
        return []

    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        print("Notion enabled but API key or database ID not configured")
        return []

    try:
        import httpx
    except ImportError:
        print("httpx not available for Notion queries")
        return []

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

    # Search the Notion database using the query API
    payload = {
        "query": query,
        "page_size": max_results,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.notion.com/v1/search",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for page in data.get("results", []):
            # Extract title from page properties
            title = _extract_page_title(page)
            # Extract plain text content from page blocks
            content = await _get_page_content(page["id"], headers)

            if content:
                results.append({
                    "content": content,
                    "source": f"Notion: {title}" if title else "Notion",
                })

        return results[:max_results]

    except Exception as e:
        print(f"Notion search error: {e}")
        return []


def _extract_page_title(page: dict) -> str:
    """Extract title from a Notion page object."""
    properties = page.get("properties", {})
    for prop in properties.values():
        if prop.get("type") == "title":
            title_parts = prop.get("title", [])
            return "".join(part.get("plain_text", "") for part in title_parts)
    return ""


async def _get_page_content(page_id: str, headers: dict) -> str:
    """Fetch and concatenate text blocks from a Notion page."""
    try:
        import httpx

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        text_parts = []
        for block in data.get("results", []):
            block_type = block.get("type", "")
            block_data = block.get(block_type, {})
            rich_texts = block_data.get("rich_text", [])
            for rt in rich_texts:
                text_parts.append(rt.get("plain_text", ""))

        return "\n".join(text_parts)

    except Exception as e:
        print(f"Error fetching Notion page {page_id}: {e}")
        return ""
