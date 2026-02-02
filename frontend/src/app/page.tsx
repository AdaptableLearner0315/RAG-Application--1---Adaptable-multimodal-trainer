'use client';

/**
 * Main application page with onboarding flow.
 */

import { useState, useEffect } from 'react';
import { Chat } from '@/components/Chat';
import { Onboarding } from '@/components/Onboarding';
import { getProfile, UserProfile } from '@/lib/api';

/**
 * Generate or retrieve user ID from localStorage.
 */
function getUserId(): string {
  if (typeof window === 'undefined') {
    return 'anonymous';
  }

  let userId = localStorage.getItem('aacp_user_id');
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('aacp_user_id', userId);
  }
  return userId;
}

/**
 * Reset user ID to start fresh.
 */
function resetUserId(): string {
  if (typeof window === 'undefined') {
    return 'anonymous';
  }
  const newUserId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  localStorage.setItem('aacp_user_id', newUserId);
  return newUserId;
}

type AppState = 'loading' | 'onboarding' | 'chat';

export default function Home() {
  const [userId, setUserId] = useState<string>('');
  const [appState, setAppState] = useState<AppState>('loading');
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    const id = getUserId();
    setUserId(id);

    // Check if user has profile
    getProfile(id)
      .then((existingProfile) => {
        if (existingProfile) {
          setProfile(existingProfile);
          setAppState('chat');
        } else {
          setAppState('onboarding');
        }
      })
      .catch(() => {
        // If error checking profile, show onboarding
        setAppState('onboarding');
      });
  }, []);

  /**
   * Handle onboarding completion.
   */
  const handleOnboardingComplete = (newProfile: UserProfile) => {
    setProfile(newProfile);
    setAppState('chat');
  };

  // Show loading spinner while checking profile
  if (appState === 'loading' || !userId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin w-10 h-10 border-4 border-emerald-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  // Show onboarding for new users
  if (appState === 'onboarding') {
    return <Onboarding userId={userId} onComplete={handleOnboardingComplete} />;
  }

  /**
   * Handle reset - clear user data and restart onboarding.
   */
  const handleReset = () => {
    const newId = resetUserId();
    setUserId(newId);
    setProfile(null);
    setAppState('onboarding');
  };

  // Show chat for existing users
  return (
    <main className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">AC</span>
            </div>
            <h1 className="font-semibold text-lg">Adaptive Coach</h1>
          </div>

          <div className="flex items-center gap-2">
            {profile && (
              <>
                <span className="text-xs text-gray-500">
                  Goal: {profile.primary_goal.replace('_', ' ')}
                </span>
                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded">
                  {profile.fitness_level}
                </span>
              </>
            )}
            <button
              onClick={handleReset}
              className="text-xs text-gray-400 hover:text-gray-600 ml-2"
              title="Reset profile (start over)"
            >
              Reset
            </button>
          </div>
        </div>
      </header>

      {/* Chat area */}
      <div className="flex-1">
        <Chat userId={userId} />
      </div>
    </main>
  );
}
