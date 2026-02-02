"""
LangGraph workflow for multi-agent orchestration.
Defines the agent graph and execution flow.
"""

from typing import Literal

from langgraph.graph import END, StateGraph

from app.agents.state import AgentState, create_initial_state
from app.agents.router import route_query
from app.agents.trainer import run_trainer
from app.agents.nutritionist import run_nutritionist
from app.agents.recovery import run_recovery_coach
from app.agents.model_router import route_to_model


def should_continue(state: AgentState) -> Literal["continue", "end"]:
    """
    Determine if we should continue to agents or end.

    Args:
        state: Current agent state.

    Returns:
        "continue" or "end".
    """
    # If router set a final response (harmful/off-topic), end
    if state.get("final_response"):
        return "end"

    # If no agents selected, end
    if not state.get("selected_agents"):
        return "end"

    return "continue"


def select_next_agent(state: AgentState) -> str:
    """
    Select the next agent to run.

    Args:
        state: Current agent state.

    Returns:
        Agent name to run next.
    """
    selected = state.get("selected_agents", [])
    responded = set(state.get("agent_responses", {}).keys())

    # Find first agent that hasn't responded
    for agent in selected:
        if agent not in responded:
            return agent

    return "merge"


def merge_responses(state: AgentState) -> AgentState:
    """
    Merge responses from multiple agents.

    Args:
        state: Current agent state.

    Returns:
        Updated state with final response.
    """
    responses = state.get("agent_responses", {})

    if not responses:
        state["final_response"] = "I'm not sure how to help with that."
        return state

    if len(responses) == 1:
        # Single agent response
        state["final_response"] = list(responses.values())[0]
    else:
        # Multiple agent responses - combine them
        combined = []

        if "trainer" in responses:
            combined.append(f"**Fitness Perspective:**\n{responses['trainer']}")

        if "nutritionist" in responses:
            combined.append(f"**Nutrition Perspective:**\n{responses['nutritionist']}")

        if "recovery" in responses:
            combined.append(f"**Recovery Perspective:**\n{responses['recovery']}")

        state["final_response"] = "\n\n".join(combined)

    return state


def build_agent_graph() -> StateGraph:
    """
    Build the LangGraph workflow.

    Returns:
        Compiled StateGraph.
    """
    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("model_router", route_to_model)
    workflow.add_node("router", route_query)
    workflow.add_node("trainer", run_trainer)
    workflow.add_node("nutritionist", run_nutritionist)
    workflow.add_node("recovery", run_recovery_coach)
    workflow.add_node("merge", merge_responses)

    # Set entry point - model routing first
    workflow.set_entry_point("model_router")

    # Model router always goes to agent router
    workflow.add_edge("model_router", "router")

    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        should_continue,
        {
            "continue": "agent_selector",
            "end": END
        }
    )

    # Add agent selector node
    def agent_selector_node(state: AgentState) -> AgentState:
        """Dummy node for routing to agents."""
        return state

    workflow.add_node("agent_selector", agent_selector_node)

    # Route to appropriate agent
    workflow.add_conditional_edges(
        "agent_selector",
        select_next_agent,
        {
            "trainer": "trainer",
            "nutritionist": "nutritionist",
            "recovery": "recovery",
            "merge": "merge"
        }
    )

    # After each agent, go back to selector or merge
    for agent in ["trainer", "nutritionist", "recovery"]:
        workflow.add_conditional_edges(
            agent,
            select_next_agent,
            {
                "trainer": "trainer",
                "nutritionist": "nutritionist",
                "recovery": "recovery",
                "merge": "merge"
            }
        )

    # Merge ends the graph
    workflow.add_edge("merge", END)

    return workflow.compile()


# Global compiled graph
_graph = None


def get_agent_graph() -> StateGraph:
    """Get or create the agent graph singleton."""
    global _graph
    if _graph is None:
        _graph = build_agent_graph()
    return _graph


async def run_agent_workflow(
    user_id: str,
    session_id: str,
    query: str,
    memory_context: dict = None
) -> str:
    """
    Run the agent workflow for a query.

    Args:
        user_id: User identifier.
        session_id: Session identifier.
        query: User query.
        memory_context: Optional memory context dict.

    Returns:
        Final response string.
    """
    # Create initial state
    state = create_initial_state(user_id, session_id, query)

    # Add memory context if provided
    if memory_context:
        state["long_term_context"] = memory_context.get("long_term", "")
        state["short_term_context"] = memory_context.get("short_term", "")
        state["working_context"] = memory_context.get("working", "")

    # Run graph
    graph = get_agent_graph()
    result = await graph.ainvoke(state)

    return result.get("final_response", "I'm not sure how to help with that.")
