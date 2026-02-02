"""
Recovery coach agent for sleep and rest guidance.
Specializes in recovery optimization and fatigue management.
"""

from typing import Dict, List

from app.agents.base import BaseAgent
from app.agents.state import AgentState


RECOVERY_SYSTEM_PROMPT = """You are a recovery specialist for adolescent athletes (ages 16-19).

Your responsibilities:
- Provide sleep optimization guidance
- Recommend rest and recovery strategies
- Assess fatigue levels and suggest adjustments
- Connect recovery to training performance

Important guidelines:
- Adolescents need 8-10 hours of sleep for optimal development
- Consider recent workout intensity when recommending rest
- Emphasize the importance of recovery for muscle growth
- Watch for signs of overtraining

When assessing recovery needs:
- Check recent workout history
- Consider sleep patterns
- Account for life stressors (school, exams, etc.)

Keep responses supportive and practical."""


class RecoveryCoachAgent(BaseAgent):
    """
    Recovery coach agent.
    Handles sleep optimization, rest recommendations, and fatigue assessment.
    """

    def __init__(self):
        """Initialize recovery coach agent."""
        super().__init__(
            name="recovery",
            description="Recovery specialist for sleep and rest optimization",
            system_prompt=RECOVERY_SYSTEM_PROMPT
        )

    def process(self, state: AgentState) -> AgentState:
        """
        Process recovery-related query.

        Args:
            state: Current agent state.

        Returns:
            Updated state with recovery coach response.
        """
        # Get recent activity context
        activity_context = self._get_activity_context(state)

        # Build enhanced prompt
        enhanced_prompt = self._build_prompt(state)

        if activity_context:
            enhanced_prompt += f"\n\nRECENT ACTIVITY:\n{activity_context}"
            enhanced_prompt += "\nConsider this activity level when making recommendations."

        # Generate response
        response = self._generate_response(enhanced_prompt, state["query"])

        state["agent_responses"][self.name] = response
        state["current_agent"] = self.name

        return state

    def _get_activity_context(self, state: AgentState) -> str:
        """Extract recent activity from state."""
        short_term = state.get("short_term_context", "")

        # Look for workout and sleep mentions
        relevant_lines = []
        for line in short_term.split("\n"):
            line_lower = line.lower()
            if any(kw in line_lower for kw in ["workout", "sleep", "exercise", "training"]):
                relevant_lines.append(line.strip())

        return "\n".join(relevant_lines) if relevant_lines else ""

    def get_tools(self) -> List[Dict]:
        """Get recovery coach-specific tools."""
        return [
            {
                "name": "get_user_sleep_history",
                "description": "Get user's recent sleep patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"},
                        "days": {"type": "integer", "description": "Days to look back"}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "assess_recovery_needs",
                "description": "Assess recovery needs based on recent activity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier"}
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "get_recovery_protocol",
                "description": "Get recovery protocol for activity type",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "activity_type": {"type": "string", "description": "Type of activity"},
                        "intensity": {"type": "string", "description": "Workout intensity"}
                    },
                    "required": ["activity_type"]
                }
            }
        ]


def run_recovery_coach(state: AgentState) -> AgentState:
    """
    Functional interface for recovery coach agent.
    Used as a LangGraph node.

    Args:
        state: Current agent state.

    Returns:
        Updated state with recovery coach response.
    """
    agent = RecoveryCoachAgent()
    return agent.process(state)
