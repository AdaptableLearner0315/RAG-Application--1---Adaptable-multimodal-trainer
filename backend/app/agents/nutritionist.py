"""
Nutritionist agent for dietary guidance.
Specializes in meal planning and macro calculations.
"""

from typing import Dict, List

from app.agents.base import BaseAgent
from app.agents.state import AgentState


NUTRITIONIST_SYSTEM_PROMPT = """You are a registered dietitian specializing in adolescent nutrition (ages 16-19).

Your responsibilities:
- Provide personalized meal and nutrition guidance
- Calculate macro targets based on goals
- Suggest foods that meet dietary requirements
- Analyze food images when provided

Important guidelines:
- ALWAYS check for allergies and intolerances before suggesting foods
- Adolescents have higher protein and calcium needs for growth
- Focus on whole foods and balanced nutrition
- Never suggest extreme calorie restrictions
- Be aware of eating disorder warning signs

When the user has dietary restrictions:
- Never suggest foods that conflict with their restrictions
- Provide safe alternatives
- Explain nutritional substitutions

Keep responses practical and actionable."""


class NutritionistAgent(BaseAgent):
    """
    Nutritionist agent.
    Handles meal guidance, macro calculations, and food analysis.
    """

    def __init__(self):
        """Initialize nutritionist agent."""
        super().__init__(
            name="nutritionist",
            description="Registered dietitian for nutrition guidance",
            system_prompt=NUTRITIONIST_SYSTEM_PROMPT
        )

    def process(self, state: AgentState) -> AgentState:
        """
        Process nutrition-related query.

        Args:
            state: Current agent state.

        Returns:
            Updated state with nutritionist response.
        """
        # Get dietary restrictions
        restrictions = self._get_dietary_restrictions(state)

        # Build enhanced prompt
        enhanced_prompt = self._build_prompt(state)

        if restrictions:
            enhanced_prompt += f"\n\nDIETARY RESTRICTIONS (MUST AVOID):\n{restrictions}"
            enhanced_prompt += "\nNever suggest foods that conflict with these restrictions."

        # Generate response
        response = self._generate_response(enhanced_prompt, state["query"])

        state["agent_responses"][self.name] = response
        state["current_agent"] = self.name

        return state

    def _get_dietary_restrictions(self, state: AgentState) -> str:
        """Extract dietary restrictions from state."""
        long_term = state.get("long_term_context", "")
        restrictions = []

        # Look for intolerance/allergy mentions
        keywords = ["intoleran", "allerg", "avoid", "cannot eat", "dietary_pref"]
        for keyword in keywords:
            if keyword in long_term.lower():
                lines = long_term.split("\n")
                for line in lines:
                    if keyword in line.lower():
                        restrictions.append(line.strip())

        return "\n".join(restrictions) if restrictions else ""

    def get_tools(self) -> List[Dict]:
        """Get nutritionist-specific tools."""
        return [
            {
                "name": "search_usda",
                "description": "Search USDA database for food nutrition info",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "food_name": {"type": "string", "description": "Food to search for"}
                    },
                    "required": ["food_name"]
                }
            },
            {
                "name": "calculate_macros",
                "description": "Calculate daily macro targets",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "weight_kg": {"type": "number", "description": "Weight in kg"},
                        "height_cm": {"type": "number", "description": "Height in cm"},
                        "age": {"type": "integer", "description": "Age in years"},
                        "goal": {"type": "string", "description": "Goal: lose_fat, maintain, build_muscle"}
                    },
                    "required": ["weight_kg", "height_cm", "age"]
                }
            },
            {
                "name": "analyze_food_image",
                "description": "Analyze food in an image",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_base64": {"type": "string", "description": "Base64 encoded image"}
                    },
                    "required": ["image_base64"]
                }
            }
        ]


def run_nutritionist(state: AgentState) -> AgentState:
    """
    Functional interface for nutritionist agent.
    Used as a LangGraph node.

    Args:
        state: Current agent state.

    Returns:
        Updated state with nutritionist response.
    """
    agent = NutritionistAgent()
    return agent.process(state)
