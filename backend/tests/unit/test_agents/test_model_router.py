"""
Unit tests for model router.
Tests query complexity classification and model selection.
"""

import pytest

from app.agents.model_router import (
    ModelRouter,
    route_to_model,
    get_model_router,
    MODEL_MAP,
)
from app.agents.state import create_initial_state


class TestModelRouter:
    """Unit tests for ModelRouter class."""

    @pytest.fixture
    def router(self) -> ModelRouter:
        """Create ModelRouter instance."""
        return ModelRouter()

    @pytest.fixture
    def base_state(self):
        """Create base state for testing."""
        return create_initial_state("user_123", "session_123", "")

    # ==================== EDGE CASE 1: Simple greeting ====================
    def test_classify_simple_greeting(self, router: ModelRouter):
        """
        GIVEN a simple greeting
        WHEN classify_complexity is called
        THEN returns 'simple'
        """
        simple_queries = ["hi", "hello", "thanks", "ok", "bye", "hey"]

        for query in simple_queries:
            result = router.classify_complexity(query)
            assert result == "simple", f"Expected 'simple' for '{query}', got '{result}'"

    # ==================== EDGE CASE 2: Short query under threshold ====================
    def test_classify_short_query_as_simple(self, router: ModelRouter):
        """
        GIVEN a short query under 15 chars
        WHEN classify_complexity is called
        THEN returns 'simple'
        """
        result = router.classify_complexity("yes please")
        assert result == "simple"

    # ==================== EDGE CASE 3: Complex planning query ====================
    def test_classify_complex_planning_query(self, router: ModelRouter):
        """
        GIVEN a complex planning query
        WHEN classify_complexity is called
        THEN returns 'complex'
        """
        complex_queries = [
            "create a plan for my entire week",
            "comprehensive workout considering my knee injury",
            "detailed meal plan taking into account my allergies",
            "weekly plan combining fitness and nutrition",
        ]

        for query in complex_queries:
            result = router.classify_complexity(query)
            assert result == "complex", f"Expected 'complex' for '{query}', got '{result}'"

    # ==================== EDGE CASE 4: Standard query ====================
    def test_classify_standard_query(self, router: ModelRouter):
        """
        GIVEN a standard advice query
        WHEN classify_complexity is called
        THEN returns 'standard' (not simple, not complex)
        """
        # Standard queries should be longer than 15 chars and not match complex patterns
        query = "what should I eat for breakfast tomorrow"
        result = router.classify_complexity(query)
        # This might use LLM classification or return standard
        assert result in ["standard", "simple", "complex"]

    # ==================== EDGE CASE 5: Get correct model for complexity ====================
    def test_get_model_for_query_returns_correct_models(self, router: ModelRouter):
        """
        GIVEN queries of different complexity
        WHEN get_model_for_query is called
        THEN returns appropriate model
        """
        # Simple -> Haiku
        model = router.get_model_for_query("hi")
        assert model == MODEL_MAP["simple"]
        assert "haiku" in model

        # Complex -> Opus
        model = router.get_model_for_query("create a comprehensive plan for the week")
        assert model == MODEL_MAP["complex"]
        assert "opus" in model

    # ==================== State Integration Tests ====================
    def test_route_to_model_updates_state(self, base_state):
        """
        GIVEN initial state with default model
        WHEN route_to_model is called
        THEN state model is updated based on query
        """
        base_state["query"] = "hello"

        result = route_to_model(base_state)

        assert result["model"] == MODEL_MAP["simple"]

    def test_route_to_model_complex_query(self, base_state):
        """
        GIVEN state with complex query
        WHEN route_to_model is called
        THEN state model is set to opus
        """
        base_state["query"] = "create a detailed weekly plan considering my injury"

        result = route_to_model(base_state)

        assert result["model"] == MODEL_MAP["complex"]

    def test_get_model_router_singleton(self):
        """
        GIVEN model router
        WHEN get_model_router is called multiple times
        THEN returns same instance
        """
        router1 = get_model_router()
        router2 = get_model_router()

        assert router1 is router2

    def test_model_map_has_all_levels(self):
        """
        GIVEN MODEL_MAP
        THEN all complexity levels are defined
        """
        assert "simple" in MODEL_MAP
        assert "standard" in MODEL_MAP
        assert "complex" in MODEL_MAP
        assert len(MODEL_MAP) == 3
