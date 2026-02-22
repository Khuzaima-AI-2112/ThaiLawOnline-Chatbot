"""FastAPI backend for ThaiLawOnline LLM Council Chatbot."""

import asyncio
import json
import uuid

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any

from . import storage
from .config import ALLOWED_ORIGINS
from .council import (
    run_full_council,
    generate_conversation_title,
    stage1_collect_responses,
    stage2_collect_rankings,
    stage3_synthesize_final,
    calculate_aggregate_rankings,
)
from .rag.retriever import retrieve_and_build_messages, retrieve_context
from .rag.prompts import build_system_prompt
from .wordpress.auth import validate_api_key
from .wordpress.models import ChatRequest, ChatResponse, SourceCitation

app = FastAPI(title="ThaiLawOnline Chatbot API")

# Enable CORS for WordPress + local development
cors_origins = list(ALLOWED_ORIGINS) + [
    "http://localhost:5173",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic models for original council endpoints ---

class CreateConversationRequest(BaseModel):
    pass


class SendMessageRequest(BaseModel):
    content: str


class ConversationMetadata(BaseModel):
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


# ============================================================
# WordPress Chat Endpoint (the main integration point)
# ============================================================

@app.post("/api/chat", response_model=ChatResponse)
async def wordpress_chat(request: Request, body: ChatRequest):
    """
    Main endpoint called by the WordPress chat widget.

    Flow:
    1. Validate API key
    2. Retrieve legal context from Vortex DB (+ optional Notion)
    3. Build augmented messages with RAG system prompt
    4. Run 3-stage LLM council
    5. Return synthesized answer with source citations
    """
    # Validate API key from WordPress
    await validate_api_key(request)

    user_message = body.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Get or create session
    session_id = body.session_id or str(uuid.uuid4())

    # Ensure conversation exists for session tracking
    conversation = storage.get_conversation(session_id)
    if conversation is None:
        storage.create_conversation(session_id)

    # Store user message
    storage.add_user_message(session_id, user_message)

    # Step 1: Retrieve legal context from Vortex DB + Notion
    messages, context_chunks = await retrieve_and_build_messages(user_message)

    # Step 2: Run the 3-stage LLM council with RAG context
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        user_message, messages=messages
    )

    # Step 3: Extract the final answer
    final_answer = stage3_result.get("response", "")

    # Step 4: Build source citations from retrieved context
    sources = [
        SourceCitation(
            source=chunk.get("source", "Unknown"),
            excerpt=chunk.get("content", "")[:200],
        )
        for chunk in context_chunks
    ]

    # Store assistant response
    storage.add_assistant_message(session_id, stage1_results, stage2_results, stage3_result)

    return ChatResponse(
        answer=final_answer,
        sources=sources,
        session_id=session_id,
        council_metadata={
            "models_used": [r["model"] for r in stage1_results],
            "chairman": stage3_result.get("model", ""),
            "aggregate_rankings": metadata.get("aggregate_rankings", []),
        },
    )


@app.post("/api/chat/stream")
async def wordpress_chat_stream(request: Request, body: ChatRequest):
    """
    Streaming version of the chat endpoint using Server-Sent Events.

    Sends progress events as each stage completes, allowing the frontend
    to show "Consulting legal experts..." status messages.
    """
    await validate_api_key(request)

    user_message = body.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = body.session_id or str(uuid.uuid4())

    conversation = storage.get_conversation(session_id)
    if conversation is None:
        storage.create_conversation(session_id)

    async def event_generator():
        try:
            storage.add_user_message(session_id, user_message)

            # RAG retrieval
            yield f"data: {json.dumps({'type': 'status', 'message': 'Retrieving legal documents...'})}\n\n"
            messages, context_chunks = await retrieve_and_build_messages(user_message)

            # Stage 1
            yield f"data: {json.dumps({'type': 'status', 'message': 'Consulting legal experts...'})}\n\n"
            stage1_results = await stage1_collect_responses(user_message, messages=messages)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'count': len(stage1_results)})}\n\n"

            # Stage 2
            yield f"data: {json.dumps({'type': 'status', 'message': 'Evaluating responses...'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(user_message, stage1_results)
            yield f"data: {json.dumps({'type': 'stage2_complete'})}\n\n"

            # Stage 3
            yield f"data: {json.dumps({'type': 'status', 'message': 'Synthesizing final answer...'})}\n\n"
            stage3_result = await stage3_synthesize_final(user_message, stage1_results, stage2_results)

            # Build response
            sources = [
                {"source": c.get("source", "Unknown"), "excerpt": c.get("content", "")[:200]}
                for c in context_chunks
            ]

            storage.add_assistant_message(session_id, stage1_results, stage2_results, stage3_result)

            yield f"data: {json.dumps({'type': 'complete', 'data': {'answer': stage3_result.get('response', ''), 'sources': sources, 'session_id': session_id}})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


# ============================================================
# Health Check
# ============================================================

@app.get("/")
async def root():
    return {"status": "ok", "service": "ThaiLawOnline Chatbot API"}


@app.get("/health")
async def health():
    return {"status": "ok"}


# ============================================================
# Original Council Endpoints (kept for direct council UI usage)
# ============================================================

@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    is_first_message = len(conversation["messages"]) == 0
    storage.add_user_message(conversation_id, request.content)

    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Use RAG-augmented council for legal queries
    messages, _ = await retrieve_and_build_messages(request.content)
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content, messages=messages
    )

    storage.add_assistant_message(conversation_id, stage1_results, stage2_results, stage3_result)

    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata,
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    is_first_message = len(conversation["messages"]) == 0

    async def event_generator():
        try:
            storage.add_user_message(conversation_id, request.content)

            title_task = None
            if is_first_message:
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # RAG retrieval
            yield f"data: {json.dumps({'type': 'rag_start'})}\n\n"
            messages, _ = await retrieve_and_build_messages(request.content)
            yield f"data: {json.dumps({'type': 'rag_complete'})}\n\n"

            # Stage 1
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"
            stage1_results = await stage1_collect_responses(request.content, messages=messages)
            yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"

            # Stage 2
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"
            stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results)
            aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
            yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"

            # Stage 3
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"
            stage3_result = await stage3_synthesize_final(request.content, stage1_results, stage2_results)
            yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"

            if title_task:
                title = await title_task
                storage.update_conversation_title(conversation_id, title)
                yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"

            storage.add_assistant_message(conversation_id, stage1_results, stage2_results, stage3_result)
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
