"""Vortex Database client for querying Thai legal documents.

Supports two backends:
- MySQL with FULLTEXT search (preferred for production on Hostinger)
- JSON files with simple text matching (fallback / development)
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

from ..config import (
    VORTEX_DB_TYPE,
    VORTEX_JSON_DIR,
    VORTEX_MAX_CHUNKS,
    VORTEX_MYSQL_DB,
    VORTEX_MYSQL_HOST,
    VORTEX_MYSQL_PASS,
    VORTEX_MYSQL_PORT,
    VORTEX_MYSQL_USER,
)


async def search_vortex(query: str, max_results: Optional[int] = None) -> list[dict]:
    """Search Vortex DB for relevant legal document chunks.

    Args:
        query: User's search query (Thai or English).
        max_results: Maximum number of chunks to return.

    Returns:
        List of dicts with 'content', 'source', and 'score' keys.
    """
    max_results = max_results or VORTEX_MAX_CHUNKS

    if VORTEX_DB_TYPE == "mysql":
        return await _search_mysql(query, max_results)
    elif VORTEX_DB_TYPE == "json_files":
        return await _search_json_files(query, max_results)
    else:
        print(f"Unknown VORTEX_DB_TYPE: {VORTEX_DB_TYPE}")
        return []


async def _search_mysql(query: str, max_results: int) -> list[dict]:
    """Search using MySQL FULLTEXT index.

    Expects a table structure like:
        legal_chunks (
            id INT PRIMARY KEY,
            content TEXT,           -- chunk text (Thai/English)
            source VARCHAR(500),    -- e.g. "Civil Code Section 420" or case number
            category VARCHAR(100),  -- e.g. "civil_code", "supreme_court"
            FULLTEXT(content)
        )
    Adapt table/column names after inspecting the actual Vortex DB schema.
    """
    try:
        import aiomysql
    except ImportError:
        print("aiomysql not installed — falling back to JSON search")
        return await _search_json_files(query, max_results)

    try:
        conn = await aiomysql.connect(
            host=VORTEX_MYSQL_HOST,
            port=VORTEX_MYSQL_PORT,
            user=VORTEX_MYSQL_USER,
            password=VORTEX_MYSQL_PASS,
            db=VORTEX_MYSQL_DB,
            charset="utf8mb4",
        )

        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Use FULLTEXT search with relevance scoring
            # The query is wrapped in double quotes to match the phrase,
            # with IN BOOLEAN MODE for partial matches
            safe_query = query.replace("'", "''")
            await cur.execute(
                """
                SELECT content, source,
                       MATCH(content) AGAINST(%s IN NATURAL LANGUAGE MODE) AS score
                FROM legal_chunks
                WHERE MATCH(content) AGAINST(%s IN NATURAL LANGUAGE MODE)
                ORDER BY score DESC
                LIMIT %s
                """,
                (safe_query, safe_query, max_results),
            )
            rows = await cur.fetchall()

        conn.close()

        return [
            {
                "content": row["content"],
                "source": row.get("source", "Vortex DB"),
                "score": float(row.get("score", 0)),
            }
            for row in rows
        ]

    except Exception as e:
        print(f"Vortex MySQL search error: {e}")
        return []


async def _search_json_files(query: str, max_results: int) -> list[dict]:
    """Fallback: search JSON files in VORTEX_JSON_DIR.

    Each JSON file should be an array of objects with 'content' and 'source' keys,
    or a single object with those keys.
    """
    json_dir = Path(VORTEX_JSON_DIR)
    if not json_dir.exists():
        print(f"Vortex JSON directory not found: {json_dir}")
        return []

    # Tokenize query into words for simple relevance scoring
    query_tokens = set(re.findall(r"\w+", query.lower()))
    if not query_tokens:
        return []

    scored_chunks: list[tuple[float, dict]] = []

    for json_file in json_dir.glob("**/*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Normalize to list of chunks
            chunks = data if isinstance(data, list) else [data]

            for chunk in chunks:
                content = chunk.get("content", "")
                if not content:
                    continue

                # Simple token overlap scoring
                content_tokens = set(re.findall(r"\w+", content.lower()))
                overlap = len(query_tokens & content_tokens)
                if overlap > 0:
                    score = overlap / len(query_tokens)
                    scored_chunks.append((score, {
                        "content": content,
                        "source": chunk.get("source", json_file.stem),
                        "score": score,
                    }))

        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading {json_file}: {e}")
            continue

    # Sort by score descending, return top results
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored_chunks[:max_results]]
