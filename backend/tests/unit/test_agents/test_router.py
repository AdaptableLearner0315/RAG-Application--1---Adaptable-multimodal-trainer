"""
Unit tests for agent router.
Tests 5 edge cases for query routing.
"""

import pytest

from app.agents.router import QueryRouter, route_query
from app.agents.state import create_initial_state


class TestQueryRouter:
    """Unit tests for QueryRouter class."""

    @pytest.fixture
    def router(self) -> QueryRouter:
        """Create QueryRouter instance."""
        return QueryRouter()

    @pytest.fixture
    def base_state(self):
        """Create base state for testing."""
        return create_initial_state("user_123", "session_123", "")

    # ==================== EDGE CASE 1: Single domain query ====================
    def test_route_fitness_query_to_trainer(self, router: QueryRouter, base_state):
        """
        GIVEN clear fitness query
        WHEN route() is called
        THEN only trainer agent is selected
        """
        base_state["query"] = "how many sets should I do for biceps?"

        result = router.route(base_state)

        assert "trainer" in result["selected_agents"]
        assert len(result["selected_agents"]) == 1

    # ==================== EDGE CASE 2: Multi-domain query ====================
    def test_route_complex_query_to_multiple(self, router: QueryRouter, base_state):
        """
        GIVEN query spanning nutrition and fitness
        WHEN route() is called
        THEN multiple relevant agents are selected
        """
        base_state["query"] = "what should I eat before my workout at the gym?"

        result = router.route(base_state)

        assert "trainer" in result["selected_agents"]
        assert "nutritionist" in result["selected_agents"]

    # ==================== EDGE CASE 3: Off-topic query ====================
    def test_route_offtopic_returns_empty(self, router: QueryRouter, base_state):
        """
        GIVEN non-health-related query
        WHEN route() is called
        THEN no agents selected, polite message returned
        """
        base_state["query"] = "what's the capital of France?"

        result = router.route(base_state)

        assert result["selected_agents"] == []
        assert result["final_response"] is not None
        assert "health" in result["final_response"].lower() or "fitness" in result["final_response"].lower()

    # ==================== EDGE CASE 4: Harmful query ====================
    def test_route_harmful_query_blocked(self, router: QueryRouter, base_state):
        """
        GIVEN query with harmful intent
        WHEN route() is called
        THEN no agents selected, safety message returned
        """
        base_state["query"] = "how to lose 20 pounds in one week"

        result = router.route(base_state)

        assert result["selected_agents"] == []
        assert result["final_response"] is not None
        assert "healthcare" in result["final_response"].lower() or "professional" in result["final_response"].lower()

    # ==================== EDGE CASE 5: Ambiguous general query ====================
    def test_route_general_query_to_all(self, router: QueryRouter, base_state):
        """
        GIVEN general/ambiguous health query
        WHEN route() is called
        THEN all agents are selected
        """
        base_state["query"] = "how can I feel better overall?"

        result = router.route(base_state)

        assert len(result["selected_agents"]) == 3
        assert "trainer" in result["selected_agents"]
        assert "nutritionist" in result["selected_agents"]
        assert "recovery" in result["selected_agents"]

    # ==================== Additional Tests ====================
    def test_route_nutrition_query(self, router: QueryRouter, base_state):
        """Test routing nutrition query to nutritionist."""
        base_state["query"] = "how many calories should I eat?"

        result = router.route(base_state)

        assert "nutritionist" in result["selected_agents"]

    def test_route_sleep_query(self, router: QueryRouter, base_state):
        """Test routing sleep query to recovery coach."""
        base_state["query"] = "I'm so tired, how much sleep do I need?"

        result = router.route(base_state)

        assert "recovery" in result["selected_agents"]

    def test_classify_intent_multiple(self, router: QueryRouter):
        """Test classifying query with multiple intents."""
        intents = router.classify_intent("I need to eat more protein and train legs")

        assert any(i in intents for i in ["protein", "eat"])
        assert any(i in intents for i in ["train", "legs"])

    def test_route_query_function(self, base_state):
        """Test functional route_query interface."""
        base_state["query"] = "best exercises for chest?"

        result = route_query(base_state)

        assert "trainer" in result["selected_agents"]

    def test_harmful_patterns_detected(self, router: QueryRouter):
        """Test that various harmful patterns are detected."""
        harmful_queries = [
            "how to starve myself",
            "anorexia tips",
            "extreme diet for fast weight loss"
        ]

        for query in harmful_queries:
            assert router._is_harmful(query.lower())

    def test_off_topic_patterns_detected(self, router: QueryRouter):
        """Test that off-topic patterns are detected."""
        off_topic_queries = [
            "what's the weather today",
            "who is the president",
            "tell me about game of thrones"
        ]

        for query in off_topic_queries:
            assert router._is_off_topic(query.lower())
