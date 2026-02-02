/**
 * API client for communicating with the backend.
 * Uses centralized HTTP client for consistent error handling.
 */

import { post, get, put, HttpError } from './http';

// ============================================================================
// Types
// ============================================================================

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

// Re-export HttpError for consumers
export { HttpError };

// ============================================================================
// Chat API
// ============================================================================

/**
 * Send a chat message to the API.
 */
export function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  return post<ChatResponse>('/api/chat', request);
}

// ============================================================================
// Voice API
// ============================================================================

/**
 * Transcribe voice audio to text.
 */
export function transcribeVoice(request: VoiceRequest): Promise<VoiceResponse> {
  return post<VoiceResponse>('/api/voice/transcribe', request);
}

// ============================================================================
// Image API
// ============================================================================

/**
 * Analyze a food image.
 */
export function analyzeImage(request: ImageRequest): Promise<ImageResponse> {
  return post<ImageResponse>('/api/image/analyze', request);
}

// ============================================================================
// Profile API
// ============================================================================

/**
 * Get user profile.
 * Returns null if profile doesn't exist (404).
 */
export async function getProfile(userId: string): Promise<UserProfile | null> {
  try {
    return await get<UserProfile>(`/api/profile/${userId}`);
  } catch (error) {
    if (error instanceof HttpError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * Create user profile.
 */
export function createProfile(
  userId: string,
  profile: Omit<UserProfile, 'user_id'>
): Promise<UserProfile> {
  return post<UserProfile>(`/api/profile/${userId}`, profile);
}

/**
 * Update user profile.
 */
export function updateProfile(
  userId: string,
  updates: Partial<UserProfile>
): Promise<UserProfile> {
  return put<UserProfile>(`/api/profile/${userId}`, updates);
}

/**
 * Delete user profile.
 */
export async function deleteProfile(userId: string): Promise<void> {
  const { del } = await import('./http');
  await del(`/api/profile/${userId}`);
}
