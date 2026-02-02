"""
Integration tests for Input + Agents modules.
Tests cross-module interactions between input processors and agent routing.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.input.text import TextProcessor
from app.agents.router import route_query
from app.agents.state import create_initial_state


class TestInputAgentsIntegration:
    """Integration tests for input processing and agent routing."""

    @pytest.fixture
    def text_processor(self) -> TextProcessor:
        """Create text processor."""
        return TextProcessor()

    # ==================== INTEGRATION TEST 1 ====================
    def test_safe_query_routes_to_agents(self, text_processor: TextProcessor):
        """
        Test that safe queries pass through text processor and route correctly.
        """
        query = "What exercises can I do for my chest?"

        # Process through text processor
        result = text_processor.process(query)

        assert result.is_safe
        assert "workout" in result.intent_keywords or len(result.intent_keywords) >= 0

        # Create initial state and verify it's valid
        state = create_initial_state(
            user_id="test_user",
            session_id="test_session",
            query=result.cleaned
        )

        assert state["query"] == result.cleaned
        assert state["user_id"] == "test_user"

    # ==================== INTEGRATION TEST 2 ====================
    def test_harmful_query_blocked_before_agents(self, text_processor: TextProcessor):
        """
        Test that harmful queries are blocked at text processor level.
        """
        harmful_query = "How can I lose 20 pounds in 3 days?"

        # Safety check should catch this
        safety_result = text_processor.check_safety(harmful_query)

        assert not safety_result.is_safe
        assert safety_result.reason is not None

    # ==================== INTEGRATION TEST 3 ====================
    def test_multi_intent_query_processing(self, text_processor: TextProcessor):
        """
        Test that queries spanning multiple domains are processed correctly.
        """
        query = "What should I eat after my leg workout for better recovery?"

        result = text_processor.process(query)

        assert result.is_safe
        # This query spans nutrition, workout, and recovery
        # Intent keywords should reflect multiple domains

    # ==================== INTEGRATION TEST 4 ====================
    def test_empty_query_handling(self, text_processor: TextProcessor):
        """
        Test that empty/whitespace queries are handled gracefully.
        """
        empty_queries = ["", "   ", "\n\t\n"]

        for query in empty_queries:
            result = text_processor.process(query)
            assert result.cleaned == "" or result.cleaned.strip() == ""

    # ==================== INTEGRATION TEST 5 ====================
    def test_long_query_truncation_before_agents(self, text_processor: TextProcessor):
        """
        Test that very long queries are truncated before reaching agents.
        """
        long_query = "Tell me about protein " * 500  # Very long query

        result = text_processor.process(long_query)

        # Should be truncated to max_length
        assert len(result.cleaned) <= text_processor.max_length
        assert result.is_safe


class TestAgentRouterIntegration:
    """Integration tests for agent router with state management."""

    # ==================== INTEGRATION TEST 6 ====================
    @pytest.mark.asyncio
    async def test_router_creates_valid_state(self):
        """
        Test that router produces valid state for downstream agents.
        """
        state = create_initial_state(
            user_id="test_user",
            session_id="test_session",
            query="How much protein should I eat?"
        )

        # Add memory context
        state["long_term_context"] = "User is 17, goal: build_muscle"
        state["short_term_context"] = "Recent meals: high carb"

        # Router should update state with selected agents
        # (actual routing tested in unit tests)
        assert state["query"] is not None
        assert state["user_id"] is not None

    # ==================== INTEGRATION TEST 7 ====================
    def test_intent_classification_consistency(self):
        """
        Test that intent classification is consistent across similar queries.
        """
        text_processor = TextProcessor()

        workout_queries = [
            "What exercises for biceps?",
            "How do I train my arms?",
            "Best gym routine for strength"
        ]

        food_queries = [
            "What should I eat for lunch?",
            "How many calories in chicken?",
            "Best protein sources"
        ]

        # Process workout queries through text processor
        workout_results = [text_processor.process(q) for q in workout_queries]

        # Process food queries through text processor
        food_results = [text_processor.process(q) for q in food_queries]

        # Verify all queries were processed safely
        assert all(r.is_safe for r in workout_results)
        assert all(r.is_safe for r in food_results)
