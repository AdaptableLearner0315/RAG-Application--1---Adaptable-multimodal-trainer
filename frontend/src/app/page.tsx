'use client';

/**
 * Main chat page.
 */

import { useState, useEffect } from 'react';
import { Chat } from '@/components/Chat';
import { getProfile } from '@/lib/api';

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

export default function Home() {
  const [userId, setUserId] = useState<string>('');
  const [hasProfile, setHasProfile] = useState<boolean | null>(null);

  useEffect(() => {
    const id = getUserId();
    setUserId(id);

    // Check if user has profile
    getProfile(id)
      .then((profile) => setHasProfile(profile !== null))
      .catch(() => setHasProfile(false));
  }, []);

  if (!userId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full" />
      </div>
    );
  }

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

          {hasProfile === false && (
            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded">
              New User
            </span>
          )}
        </div>
      </header>

      {/* Chat area */}
      <div className="flex-1">
        <Chat userId={userId} />
      </div>
    </main>
  );
}
