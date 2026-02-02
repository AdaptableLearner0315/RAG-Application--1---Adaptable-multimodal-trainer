/**
 * Custom hook for voice recording and transcription.
 */

import { useState, useCallback, useRef } from 'react';
import { transcribeVoice, VoiceResponse } from '@/lib/api';

/**
 * Voice recording state and actions.
 */
export interface UseVoiceReturn {
  isRecording: boolean;
  isTranscribing: boolean;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<VoiceResponse | null>;
  cancelRecording: () => void;
}

/**
 * Custom hook for voice recording and transcription.
 *
 * @returns Voice recording state and actions
 */
export function useVoice(): UseVoiceReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  /**
   * Start recording audio.
   */
  const startRecording = useCallback(async () => {
    setError(null);
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to access microphone';
      setError(message);
    }
  }, []);

  /**
   * Stop recording and transcribe audio.
   *
   * @returns Transcription result or null if cancelled
   */
  const stopRecording = useCallback(async (): Promise<VoiceResponse | null> => {
    if (!mediaRecorderRef.current || !isRecording) {
      return null;
    }

    return new Promise((resolve) => {
      const mediaRecorder = mediaRecorderRef.current!;

      mediaRecorder.onstop = async () => {
        // Stop all tracks
        mediaRecorder.stream.getTracks().forEach((track) => track.stop());

        // Create audio blob
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });

        // Convert to base64
        const reader = new FileReader();
        reader.onloadend = async () => {
          const base64 = (reader.result as string).split(',')[1];

          setIsRecording(false);
          setIsTranscribing(true);

          try {
            const result = await transcribeVoice({
              audio_base64: base64,
              format: 'webm',
            });
            resolve(result);
          } catch (err) {
            const message = err instanceof Error ? err.message : 'Transcription failed';
            setError(message);
            resolve(null);
          } finally {
            setIsTranscribing(false);
          }
        };

        reader.readAsDataURL(audioBlob);
      };

      mediaRecorder.stop();
    });
  }, [isRecording]);

  /**
   * Cancel recording without transcribing.
   */
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      mediaRecorderRef.current = null;
      chunksRef.current = [];
      setIsRecording(false);
    }
  }, [isRecording]);

  return {
    isRecording,
    isTranscribing,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
