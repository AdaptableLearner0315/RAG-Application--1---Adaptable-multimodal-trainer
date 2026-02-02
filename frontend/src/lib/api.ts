/**
 * API client for communicating with the backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Chat request payload.
 * Note: Model is auto-selected by backend based on query complexity.
 */
export interface ChatRequest {
  message: string;
  user_id: string;
  session_id?: string;
  image_base64?: string;
}

/**
 * Chat response from API.
 */
export interface ChatResponse {
  response: string;
  agent: string;
  session_id: string;
  sources?: string[];
  memory_updated: boolean;
}

/**
 * Voice transcription request.
 */
export interface VoiceRequest {
  audio_base64: string;
  format: string;
}

/**
 * Voice transcription response.
 */
export interface VoiceResponse {
  text: string;
  confidence: number;
  duration_sec?: number;
}

/**
 * Image analysis request.
 */
export interface ImageRequest {
  image_base64: string;
  user_id: string;
}

/**
 * Food item from image analysis.
 */
export interface FoodItem {
  name: string;
  estimated_calories?: number;
  estimated_protein?: number;
  estimated_carbs?: number;
  estimated_fat?: number;
  portion_size?: string;
}

/**
 * Image analysis response.
 */
export interface ImageResponse {
  detected_foods: FoodItem[];
  total_calories?: number;
  confidence: number;
  message: string;
  low_confidence: boolean;
}

/**
 * User profile data.
 */
export interface UserProfile {
  user_id: string;
  age: number;
  height_cm: number;
  weight_kg: number;
  gender: string;
  injuries: string[];
  intolerances: string[];
  allergies: string[];
  health_conditions: string[];
  medications: string[];
  dietary_pref: string;
  fitness_level: string;
  primary_goal: string;
  target_weight_kg?: number;
}

/**
 * API error response.
 */
export interface ApiError {
  detail: string;
}

/**
 * Send a chat message to the API.
 *
 * @param request - Chat request payload
 * @returns Promise resolving to chat response
 */
export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to send message');
  }

  return response.json();
}

/**
 * Transcribe voice audio to text.
 *
 * @param request - Voice request with audio data
 * @returns Promise resolving to transcription result
 */
export async function transcribeVoice(request: VoiceRequest): Promise<VoiceResponse> {
  const response = await fetch(`${API_URL}/api/voice/transcribe`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to transcribe audio');
  }

  return response.json();
}

/**
 * Analyze a food image.
 *
 * @param request - Image request with base64 data
 * @returns Promise resolving to image analysis result
 */
export async function analyzeImage(request: ImageRequest): Promise<ImageResponse> {
  const response = await fetch(`${API_URL}/api/image/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to analyze image');
  }

  return response.json();
}

/**
 * Get user profile.
 *
 * @param userId - User identifier
 * @returns Promise resolving to user profile or null if not found
 */
export async function getProfile(userId: string): Promise<UserProfile | null> {
  const response = await fetch(`${API_URL}/api/profile/${userId}`);

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to get profile');
  }

  return response.json();
}

/**
 * Create user profile.
 *
 * @param userId - User identifier
 * @param profile - Profile data
 * @returns Promise resolving to created profile
 */
export async function createProfile(
  userId: string,
  profile: Omit<UserProfile, 'user_id'>
): Promise<UserProfile> {
  try {
    const response = await fetch(`${API_URL}/api/profile/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profile),
    });

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const error: ApiError = await response.json();
        errorMessage = error.detail || errorMessage;
      } catch {
        // JSON parsing failed, use status text
      }
      throw new Error(errorMessage);
    }

    return response.json();
  } catch (err) {
    if (err instanceof Error) {
      throw err;
    }
    throw new Error('Network error: Failed to create profile');
  }
}

/**
 * Update user profile.
 *
 * @param userId - User identifier
 * @param updates - Partial profile updates
 * @returns Promise resolving to updated profile
 */
export async function updateProfile(
  userId: string,
  updates: Partial<UserProfile>
): Promise<UserProfile> {
  const response = await fetch(`${API_URL}/api/profile/${userId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error: ApiError = await response.json();
    throw new Error(error.detail || 'Failed to update profile');
  }

  return response.json();
}
