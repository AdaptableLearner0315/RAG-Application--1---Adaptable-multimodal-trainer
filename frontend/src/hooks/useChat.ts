/**
 * Custom hook for managing chat state.
 */

import { useState, useCallback } from 'react';
import { sendMessage, ChatResponse } from '@/lib/api';

/**
 * Chat message structure.
 */
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  timestamp: Date;
}

/**
 * Chat state and actions.
 */
export interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  sendUserMessage: (content: string, imageBase64?: string) => Promise<void>;
  clearMessages: () => void;
  clearError: () => void;
}

/**
 * Generate a unique ID for messages.
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Custom hook for chat functionality.
 *
 * @param userId - User identifier
 * @returns Chat state and actions
 */
export function useChat(userId: string): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  /**
   * Send a user message and get assistant response.
   *
   * @param content - Message content
   * @param imageBase64 - Optional image data
   */
  const sendUserMessage = useCallback(
    async (content: string, imageBase64?: string) => {
      if (!content.trim()) return;

      // Add user message
      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response: ChatResponse = await sendMessage({
          message: content.trim(),
          user_id: userId,
          session_id: sessionId || undefined,
          image_base64: imageBase64,
        });

        // Update session ID if new
        if (response.session_id && !sessionId) {
          setSessionId(response.session_id);
        }

        // Add assistant message
        const assistantMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: response.response,
          agent: response.agent,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [userId, sessionId]
  );

  /**
   * Clear all messages.
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
    setSessionId(null);
  }, []);

  /**
   * Clear error state.
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    sendUserMessage,
    clearMessages,
    clearError,
  };
}
