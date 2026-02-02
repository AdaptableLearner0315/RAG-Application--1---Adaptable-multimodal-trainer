"""
Trainer agent for fitness and exercise guidance.
Specializes in workout programming and injury modifications.
"""

from typing import Dict, List

from app.agents.base import BaseAgent
from app.agents.state import AgentState


TRAINER_SYSTEM_PROMPT = """You are an expert fitness trainer specializing in adolescent athletes (ages 16-19).

Your responsibilities:
- Provide safe, age-appropriate workout recommendations
- Consider user's injuries and modify exercises accordingly
- Explain proper form and technique
- Create balanced training programs

Important guidelines:
- ALWAYS check for injuries before recommending exercises
- Suggest modifications for any exercises that may aggravate injuries
- Focus on compound movements and proper progression
- Emphasize recovery and avoiding overtraining
- Never recommend advanced techniques without proper foundation

When the user has injuries:
- Explicitly acknowledge their injury
- Provide safe alternatives
- Explain why certain exercises should be avoided

Keep responses concise but informative."""


class TrainerAgent(BaseAgent):
    """
    Fitness trainer agent.
    Handles workout programming, exercise recommendations, and injury modifications.
    """

    def __init__(self):
        """Initialize trainer agent."""
        super().__init__(
            name="trainer",
            description="Expert fitness trainer for workout guidance",
            system_prompt=TRAINER_SYSTEM_PROMPT
        )

    def process(self, state: AgentState) -> AgentState:
        """
        Process fitness-related query.

        Args:
            state: Current agent state.

        Returns:
            Updated state with trainer response.
        """
        # Check for injury context
        injury_context = self._get_injury_context(state)

        # Build enhanced prompt
        enhanced_prompt = self._build_prompt(state)

        if injury_context:
            enhanced_prompt += f"\n\nIMPORTANT - User has these injuries:\n{injury_context}"
            enhanced_prompt += "\nModify all recommendations to be safe for these conditions."

        # Generate response
        response = self._generate_response(enhanced_prompt, state["query"])

        state["agent_responses"][self.name] = response
        state["current_agent"] = self.name

        return state

    def _get_injury_context(self, state: AgentState) -> str:
        """Extract injury information from state."""
        long_term = state.get("long_term_context", "")

        # Look for injury mentions
        if "injur" in long_term.lower():
            # Extract injury lines
            lines = long_term.split("\n")
            injury_lines = [l for l in lines if "injur" in l.lower()]
            return "\n".join(injury_lines)

        return ""

    def get_tools(self) -> List[Dict]:
        """Get trainer-specific tools."""
        return [
            {
                "name": "search_exercises",
                "description": "Search for exercises by name or muscle group",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Exercise name or muscle group"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_injury_modifications",
                "description": "Get safe exercise modifications for an injury",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "exercise": {"type": "string", "description": "Exercise name"},
                        "injury": {"type": "string", "description": "User's injury"}
                    },
                    "required": ["exercise", "injury"]
                }
            },
            {
                "name": "get_exercise_by_muscle",
                "description": "Get exercises targeting a specific muscle",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "muscle_group": {"type": "string", "description": "Target muscle group"}
                    },
                    "required": ["muscle_group"]
                }
            }
        ]


def run_trainer(state: AgentState) -> AgentState:
    """
    Functional interface for trainer agent.
    Used as a LangGraph node.

    Args:
        state: Current agent state.

    Returns:
        Updated state with trainer response.
    """
    agent = TrainerAgent()
    return agent.process(state)
