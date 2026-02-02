/**
 * Unit tests for useChat hook.
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useChat } from '../src/hooks/useChat';
import * as api from '../src/lib/api';

// Mock the API module
jest.mock('../src/lib/api');

describe('useChat Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should initialize with empty state', () => {
    const { result } = renderHook(() => useChat('user123'));

    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.sessionId).toBeNull();
  });

  it('should send message and update state', async () => {
    const mockResponse = {
      response: 'Here is your workout plan',
      agent: 'trainer',
      session_id: 'session123',
      memory_updated: true,
    };

    (api.sendMessage as jest.Mock).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useChat('user123'));

    await act(async () => {
      await result.current.sendUserMessage('What workout should I do?');
    });

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.messages[0].content).toBe('What workout should I do?');
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.messages[1].content).toBe('Here is your workout plan');
    expect(result.current.messages[1].agent).toBe('trainer');
    expect(result.current.sessionId).toBe('session123');
  });

  it('should handle API errors', async () => {
    (api.sendMessage as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => useChat('user123'));

    await act(async () => {
      await result.current.sendUserMessage('Test message');
    });

    expect(result.current.error).toBe('Network error');
    expect(result.current.messages).toHaveLength(1); // Only user message
  });

  it('should not send empty messages', async () => {
    const { result } = renderHook(() => useChat('user123'));

    await act(async () => {
      await result.current.sendUserMessage('   ');
    });

    expect(api.sendMessage).not.toHaveBeenCalled();
    expect(result.current.messages).toHaveLength(0);
  });

  it('should clear messages', async () => {
    const mockResponse = {
      response: 'Response',
      agent: 'trainer',
      session_id: 'session123',
      memory_updated: true,
    };

    (api.sendMessage as jest.Mock).mockResolvedValueOnce(mockResponse);

    const { result } = renderHook(() => useChat('user123'));

    await act(async () => {
      await result.current.sendUserMessage('Test');
    });

    expect(result.current.messages).toHaveLength(2);

    act(() => {
      result.current.clearMessages();
    });

    expect(result.current.messages).toHaveLength(0);
    expect(result.current.sessionId).toBeNull();
  });

  it('should clear error', async () => {
    (api.sendMessage as jest.Mock).mockRejectedValueOnce(new Error('Test error'));

    const { result } = renderHook(() => useChat('user123'));

    await act(async () => {
      await result.current.sendUserMessage('Test');
    });

    expect(result.current.error).toBe('Test error');

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it('should preserve session ID across messages', async () => {
    const mockResponse1 = {
      response: 'First response',
      agent: 'trainer',
      session_id: 'session123',
      memory_updated: true,
    };

    const mockResponse2 = {
      response: 'Second response',
      agent: 'nutritionist',
      session_id: 'session123',
      memory_updated: true,
    };

    (api.sendMessage as jest.Mock)
      .mockResolvedValueOnce(mockResponse1)
      .mockResolvedValueOnce(mockResponse2);

    const { result } = renderHook(() => useChat('user123'));

    await act(async () => {
      await result.current.sendUserMessage('First message');
    });

    await act(async () => {
      await result.current.sendUserMessage('Second message');
    });

    expect(result.current.messages).toHaveLength(4);
    expect(result.current.sessionId).toBe('session123');

    // Verify session ID was passed in second call
    expect(api.sendMessage).toHaveBeenCalledTimes(2);
    expect((api.sendMessage as jest.Mock).mock.calls[1][0]).toHaveProperty(
      'session_id',
      'session123'
    );
  });

  it('should set loading state during request', async () => {
    let resolvePromise: (value: unknown) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    (api.sendMessage as jest.Mock).mockReturnValueOnce(promise);

    const { result } = renderHook(() => useChat('user123'));

    act(() => {
      result.current.sendUserMessage('Test');
    });

    // Should be loading immediately after starting request
    expect(result.current.isLoading).toBe(true);

    await act(async () => {
      resolvePromise!({
        response: 'Done',
        agent: 'trainer',
        session_id: 'session123',
        memory_updated: true,
      });
    });

    // Should stop loading after request completes
    expect(result.current.isLoading).toBe(false);
  });
});
