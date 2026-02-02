"""
Model router for automatic model selection based on query complexity.
Uses Haiku for fast classification to determine optimal model.
"""

from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.core.config import get_settings


# Fast classification prompt (~50 tokens)
COMPLEXITY_PROMPT = """Classify this query's complexity as SIMPLE, STANDARD, or COMPLEX:

- SIMPLE: greetings, thanks, acknowledgments, yes/no questions, single-word responses
- STANDARD: specific advice requests, single-topic questions, routine guidance
- COMPLEX: multi-part questions, detailed planning, analysis across domains, comprehensive plans

Query: "{query}"

Classification (respond with one word only):"""

# Model mapping
MODEL_MAP = {
    "simple": "claude-3-haiku-20240307",
    "standard": "claude-sonnet-4-20250514",
    "complex": "claude-opus-4-20250514",
}

ComplexityLevel = Literal["simple", "standard", "complex"]


class ModelRouter:
    """
    Routes queries to appropriate model based on complexity.
    Uses Haiku for fast classification.
    """

    def __init__(self):
        """Initialize model router with Haiku classifier."""
        self._classifier = None

    @property
    def classifier(self) -> ChatAnthropic:
        """Lazy load Haiku classifier."""
        if self._classifier is None:
            settings = get_settings()
            self._classifier = ChatAnthropic(
                model="claude-3-haiku-20240307",
                api_key=settings.anthropic_api_key,
                max_tokens=10,
                temperature=0.0,
            )
        return self._classifier

    def classify_complexity(self, query: str) -> ComplexityLevel:
        """
        Classify query complexity.

        Args:
            query: User query to classify.

        Returns:
            Complexity level: simple, standard, or complex.
        """
        # Quick pattern matching for obvious cases
        query_lower = query.strip().lower()

        # Simple patterns - greetings, thanks, short acknowledgments
        simple_patterns = [
            "hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye",
            "ok", "okay", "yes", "no", "sure", "cool", "great", "nice",
            "good morning", "good night", "good evening", "how are you",
        ]

        if query_lower in simple_patterns or len(query_lower) < 15:
            return "simple"

        # Complex patterns - multi-topic, planning keywords
        complex_patterns = [
            "create a plan", "weekly plan", "full week", "detailed",
            "comprehensive", "considering my", "taking into account",
            "multiple", "combining", "both fitness and nutrition",
        ]

        if any(pattern in query_lower for pattern in complex_patterns):
            return "complex"

        # For ambiguous cases, use Haiku classifier
        try:
            messages = [
                SystemMessage(content="You are a query classifier. Respond with only one word: SIMPLE, STANDARD, or COMPLEX."),
                HumanMessage(content=COMPLEXITY_PROMPT.format(query=query)),
            ]

            response = self.classifier.invoke(messages)
            classification = response.content.strip().upper()

            if "SIMPLE" in classification:
                return "simple"
            elif "COMPLEX" in classification:
                return "complex"
            else:
                return "standard"

        except Exception:
            # Default to standard if classification fails
            return "standard"

    def get_model_for_query(self, query: str) -> str:
        """
        Get appropriate model for a query.

        Args:
            query: User query.

        Returns:
            Model name string.
        """
        complexity = self.classify_complexity(query)
        return MODEL_MAP[complexity]


# Global router instance
_router = None


def get_model_router() -> ModelRouter:
    """Get or create model router singleton."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router


def route_to_model(state: AgentState) -> AgentState:
    """
    Route query to appropriate model.
    Used as a LangGraph node.

    Args:
        state: Current agent state.

    Returns:
        Updated state with selected model.
    """
    router = get_model_router()
    query = state.get("query", "")

    model = router.get_model_for_query(query)
    state["model"] = model

    return state
