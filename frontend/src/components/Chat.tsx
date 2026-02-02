'use client';

/**
 * Main chat interface component.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useChat, Message } from '@/hooks/useChat';
import { VoiceInput } from './VoiceInput';
import { ImageUpload } from './ImageUpload';
import { Send, User, Bot, Dumbbell, Apple, Moon } from 'lucide-react';

interface ChatProps {
  userId: string;
}

/**
 * Get agent icon based on agent type.
 */
function getAgentIcon(agent?: string) {
  switch (agent) {
    case 'trainer':
      return <Dumbbell className="w-4 h-4" />;
    case 'nutritionist':
      return <Apple className="w-4 h-4" />;
    case 'recovery':
      return <Moon className="w-4 h-4" />;
    default:
      return <Bot className="w-4 h-4" />;
  }
}

/**
 * Get agent label.
 */
function getAgentLabel(agent?: string): string {
  switch (agent) {
    case 'trainer':
      return 'Trainer';
    case 'nutritionist':
      return 'Nutritionist';
    case 'recovery':
      return 'Recovery Coach';
    case 'system':
      return 'System';
    default:
      return 'Coach';
  }
}

/**
 * Chat message component.
 */
function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-blue-600' : 'bg-emerald-600'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <span className="text-white">{getAgentIcon(message.agent)}</span>
        )}
      </div>
      <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
        {!isUser && (
          <span className="text-xs text-gray-500 mb-1 block">
            {getAgentLabel(message.agent)}
          </span>
        )}
        <div
          className={`inline-block p-3 rounded-lg max-w-[80%] ${
            isUser
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        <span className="text-xs text-gray-400 mt-1 block">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}

/**
 * Main Chat component.
 */
export function Chat({ userId }: ChatProps) {
  const {
    messages,
    isLoading,
    error,
    sendUserMessage,
    clearError,
  } = useChat(userId);

  const [input, setInput] = useState('');
  const [pendingImage, setPendingImage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Handle form submission.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !pendingImage) return;

    const message = input.trim() || 'What is in this image?';
    setInput('');

    await sendUserMessage(message, pendingImage || undefined);
    setPendingImage(null);
  };

  /**
   * Handle voice transcription result.
   */
  const handleVoiceResult = (text: string) => {
    setInput(text);
  };

  /**
   * Handle image upload.
   */
  const handleImageUpload = (base64: string) => {
    setPendingImage(base64);
  };

  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-10">
            <Bot className="w-12 h-12 mx-auto mb-4 text-emerald-600" />
            <h2 className="text-xl font-semibold mb-2">
              Welcome to Your Coaching Assistant
            </h2>
            <p>
              Ask me about nutrition, workouts, recovery, or share a photo of your meal.
            </p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-gray-100 rounded-lg p-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700">
            <p>{error}</p>
            <button
              onClick={clearError}
              className="text-sm underline mt-1"
            >
              Dismiss
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Pending image preview */}
      {pendingImage && (
        <div className="px-4 pb-2">
          <div className="bg-gray-100 rounded-lg p-2 flex items-center gap-2">
            <img
              src={`data:image/jpeg;base64,${pendingImage}`}
              alt="Pending upload"
              className="w-16 h-16 object-cover rounded"
            />
            <span className="text-sm text-gray-600 flex-1">
              Image ready to send
            </span>
            <button
              onClick={() => setPendingImage(null)}
              className="text-red-600 text-sm"
            >
              Remove
            </button>
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <VoiceInput onResult={handleVoiceResult} />
          <ImageUpload onUpload={handleImageUpload} userId={userId} />

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about nutrition, fitness, or recovery..."
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            disabled={isLoading}
          />

          <button
            type="submit"
            disabled={isLoading || (!input.trim() && !pendingImage)}
            className="bg-emerald-600 text-white rounded-lg px-4 py-2 hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}
