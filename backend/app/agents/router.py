"""
Query router for agent selection.
Determines which agent(s) should handle a query.
"""

import re
from typing import List

from app.agents.state import AgentState


# Intent to agent mapping
INTENT_AGENT_MAP = {
    "workout": "trainer",
    "exercise": "trainer",
    "training": "trainer",
    "gym": "trainer",
    "strength": "trainer",
    "cardio": "trainer",
    "lift": "trainer",
    "muscle": "trainer",

    "food": "nutritionist",
    "meal": "nutritionist",
    "eat": "nutritionist",
    "diet": "nutritionist",
    "nutrition": "nutritionist",
    "calories": "nutritionist",
    "protein": "nutritionist",
    "carbs": "nutritionist",
    "macro": "nutritionist",

    "sleep": "recovery",
    "rest": "recovery",
    "recovery": "recovery",
    "tired": "recovery",
    "fatigue": "recovery",
    "energy": "recovery",
    "soreness": "recovery"
}

# Off-topic keywords
OFF_TOPIC_PATTERNS = [
    r"weather",
    r"politics",
    r"news",
    r"movie",
    r"game\s+of\s+thrones",
    r"capital\s+of",
    r"president",
    r"who\s+is\s+\w+\s+\w+$"  # "Who is [name]" patterns
]

# Harmful query patterns
HARMFUL_PATTERNS = [
    r"how\s+to\s+(starve|purge)",
    r"(anorexia|bulimia)",
    r"extreme\s+diet",
    r"steroids?",
    r"lose\s+\d+\s+pounds?\s+in\s+(one|two|\d)\s+(day|week)"
]


class QueryRouter:
    """
    Route queries to appropriate agent(s).
    Handles multi-domain queries and safety checks.
    """

    def __init__(self):
        """Initialize query router."""
        self.off_topic_regex = [
            re.compile(p, re.IGNORECASE) for p in OFF_TOPIC_PATTERNS
        ]
        self.harmful_regex = [
            re.compile(p, re.IGNORECASE) for p in HARMFUL_PATTERNS
        ]

    def route(self, state: AgentState) -> AgentState:
        """
        Determine which agents should handle the query.

        Args:
            state: Current agent state.

        Returns:
            Updated state with selected_agents populated.
        """
        query = state["query"].lower()

        # Check for harmful queries
        if self._is_harmful(query):
            state["selected_agents"] = []
            state["final_response"] = (
                "I'm not able to provide advice on that topic. "
                "Please consult a healthcare professional for guidance."
            )
            return state

        # Check for off-topic queries
        if self._is_off_topic(query):
            state["selected_agents"] = []
            state["final_response"] = (
                "I'm your health and fitness coach, so I can help with "
                "nutrition, workouts, and recovery. What would you like to know?"
            )
            return state

        # Extract intents and map to agents
        agents = self._extract_agents(query)

        # If no specific agents, return all for general query
        if not agents:
            agents = ["trainer", "nutritionist", "recovery"]

        state["selected_agents"] = agents
        state["query_intent"] = list(set(
            intent for intent, agent in INTENT_AGENT_MAP.items()
            if agent in agents and intent in query
        ))

        return state

    def _is_harmful(self, query: str) -> bool:
        """Check if query contains harmful patterns."""
        return any(p.search(query) for p in self.harmful_regex)

    def _is_off_topic(self, query: str) -> bool:
        """Check if query is off-topic."""
        return any(p.search(query) for p in self.off_topic_regex)

    def _extract_agents(self, query: str) -> List[str]:
        """Extract relevant agents based on query keywords."""
        agents = set()

        for keyword, agent in INTENT_AGENT_MAP.items():
            if keyword in query:
                agents.add(agent)

        return list(agents)

    def classify_intent(self, query: str) -> List[str]:
        """
        Classify query intent without full routing.

        Args:
            query: User query.

        Returns:
            List of intent categories.
        """
        query_lower = query.lower()
        intents = []

        for keyword, agent in INTENT_AGENT_MAP.items():
            if keyword in query_lower:
                intents.append(keyword)

        return list(set(intents))


def route_query(state: AgentState) -> AgentState:
    """
    Functional interface for routing.
    Used as a LangGraph node.

    Args:
        state: Current agent state.

    Returns:
        Updated state with routing decisions.
    """
    router = QueryRouter()
    return router.route(state)
