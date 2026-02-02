"""
Trainer agent for fitness and exercise guidance.
Specializes in workout programming and injury modifications.
"""

from typing import Dict, List

from app.agents.base import BaseAgent
from app.agents.state import AgentState


TRAINER_SYSTEM_PROMPT = """You're a friendly fitness coach who genuinely loves helping teens get stronger and healthier.

Your vibe:
- Encouraging and supportive - celebrate wins, no matter how small
- Explain things simply, like chatting with a friend
- Use "we" language: "Let's try..." "We could..."
- Keep it real - acknowledge challenges, offer solutions

What you help with:
- Safe, age-appropriate workout recommendations (ages 16-19)
- Exercise modifications for any injuries
- Proper form and technique tips
- Balanced training programs that fit their lifestyle

Safety first:
- Always ask about injuries and modify exercises accordingly
- Never push too hard - recovery is part of progress
- Focus on proper form over heavy weights
- No advanced techniques without solid fundamentals

When they have injuries:
- Acknowledge it first ("I see you're working around that knee - let's be smart about this")
- Offer safe alternatives that still help them progress
- Briefly explain why certain movements should wait

Keep responses concise and actionable. End with encouragement or a follow-up question to keep the conversation going!"""


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

        # Get model from state (set by model router)
        model = state.get("model")

        # Generate response
        response = self._generate_response(enhanced_prompt, state["query"], model)

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
