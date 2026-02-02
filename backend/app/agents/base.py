"""
Base agent class with shared functionality.
All specialized agents inherit from this.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.core.config import get_settings


class BaseAgent(ABC):
    """
    Base class for all coaching agents.
    Provides common functionality for LLM interaction.
    """

    def __init__(
        self,
        name: str,
        description: str,
        system_prompt: str
    ):
        """
        Initialize base agent.

        Args:
            name: Agent name (e.g., "trainer").
            description: Agent description.
            system_prompt: System prompt for this agent.
        """
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self._llm_cache: Dict[str, ChatAnthropic] = {}

    def get_llm(self, model: Optional[str] = None) -> ChatAnthropic:
        """
        Get LLM instance for specified model.

        Args:
            model: Model name. If None, uses default from settings.

        Returns:
            ChatAnthropic instance.
        """
        settings = get_settings()
        model_name = model or settings.llm_model

        if model_name not in self._llm_cache:
            self._llm_cache[model_name] = ChatAnthropic(
                model=model_name,
                api_key=settings.anthropic_api_key,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature
            )

        return self._llm_cache[model_name]

    @property
    def llm(self) -> ChatAnthropic:
        """Lazy load default LLM (for backward compatibility)."""
        return self.get_llm()

    def process(self, state: AgentState) -> AgentState:
        """
        Process query and generate response.

        Args:
            state: Current agent state.

        Returns:
            Updated state with agent response.
        """
        # Build context-aware prompt
        full_prompt = self._build_prompt(state)

        # Get model from state (set by model router)
        model = state.get("model")

        # Generate response
        response = self._generate_response(full_prompt, state["query"], model)

        # Store response
        state["agent_responses"][self.name] = response
        state["current_agent"] = self.name

        return state

    def _build_prompt(self, state: AgentState) -> str:
        """
        Build full system prompt with context.

        Args:
            state: Current agent state.

        Returns:
            Complete system prompt.
        """
        parts = [self.system_prompt]

        # Add user context from memory
        if state.get("long_term_context"):
            parts.append(f"\n\nUser Profile:\n{state['long_term_context']}")

        if state.get("short_term_context"):
            parts.append(f"\n\nRecent Activity:\n{state['short_term_context']}")

        # Add retrieved documents
        if state.get("retrieved_docs"):
            docs_text = "\n".join([
                f"- {doc.get('content', '')[:200]}"
                for doc in state["retrieved_docs"][:3]
            ])
            parts.append(f"\n\nRelevant Information:\n{docs_text}")

        return "\n".join(parts)

    def _generate_response(
        self,
        system_prompt: str,
        query: str,
        model: Optional[str] = None
    ) -> str:
        """
        Generate response using LLM.

        Args:
            system_prompt: Full system prompt.
            query: User query.
            model: Optional model override from state.

        Returns:
            Generated response text.
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]

        try:
            llm = self.get_llm(model)
            response = llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"I apologize, but I encountered an issue: {str(e)}"

    @abstractmethod
    def get_tools(self) -> List[Dict]:
        """
        Get tools available to this agent.

        Returns:
            List of tool definitions.
        """
        pass
