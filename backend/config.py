"""Configuration for the ThaiLawOnline LLM Council Chatbot."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- OpenRouter API ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Council members - list of OpenRouter model identifiers
COUNCIL_MODELS = [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "x-ai/grok-4",
]

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "google/gemini-3-pro-preview"

# --- Vortex Database (Thai Legal Documents) ---
VORTEX_DB_TYPE = os.getenv("VORTEX_DB_TYPE", "mysql")  # "mysql" or "json_files"
VORTEX_MYSQL_HOST = os.getenv("VORTEX_MYSQL_HOST", "localhost")
VORTEX_MYSQL_PORT = int(os.getenv("VORTEX_MYSQL_PORT", "3306"))
VORTEX_MYSQL_USER = os.getenv("VORTEX_MYSQL_USER", "")
VORTEX_MYSQL_PASS = os.getenv("VORTEX_MYSQL_PASS", "")
VORTEX_MYSQL_DB = os.getenv("VORTEX_MYSQL_DB", "")
VORTEX_JSON_DIR = os.getenv("VORTEX_JSON_DIR", "data/vortex")
VORTEX_MAX_CHUNKS = int(os.getenv("VORTEX_MAX_CHUNKS", "10"))

# --- Notion (optional supplementary legal facts) ---
NOTION_ENABLED = os.getenv("NOTION_ENABLED", "false").lower() == "true"
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# --- WordPress Integration ---
WP_API_KEY = os.getenv("WP_API_KEY", "")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "https://thailawonline.com,https://www.thailawonline.com"
    ).split(",")
    if origin.strip()
]

# --- Storage ---
DATA_DIR = "data/conversations"
