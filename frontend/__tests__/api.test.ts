/**
 * Unit tests for API client.
 */

import { sendMessage, transcribeVoice, analyzeImage, getProfile, createProfile, updateProfile } from '../src/lib/api';

// Mock fetch globally
global.fetch = jest.fn();

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('sendMessage', () => {
    it('should send message and return response', async () => {
      const mockResponse = {
        response: 'Here is your workout plan',
        agent: 'trainer',
        session_id: 'session123',
        memory_updated: true,
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await sendMessage({
        message: 'What workout should I do?',
        user_id: 'user123',
      });

      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/chat',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });

    it('should throw error on failed request', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Message blocked' }),
      });

      await expect(
        sendMessage({ message: 'test', user_id: 'user123' })
      ).rejects.toThrow('Message blocked');
    });
  });

  describe('transcribeVoice', () => {
    it('should transcribe audio and return text', async () => {
      const mockResponse = {
        text: 'What should I eat?',
        confidence: 0.95,
        duration_sec: 2.5,
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await transcribeVoice({
        audio_base64: 'base64audio',
        format: 'webm',
      });

      expect(result.text).toBe('What should I eat?');
      expect(result.confidence).toBe(0.95);
    });

    it('should throw error on transcription failure', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Invalid audio format' }),
      });

      await expect(
        transcribeVoice({ audio_base64: 'bad', format: 'invalid' })
      ).rejects.toThrow('Invalid audio format');
    });
  });

  describe('analyzeImage', () => {
    it('should analyze food image', async () => {
      const mockResponse = {
        detected_foods: [
          { name: 'chicken', estimated_calories: 200 },
        ],
        confidence: 0.85,
        message: 'Found 1 food item',
        low_confidence: false,
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await analyzeImage({
        image_base64: 'base64image',
        user_id: 'user123',
      });

      expect(result.detected_foods).toHaveLength(1);
      expect(result.detected_foods[0].name).toBe('chicken');
    });
  });

  describe('getProfile', () => {
    it('should return profile when found', async () => {
      const mockProfile = {
        user_id: 'user123',
        age: 17,
        height_cm: 175,
        weight_kg: 70,
        injuries: [],
        intolerances: [],
        allergies: [],
        dietary_pref: 'omnivore',
        fitness_level: 'beginner',
        primary_goal: 'build_muscle',
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockProfile,
      });

      const result = await getProfile('user123');
      expect(result).toEqual(mockProfile);
    });

    it('should return null when profile not found', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      const result = await getProfile('nonexistent');
      expect(result).toBeNull();
    });
  });

  describe('createProfile', () => {
    it('should create new profile', async () => {
      const profileData = {
        age: 17,
        height_cm: 175,
        weight_kg: 70,
        injuries: [],
        intolerances: [],
        allergies: [],
        dietary_pref: 'omnivore',
        fitness_level: 'beginner',
        primary_goal: 'build_muscle',
      };

      const mockResponse = { user_id: 'user123', ...profileData };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await createProfile('user123', profileData);
      expect(result.user_id).toBe('user123');
    });
  });

  describe('updateProfile', () => {
    it('should update existing profile', async () => {
      const updates = { weight_kg: 72 };
      const mockResponse = {
        user_id: 'user123',
        age: 17,
        height_cm: 175,
        weight_kg: 72,
        injuries: [],
        intolerances: [],
        allergies: [],
        dietary_pref: 'omnivore',
        fitness_level: 'beginner',
        primary_goal: 'build_muscle',
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await updateProfile('user123', updates);
      expect(result.weight_kg).toBe(72);
    });
  });
});
