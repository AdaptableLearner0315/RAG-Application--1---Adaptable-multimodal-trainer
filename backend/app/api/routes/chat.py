"""
Chat endpoint for the Adaptive Coaching Platform.
Handles text-based conversations with the multi-agent system.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.api.deps import (
    get_memory_retriever,
    get_long_term_store,
    get_working_store,
    validate_user_id,
    validate_session_id
)
from app.agents.graph import run_agent_workflow
from app.input.text import TextProcessor, SafetyCheckResult

router = APIRouter()


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4096, description="User message")
    user_id: str = Field(..., description="Unique user identifier")
    session_id: Optional[str] = Field(default=None, description="Session ID (auto-generated if not provided)")
    image_base64: Optional[str] = Field(default=None, description="Optional food image in base64")


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    response: str = Field(..., description="Agent response")
    agent: str = Field(..., description="Primary agent that responded")
    session_id: str = Field(..., description="Session ID")
    sources: Optional[List[str]] = Field(default=None, description="RAG sources used")
    memory_updated: bool = Field(default=False, description="Whether memory was updated")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message through the multi-agent system.

    Args:
        request: Chat request with message, user_id, and optional image.

    Returns:
        ChatResponse with agent response and metadata.

    Raises:
        HTTPException: If message fails safety check or processing fails.
    """
    # Validate inputs
    try:
        user_id = validate_user_id(request.user_id)
        session_id = request.session_id or str(uuid.uuid4())
        session_id = validate_session_id(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Safety check
    text_processor = TextProcessor()
    safety_result = text_processor.check_safety(request.message)

    if not safety_result.is_safe:
        raise HTTPException(
            status_code=400,
            detail=f"Message blocked: {safety_result.reason}"
        )

    # Check if user has profile
    long_term_store = get_long_term_store()
    profile = long_term_store.get(user_id)

    if profile is None:
        # New user - return onboarding prompt
        return ChatResponse(
            response=(
                "Welcome! I'm your personal coaching assistant. "
                "Before we get started, I'd like to learn a bit about you. "
                "Could you tell me your age, height, weight, and primary fitness goal? "
                "Also, do you have any food allergies, intolerances, or injuries I should know about?"
            ),
            agent="system",
            session_id=session_id,
            memory_updated=False
        )

    # Get memory context
    retriever = get_memory_retriever()
    memory_context = retriever.retrieve_for_query(user_id, request.message)

    # Update working memory with this message
    working_store = get_working_store()
    working_store.add_message(
        user_id=user_id,
        session_id=session_id,
        role="user",
        content=request.message
    )

    # Run agent workflow
    try:
        response = await run_agent_workflow(
            user_id=user_id,
            session_id=session_id,
            query=request.message,
            memory_context=memory_context
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )

    # Store assistant response in working memory
    working_store.add_message(
        user_id=user_id,
        session_id=session_id,
        role="assistant",
        content=response
    )

    # Determine primary agent from response
    agent = "coach"
    if "**Fitness" in response:
        agent = "trainer"
    elif "**Nutrition" in response:
        agent = "nutritionist"
    elif "**Recovery" in response:
        agent = "recovery"

    return ChatResponse(
        response=response,
        agent=agent,
        session_id=session_id,
        memory_updated=True
    )


@router.get("/chat/health")
async def health_check() -> dict:
    """
    Health check endpoint for chat service.

    Returns:
        Status dict.
    """
    return {"status": "healthy", "service": "chat"}
