"""
Query-aware memory retrieval.
Fetches relevant memory context based on query intent.
"""

import re
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.memory.long_term import LongTermMemoryStore
from app.memory.short_term import ShortTermMemoryStore
from app.memory.working import WorkingMemoryStore


# Query intent to memory field mappings
QUERY_MEMORY_MAP = {
    "workout|exercise|training|gym|lift|strength": {
        "long_term": ["injuries", "fitness_level", "primary_goal"],
        "short_term": ["workouts", "sleep"],
        "working": {"message_count": 3}
    },
    "food|meal|eat|nutrition|calories|diet|protein|carb": {
        "long_term": ["intolerances", "allergies", "dietary_pref", "primary_goal", "weight_kg", "target_weight_kg"],
        "short_term": ["meals", "calories_consumed", "protein_total"],
        "working": {"message_count": 3}
    },
    "sleep|tired|rest|recovery|fatigue|energy": {
        "long_term": ["fitness_level", "primary_goal"],
        "short_term": ["sleep", "workouts"],
        "working": {"message_count": 3}
    },
    "plan|week|schedule|program|routine": {
        "long_term": ["injuries", "fitness_level", "primary_goal", "dietary_pref", "intolerances"],
        "short_term": ["meals", "workouts", "sleep"],
        "working": {"message_count": 5}
    },
    "weight|progress|goal|target": {
        "long_term": ["weight_kg", "target_weight_kg", "primary_goal", "height_cm", "age"],
        "short_term": ["calories_consumed", "calories_burned"],
        "working": {"message_count": 3}
    }
}

DEFAULT_MEMORY_SPEC = {
    "long_term": ["primary_goal", "injuries", "intolerances"],
    "short_term": ["meals", "workouts"],
    "working": {"message_count": 3}
}


class MemoryRetriever:
    """
    Query-aware memory fetching.
    Retrieves only relevant memory sections based on query intent.
    """

    def __init__(
        self,
        working: WorkingMemoryStore,
        short_term: ShortTermMemoryStore,
        long_term: LongTermMemoryStore,
        token_budgets: Optional[Dict[str, int]] = None
    ):
        """
        Initialize memory retriever with all three memory stores.

        Args:
            working: Session-scoped memory store.
            short_term: 7-day rolling memory store.
            long_term: Permanent profile store.
            token_budgets: Max tokens per memory tier. Uses config defaults if None.
        """
        self.working = working
        self.short_term = short_term
        self.long_term = long_term

        settings = get_settings()
        self.budgets = token_budgets or {
            "working": settings.working_memory_budget,
            "short_term": settings.short_term_memory_budget,
            "long_term": settings.long_term_memory_budget
        }

    def retrieve_for_query(
        self,
        user_id: str,
        session_id: str,
        query: str
    ) -> Dict[str, str]:
        """
        Retrieve relevant memory context for a given query.

        Args:
            user_id: User identifier.
            session_id: Current session identifier.
            query: Raw user query text.

        Returns:
            Dict with keys 'long_term', 'short_term', 'working'.
            Each value is a formatted string within token budget.
        """
        intent = self._classify_intent(query)
        memory_spec = self._get_memory_spec(intent)

        context = {}

        # Fetch long-term (profile data)
        try:
            lt_fields = memory_spec["long_term"]
            context["long_term"] = self._fetch_long_term(user_id, lt_fields)
        except Exception:
            context["long_term"] = ""

        # Fetch short-term (recent activity)
        try:
            st_fields = memory_spec["short_term"]
            context["short_term"] = self._fetch_short_term(user_id, st_fields)
        except Exception:
            context["short_term"] = ""

        # Fetch working (conversation)
        try:
            msg_count = memory_spec["working"].get("message_count", 3)
            context["working"] = self._fetch_working(user_id, session_id, msg_count)
        except Exception:
            context["working"] = ""

        return context

    def _classify_intent(self, query: str) -> str:
        """
        Classify query intent using keyword matching.

        Args:
            query: Raw query text.

        Returns:
            Intent pattern string or 'general'.
        """
        query_lower = query.lower()

        for pattern in QUERY_MEMORY_MAP.keys():
            keywords = pattern.split("|")
            if any(kw in query_lower for kw in keywords):
                return pattern

        return "general"

    def _get_memory_spec(self, intent: str) -> Dict:
        """
        Get memory specification for intent.

        Args:
            intent: Query intent pattern.

        Returns:
            Memory field specification dict.
        """
        if intent == "general":
            return DEFAULT_MEMORY_SPEC

        # Check for multi-intent (query matches multiple patterns)
        matched_specs = []
        for pattern, spec in QUERY_MEMORY_MAP.items():
            if pattern == intent:
                matched_specs.append(spec)

        if not matched_specs:
            return DEFAULT_MEMORY_SPEC

        if len(matched_specs) == 1:
            return matched_specs[0]

        # Merge multiple specs
        merged = {
            "long_term": [],
            "short_term": [],
            "working": {"message_count": 3}
        }
        for spec in matched_specs:
            merged["long_term"].extend(spec.get("long_term", []))
            merged["short_term"].extend(spec.get("short_term", []))
            merged["working"]["message_count"] = max(
                merged["working"]["message_count"],
                spec.get("working", {}).get("message_count", 3)
            )

        # Dedupe
        merged["long_term"] = list(set(merged["long_term"]))
        merged["short_term"] = list(set(merged["short_term"]))

        return merged

    def _fetch_long_term(self, user_id: str, fields: List[str]) -> str:
        """
        Fetch and format long-term memory fields.

        Args:
            user_id: User identifier.
            fields: List of profile fields to include.

        Returns:
            Formatted string within token budget.
        """
        profile = self.long_term.get(user_id)
        if not profile:
            return ""

        data = profile.model_dump()
        selected = {f: data.get(f) for f in fields if f in data and data.get(f)}

        return self._format_memory(selected, self.budgets["long_term"])

    def _fetch_short_term(self, user_id: str, fields: List[str]) -> str:
        """
        Fetch and format short-term memory fields.

        Args:
            user_id: User identifier.
            fields: List of activity fields to include.

        Returns:
            Formatted string within token budget.
        """
        recent = self.short_term.get_recent(user_id, days=7)
        if not recent:
            return ""

        summary = {}

        for field in fields:
            if field == "meals":
                all_meals = []
                for day in recent[:3]:  # Last 3 days
                    for meal in day.meals:
                        all_meals.append(f"{day.date}: {', '.join(meal.foods)}")
                if all_meals:
                    summary["recent_meals"] = all_meals[:5]

            elif field == "workouts":
                all_workouts = []
                for day in recent[:3]:
                    for workout in day.workouts:
                        all_workouts.append(
                            f"{day.date}: {workout.type} ({workout.duration_min}min, {workout.intensity})"
                        )
                if all_workouts:
                    summary["recent_workouts"] = all_workouts[:5]

            elif field == "sleep":
                sleep_logs = []
                for day in recent[:3]:
                    if day.sleep:
                        sleep_logs.append(f"{day.date}: quality {day.sleep.quality}/5")
                if sleep_logs:
                    summary["recent_sleep"] = sleep_logs

            elif field == "calories_consumed":
                avg = sum(d.calories_consumed for d in recent) // len(recent) if recent else 0
                summary["avg_daily_calories"] = avg

            elif field == "protein_total":
                avg = sum(d.protein_total for d in recent) // len(recent) if recent else 0
                summary["avg_daily_protein"] = f"{avg}g"

            elif field == "calories_burned":
                avg = sum(d.calories_burned for d in recent) // len(recent) if recent else 0
                summary["avg_daily_burned"] = avg

        return self._format_memory(summary, self.budgets["short_term"])

    def _fetch_working(self, user_id: str, session_id: str, message_count: int) -> str:
        """
        Fetch recent conversation from working memory.

        Args:
            user_id: User identifier.
            session_id: Session identifier.
            message_count: Number of recent messages to include.

        Returns:
            Formatted conversation string within token budget.
        """
        messages = self.working.get_recent_messages(user_id, session_id, message_count)
        if not messages:
            return ""

        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role}: {content}")

        text = "\n".join(lines)
        return self._truncate_to_tokens(text, self.budgets["working"])

    def _format_memory(self, data: Dict, max_tokens: int) -> str:
        """
        Format memory dict as string, truncating to fit budget.

        Args:
            data: Memory data dictionary.
            max_tokens: Maximum token count.

        Returns:
            Formatted string within budget.
        """
        if not data:
            return ""

        lines = []
        for key, value in data.items():
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value[:5])  # Limit list items
            else:
                value_str = str(value)
            lines.append(f"- {key}: {value_str}")

        text = "\n".join(lines)
        return self._truncate_to_tokens(text, max_tokens)

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to approximate token count.

        Args:
            text: Input text.
            max_tokens: Maximum tokens (approx 4 chars/token).

        Returns:
            Truncated text.
        """
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 3] + "..."
