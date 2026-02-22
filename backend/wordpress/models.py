"""Pydantic request/response models for the WordPress chat API."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message from WordPress."""

    message: str = Field(..., min_length=1, max_length=5000, description="User's question")
    session_id: str = Field(
        default="",
        max_length=200,
        description="Optional session ID for conversation continuity",
    )


class SourceCitation(BaseModel):
    """A single source citation from the RAG retrieval."""

    source: str = Field(..., description="Source identifier (law section, case number)")
    excerpt: str = Field(default="", description="Brief excerpt from the source")


class ChatResponse(BaseModel):
    """Response sent back to WordPress."""

    answer: str = Field(..., description="Final synthesized legal answer")
    sources: list[SourceCitation] = Field(
        default_factory=list, description="Source citations used"
    )
    session_id: str = Field(default="", description="Session ID for follow-ups")
    council_metadata: dict = Field(
        default_factory=dict,
        description="Optional metadata about the council process",
    )
