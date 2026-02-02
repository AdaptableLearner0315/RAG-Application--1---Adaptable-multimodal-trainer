"""
Working memory using Redis for session state.
Stores current conversation and context during active sessions.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from unittest.mock import MagicMock

from app.core.config import get_settings
from app.memory.schemas import WorkingMemory


class WorkingMemoryStore:
    """
    Current session state stored in Redis.
    Falls back to in-memory dict if Redis unavailable.
    """

    def __init__(self, redis_client=None, session_ttl: int = 3600):
        """
        Initialize working memory store.

        Args:
            redis_client: Redis client instance. If None, uses in-memory fallback.
            session_ttl: Session time-to-live in seconds. Defaults to 1 hour.
        """
        self.redis = redis_client
        self.session_ttl = session_ttl
        self._fallback_store: Dict[str, Dict] = {}
        self._use_fallback = redis_client is None

        if not self._use_fallback:
            try:
                self.redis.ping()
            except Exception:
                self._use_fallback = True

    def _get_key(self, user_id: str, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"working_memory:{user_id}:{session_id}"

    def _get_fallback_key(self, user_id: str, session_id: str) -> str:
        """Generate fallback store key."""
        return f"{user_id}:{session_id}"

    def create_session(self, user_id: str, session_id: str) -> WorkingMemory:
        """
        Create a new session.

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.

        Returns:
            New WorkingMemory instance.
        """
        memory = WorkingMemory(user_id=user_id, session_id=session_id)

        if self._use_fallback:
            key = self._get_fallback_key(user_id, session_id)
            self._fallback_store[key] = memory.model_dump()
        else:
            key = self._get_key(user_id, session_id)
            self.redis.setex(key, self.session_ttl, memory.model_dump_json())

        return memory

    def get(self, user_id: str, session_id: str) -> Optional[WorkingMemory]:
        """
        Retrieve session working memory.

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.

        Returns:
            WorkingMemory or None if not found.
        """
        if self._use_fallback:
            key = self._get_fallback_key(user_id, session_id)
            data = self._fallback_store.get(key)
            if data:
                return WorkingMemory(**data)
            return None

        key = self._get_key(user_id, session_id)
        data = self.redis.get(key)
        if not data:
            return None

        return WorkingMemory(**json.loads(data))

    def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Add message to conversation history.

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.
            role: Message role (user, assistant, system).
            content: Message content.
        """
        memory = self.get(user_id, session_id)
        if not memory:
            memory = self.create_session(user_id, session_id)

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        memory.conversation.append(message)

        self._save(memory)

    def get_recent_messages(
        self,
        user_id: str,
        session_id: str,
        count: int = 5
    ) -> List[Dict]:
        """
        Get recent messages from conversation.

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.
            count: Number of recent messages to return.

        Returns:
            List of recent messages.
        """
        memory = self.get(user_id, session_id)
        if not memory:
            return []
        return memory.conversation[-count:]

    def set_active_agent(
        self,
        user_id: str,
        session_id: str,
        agent: str
    ) -> None:
        """
        Set currently active agent.

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.
            agent: Agent name.
        """
        memory = self.get(user_id, session_id)
        if not memory:
            memory = self.create_session(user_id, session_id)

        memory.current_agent = agent
        self._save(memory)

    def set_context(
        self,
        user_id: str,
        session_id: str,
        context: Dict
    ) -> None:
        """
        Set pending context (retrieved docs, tool results).

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.
            context: Context dictionary.
        """
        memory = self.get(user_id, session_id)
        if not memory:
            memory = self.create_session(user_id, session_id)

        memory.pending_context = context
        self._save(memory)

    def _save(self, memory: WorkingMemory) -> None:
        """Save memory to store."""
        if self._use_fallback:
            key = self._get_fallback_key(memory.user_id, memory.session_id)
            self._fallback_store[key] = memory.model_dump()
        else:
            key = self._get_key(memory.user_id, memory.session_id)
            self.redis.setex(key, self.session_ttl, memory.model_dump_json())

    def clear(self, user_id: str, session_id: str) -> bool:
        """
        Clear session working memory.

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.

        Returns:
            True if cleared, False if not found.
        """
        if self._use_fallback:
            key = self._get_fallback_key(user_id, session_id)
            if key in self._fallback_store:
                del self._fallback_store[key]
                return True
            return False

        key = self._get_key(user_id, session_id)
        return self.redis.delete(key) > 0

    def extend_ttl(self, user_id: str, session_id: str) -> bool:
        """
        Extend session TTL.

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.

        Returns:
            True if extended, False if session not found.
        """
        if self._use_fallback:
            # Fallback store doesn't expire
            key = self._get_fallback_key(user_id, session_id)
            return key in self._fallback_store

        key = self._get_key(user_id, session_id)
        return self.redis.expire(key, self.session_ttl)
