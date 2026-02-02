'use client';

/**
 * Voice input component for recording and transcribing audio.
 */

import React from 'react';
import { useVoice } from '@/hooks/useVoice';
import { Mic, MicOff, Loader } from 'lucide-react';

interface VoiceInputProps {
  onResult: (text: string) => void;
}

/**
 * Voice input button with recording state.
 */
export function VoiceInput({ onResult }: VoiceInputProps) {
  const {
    isRecording,
    isTranscribing,
    error,
    startRecording,
    stopRecording,
  } = useVoice();

  /**
   * Handle mic button click.
   */
  const handleClick = async () => {
    if (isRecording) {
      const result = await stopRecording();
      if (result && result.text) {
        onResult(result.text);
      }
    } else {
      await startRecording();
    }
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={handleClick}
        disabled={isTranscribing}
        className={`p-2 rounded-lg transition-colors ${
          isRecording
            ? 'bg-red-600 text-white hover:bg-red-700'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        } ${isTranscribing ? 'opacity-50 cursor-not-allowed' : ''}`}
        title={isRecording ? 'Stop recording' : 'Start voice input'}
      >
        {isTranscribing ? (
          <Loader className="w-5 h-5 animate-spin" />
        ) : isRecording ? (
          <MicOff className="w-5 h-5" />
        ) : (
          <Mic className="w-5 h-5" />
        )}
      </button>

      {/* Recording indicator */}
      {isRecording && (
        <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
      )}

      {/* Error tooltip */}
      {error && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-red-600 text-white text-xs rounded whitespace-nowrap">
          {error}
        </div>
      )}
    </div>
  );
}
