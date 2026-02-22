# CLAUDE.md - ThaiLawOnline Chatbot

## Project Overview

Thai legal chatbot for thailawonline.com combining:
- **LLM Council** (forked from karpathy/llm-council) — 3-stage pipeline: parallel LLM queries → peer ranking → chairman synthesis
- **Vortex Database** — ~50k Thai legal documents (civil code, Supreme Court judgments) via RAG
- **Optional Notion** — supplementary legal facts
- **WordPress trigger** — chat widget on thailawonline.com → FastAPI backend → answer

## Architecture

```
WordPress Chat Widget → wp_ajax proxy → FastAPI Backend (localhost:8001)
    1. Validate API key
    2. Query Vortex DB (MySQL FULLTEXT or JSON files)
    3. Query Notion (optional)
    4. Inject context into LLM Council system prompt
    5. Run 3-stage council via OpenRouter
    6. Return answer + citations
```

## File Structure

```
backend/
├── config.py          — All env vars (OpenRouter, Vortex, Notion, WP)
├── council.py         — 3-stage council with optional RAG messages param
├── main.py            — FastAPI app: /api/chat (WP), /api/conversations (council UI)
├── openrouter.py      — Async OpenRouter API client
├── storage.py         — JSON conversation persistence
├── rag/
│   ├── retriever.py   — Orchestrates Vortex + Notion retrieval
│   ├── vortex_client.py — MySQL FULLTEXT or JSON file search
│   ├── notion_client.py — Optional Notion API integration
│   └── prompts.py     — Thai legal system prompt with {context} injection
└── wordpress/
    ├── auth.py        — X-API-Key validation middleware
    └── models.py      — ChatRequest/ChatResponse Pydantic models

deploy/
├── nginx.conf         — Reverse proxy config for api.thailawonline.com
└── chatbot.service    — systemd service file

wordpress/
├── chatbot-connector.php — WP plugin (AJAX proxy to backend)
└── chatbot-connector.js  — Frontend JS chat connector
```

## Key Implementation Details

### Relative Imports
All backend modules use relative imports (`from .config import ...`). Run as `python -m backend.main` from project root.

### RAG Context Injection
`council.py:run_full_council()` accepts optional `messages` param. When provided, Stage 1 uses pre-built messages with system prompt containing Vortex DB context instead of plain user query.

### Vortex DB
- MySQL: FULLTEXT search on `legal_chunks` table (`content`, `source` columns)
- JSON fallback: Token overlap scoring on files in `VORTEX_JSON_DIR`
- Adapt table/column names after inspecting actual schema on Hostinger

### WordPress Integration
- PHP plugin proxies AJAX requests to localhost:8001
- API key stays server-side (never exposed to browser)
- Nonce verification for CSRF protection

### Port
Backend: **8001** (to avoid conflict with other services)

## Environment
Copy `.env.example` to `.env`. Required: `OPENROUTER_API_KEY`. See `.env.example` for all variables.

## Running Locally
```bash
pip install -e .
cp .env.example .env  # fill in values
python -m backend.main
# or: python main.py
```
