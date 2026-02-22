"""Orchestrates retrieval from Vortex DB and optional Notion sources."""

import asyncio

from .notion_client import search_notion
from .prompts import build_system_prompt
from .vortex_client import search_vortex


async def retrieve_context(query: str) -> list[dict]:
    """Retrieve relevant legal document chunks from all configured sources.

    Queries Vortex DB and (optionally) Notion in parallel, then merges results.

    Args:
        query: The user's question.

    Returns:
        List of context chunk dicts with 'content', 'source', and 'score' keys.
    """
    # Query all sources in parallel
    vortex_task = search_vortex(query)
    notion_task = search_notion(query)

    vortex_results, notion_results = await asyncio.gather(
        vortex_task, notion_task
    )

    # Merge: Vortex chunks first (primary), then Notion (supplementary)
    all_chunks = vortex_results + notion_results
    return all_chunks


async def retrieve_and_build_messages(query: str) -> list[dict]:
    """Retrieve context and build the messages list with RAG system prompt.

    Args:
        query: The user's question.

    Returns:
        Messages list suitable for LLM council (system prompt + user message).
    """
    context_chunks = await retrieve_context(query)
    system_prompt = build_system_prompt(context_chunks)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    return messages, context_chunks
