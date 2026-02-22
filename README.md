<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/OpenRouter-AI-7C3AED?style=for-the-badge&logo=openai&logoColor=white" alt="OpenRouter"/>
  <img src="https://img.shields.io/badge/WordPress-Plugin-21759B?style=for-the-badge&logo=wordpress&logoColor=white" alt="WordPress"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">⚖️ ThaiLawOnline Chatbot</h1>

<p align="center">
  <strong>An AI-powered Thai legal assistant combining multi-LLM council reasoning with RAG-based legal document retrieval</strong>
</p>

<p align="center">
  <em>Built for <a href="https://thailawonline.com">thailawonline.com</a> — Providing accurate, well-cited answers about Thai law backed by ~50,000 legal documents</em>
</p>

---

## 🌟 Overview

ThaiLawOnline Chatbot is an advanced legal AI assistant that goes beyond simple question-answering. Instead of relying on a single AI model, it employs a **3-stage LLM Council** architecture (inspired by [karpathy/llm-council](https://github.com/karpathy/llm-council)) where multiple AI models deliberate, peer-review, and synthesize answers — producing more reliable and comprehensive legal responses.

### Why a Council?

| Single LLM | LLM Council (This Project) |
|---|---|
| One model, one perspective | 4 models provide diverse perspectives |
| No quality check | Models peer-rank each other's answers |
| Potential hallucinations go unchecked | Chairman synthesizes the best insights |
| Inconsistent accuracy | Aggregate wisdom improves reliability |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    thailawonline.com (WordPress)                 │
│                         Chat Widget                              │
│                    [chatbot-connector.js]                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ AJAX + Nonce
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│              WordPress Plugin (chatbot-connector.php)            │
│              ├── Nonce verification (CSRF protection)            │
│              ├── API key injection (server-side only)            │
│              └── wp_remote_post → localhost:8001                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ X-API-Key Header
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (:8001)                        │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  1️⃣  RAG Retrieval                                        │  │
│  │     ├── Vortex DB (MySQL FULLTEXT / JSON fallback)        │  │
│  │     ├── Notion API (optional)                              │  │
│  │     └── Build system prompt with legal context             │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  2️⃣  LLM Council — Stage 1: Parallel Responses            │  │
│  │     ├── GPT-5.1                                            │  │
│  │     ├── Gemini 3 Pro                                       │  │
│  │     ├── Claude Sonnet 4.5                                  │  │
│  │     └── Grok 4                                             │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  3️⃣  LLM Council — Stage 2: Peer Ranking                  │  │
│  │     Each model ranks the anonymized responses              │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  4️⃣  LLM Council — Stage 3: Chairman Synthesis             │  │
│  │     Gemini 3 Pro synthesizes the final answer              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                    Return answer + source citations               │
└──────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🤖 Multi-LLM Council
- **4 council members** query in parallel via [OpenRouter](https://openrouter.ai) — GPT-5.1, Gemini 3 Pro, Claude Sonnet 4.5, Grok 4
- **Peer-ranking** — each model evaluates and ranks the others' responses (anonymized)
- **Chairman synthesis** — Gemini 3 Pro synthesizes the collective wisdom into a single answer
- **Aggregate scoring** — mathematical ranking of model performance per query

### 📚 RAG-Powered Legal Knowledge
- **Vortex Database** — ~50,000 Thai legal documents including:
  - Civil and Commercial Code
  - Supreme Court judgments & decisions
  - Legal commentaries
- **MySQL FULLTEXT search** for production, JSON fallback for development
- **Notion integration** (optional) for supplementary legal facts

### 🔒 Security
- **API key validation** — X-API-Key header authentication
- **WordPress nonce verification** — CSRF protection on all AJAX requests
- **Server-side secrets** — API keys never exposed to the browser
- **CORS whitelisting** — only approved origins can access the API

### ⚡ Streaming Support
- **Server-Sent Events (SSE)** — real-time progress updates
- Frontend shows stage-by-stage progress: *"Retrieving legal documents..."*, *"Consulting legal experts..."*, *"Synthesizing final answer..."*

### 🌐 WordPress Integration
- Drop-in WordPress plugin with admin settings page
- Zero-configuration chat widget
- Auto-generates session IDs for conversation tracking

---

## 📁 Project Structure

```
ThaiLawOnline-Chatbot/
│
├── 📄 main.py                    # Entry point (python main.py)
├── 📄 pyproject.toml             # Project metadata & dependencies
├── 📄 start.sh                   # Production startup script
├── 📄 .env.example               # Environment variable template
│
├── 🐍 backend/                   # FastAPI application
│   ├── __init__.py
│   ├── config.py                 # All env vars & model configuration
│   ├── council.py                # 3-stage LLM Council orchestration
│   ├── main.py                   # FastAPI routes & middleware
│   ├── openrouter.py             # Async OpenRouter API client
│   ├── storage.py                # JSON conversation persistence
│   │
│   ├── 📂 rag/                   # Retrieval-Augmented Generation
│   │   ├── __init__.py
│   │   ├── retriever.py          # Orchestrates Vortex + Notion
│   │   ├── vortex_client.py      # MySQL FULLTEXT / JSON search
│   │   ├── notion_client.py      # Optional Notion API integration
│   │   └── prompts.py            # Thai legal system prompts
│   │
│   └── 📂 wordpress/             # WordPress integration
│       ├── __init__.py
│       ├── auth.py               # X-API-Key validation middleware
│       └── models.py             # Pydantic request/response models
│
├── 🌐 wordpress/                 # WordPress plugin files
│   ├── chatbot-connector.php     # WP plugin (AJAX proxy)
│   └── chatbot-connector.js      # Frontend chat connector
│
└── 🚀 deploy/                    # Deployment configuration
    ├── nginx.conf                # Reverse proxy for api.thailawonline.com
    └── chatbot.service           # systemd service file
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **OpenRouter API Key** — [Get one here](https://openrouter.ai/keys)
- **MySQL** (optional, for Vortex DB — JSON fallback available)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Khuzaima-AI-2112/ThaiLawOnline-Chatbot.git
cd ThaiLawOnline-Chatbot

# 2. Install dependencies
pip install -e .

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys and database credentials
```

### Running Locally

```bash
# Option 1: Direct run
python main.py

# Option 2: Module run (recommended)
python -m backend.main

# Option 3: With Uvicorn (production-like)
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --workers 2
```

The API will be available at `http://localhost:8001`

### Verify Installation

```bash
# Health check
curl http://localhost:8001/health
# → {"status": "ok"}

# Root endpoint
curl http://localhost:8001/
# → {"status": "ok", "service": "ThaiLawOnline Chatbot API"}
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | — | OpenRouter API key for LLM access |
| `VORTEX_DB_TYPE` | ❌ | `mysql` | Database type: `mysql` or `json_files` |
| `VORTEX_MYSQL_HOST` | ❌ | `localhost` | MySQL host |
| `VORTEX_MYSQL_PORT` | ❌ | `3306` | MySQL port |
| `VORTEX_MYSQL_USER` | ❌ | — | MySQL username |
| `VORTEX_MYSQL_PASS` | ❌ | — | MySQL password |
| `VORTEX_MYSQL_DB` | ❌ | — | MySQL database name |
| `VORTEX_JSON_DIR` | ❌ | `data/vortex` | JSON files directory (fallback) |
| `VORTEX_MAX_CHUNKS` | ❌ | `10` | Max legal chunks per query |
| `WP_API_KEY` | ❌ | — | Shared secret for WordPress auth |
| `ALLOWED_ORIGINS` | ❌ | `thailawonline.com` | Comma-separated CORS origins |
| `NOTION_ENABLED` | ❌ | `false` | Enable Notion integration |
| `NOTION_API_KEY` | ❌ | — | Notion API key |
| `NOTION_DATABASE_ID` | ❌ | — | Notion database ID |

### Council Models

The default council configuration (in `backend/config.py`):

```python
COUNCIL_MODELS = [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "x-ai/grok-4",
]
CHAIRMAN_MODEL = "google/gemini-3-pro-preview"
```

You can modify these to use any models available on [OpenRouter](https://openrouter.ai/models).

---

## 📡 API Reference

### WordPress Chat Endpoint

#### `POST /api/chat`

Main endpoint for WordPress integration. Requires `X-API-Key` header.

**Request:**
```json
{
  "message": "What is Section 420 of the Civil and Commercial Code?",
  "session_id": "optional-session-uuid"
}
```

**Response:**
```json
{
  "answer": "Section 420 of the Thai Civil and Commercial Code states that...",
  "sources": [
    {
      "source": "Civil and Commercial Code",
      "excerpt": "Section 420: A person who, wilfully or negligently..."
    }
  ],
  "session_id": "generated-or-provided-uuid",
  "council_metadata": {
    "models_used": ["openai/gpt-5.1", "google/gemini-3-pro-preview", ...],
    "chairman": "google/gemini-3-pro-preview",
    "aggregate_rankings": [
      {"model": "anthropic/claude-sonnet-4.5", "average_rank": 1.5, "rankings_count": 4}
    ]
  }
}
```

#### `POST /api/chat/stream`

Streaming version using Server-Sent Events (SSE).

**Events:**
```
data: {"type": "status", "message": "Retrieving legal documents..."}
data: {"type": "status", "message": "Consulting legal experts..."}
data: {"type": "stage1_complete", "count": 4}
data: {"type": "status", "message": "Evaluating responses..."}
data: {"type": "stage2_complete"}
data: {"type": "status", "message": "Synthesizing final answer..."}
data: {"type": "complete", "data": {"answer": "...", "sources": [...], "session_id": "..."}}
```

### Council UI Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/conversations` | List all conversations |
| `POST` | `/api/conversations` | Create new conversation |
| `GET` | `/api/conversations/{id}` | Get conversation details |
| `POST` | `/api/conversations/{id}/message` | Send message |
| `POST` | `/api/conversations/{id}/message/stream` | Send message (SSE) |

### Health Check

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service status |
| `GET` | `/health` | Health check |

---

## 🚢 Deployment

### Production Setup (Linux Server)

```bash
# 1. Clone and install
git clone https://github.com/Khuzaima-AI-2112/ThaiLawOnline-Chatbot.git
cd ThaiLawOnline-Chatbot
pip install -e .

# 2. Configure
cp .env.example .env
nano .env  # Fill in production values

# 3. Setup systemd service
sudo cp deploy/chatbot.service /etc/systemd/system/
sudo systemctl enable chatbot
sudo systemctl start chatbot

# 4. Setup Nginx reverse proxy
sudo cp deploy/nginx.conf /etc/nginx/sites-available/chatbot.conf
sudo ln -s /etc/nginx/sites-available/chatbot.conf /etc/nginx/sites-enabled/
sudo certbot --nginx -d api.thailawonline.com  # SSL certificate
sudo systemctl reload nginx
```

### WordPress Plugin Setup

1. Copy `wordpress/chatbot-connector.php` and `wordpress/chatbot-connector.js` to `wp-content/plugins/thailaw-chatbot/`
2. Activate the plugin in WordPress admin
3. Go to **Settings → ThaiLaw Chatbot** and enter the API key
4. The chat widget will automatically appear on your site

---

## 🧠 How the LLM Council Works

```
┌─────────────────────────────────────────────────────────────┐
│                    User Asks a Legal Question                │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  📚 RAG Retrieval                                           │
│  Search Vortex DB for relevant legal documents              │
│  Inject context into system prompt                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  🔄 Stage 1: Parallel Responses                            │
│                                                             │
│  GPT-5.1 ────────────┐                                     │
│  Gemini 3 Pro ────────┤──→ 4 independent legal answers      │
│  Claude Sonnet 4.5 ───┤                                     │
│  Grok 4 ──────────────┘                                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  🏅 Stage 2: Peer Ranking                                   │
│                                                             │
│  Responses anonymized as A, B, C, D                         │
│  Each model evaluates & ranks all responses                 │
│  Aggregate rankings computed mathematically                 │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  👨‍⚖️ Stage 3: Chairman Synthesis                           │
│                                                             │
│  Gemini 3 Pro reviews all responses + rankings              │
│  Synthesizes collective wisdom into final answer            │
│  Returns comprehensive, well-cited legal response           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                    📤 Answer + Source Citations
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- **[karpathy/llm-council](https://github.com/karpathy/llm-council)** — Inspiration for the multi-LLM council architecture
- **[OpenRouter](https://openrouter.ai)** — Unified API for accessing multiple LLM providers
- **[FastAPI](https://fastapi.tiangolo.com)** — Modern, high-performance Python web framework
- **[thailawonline.com](https://thailawonline.com)** — Thai legal knowledge platform

---

<p align="center">
  <strong>Built with ❤️ for the Thai legal community</strong>
</p>
