"""
Agent state schema for LangGraph.
Defines the shared state passed between agents.
"""

from datetime import datetime
from typing import Annotated, Dict, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state for agent graph.
    Passed between all nodes in the workflow.
    """
    # User context
    user_id: str
    session_id: str

    # Messages (LangGraph managed)
    messages: Annotated[list, add_messages]

    # Current query
    query: str
    query_intent: List[str]

    # Memory context
    long_term_context: str
    short_term_context: str
    working_context: str

    # RAG context
    retrieved_docs: List[Dict]

    # Routing
    selected_agents: List[str]
    current_agent: Optional[str]

    # Model selection (auto-routed based on query complexity)
    model: str

    # Response accumulation
    agent_responses: Dict[str, str]
    final_response: Optional[str]

    # Metadata
    timestamp: str
    turn_count: int


def create_initial_state(
    user_id: str,
    session_id: str,
    query: str
) -> AgentState:
    """
    Create initial state for a new query.

    Args:
        user_id: User identifier.
        session_id: Session identifier.
        query: User's query.

    Returns:
        Initial AgentState.
    """
    return AgentState(
        user_id=user_id,
        session_id=session_id,
        messages=[],
        query=query,
        query_intent=[],
        long_term_context="",
        short_term_context="",
        working_context="",
        retrieved_docs=[],
        selected_agents=[],
        current_agent=None,
        model="claude-sonnet-4-20250514",  # Default, will be updated by model router
        agent_responses={},
        final_response=None,
        timestamp=datetime.utcnow().isoformat(),
        turn_count=0
    )
