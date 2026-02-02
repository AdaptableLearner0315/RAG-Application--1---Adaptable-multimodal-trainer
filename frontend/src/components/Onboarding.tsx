'use client';

/**
 * Onboarding flow component for new users.
 * Collects user profile information in 5-6 steps.
 */

import React, { useState } from 'react';
import { createProfile, UserProfile } from '@/lib/api';
import { ChevronRight, ChevronLeft, User, Heart, Pill, Utensils, Target, CheckCircle } from 'lucide-react';

interface OnboardingProps {
  userId: string;
  onComplete: (profile: UserProfile) => void;
}

interface OnboardingData {
  // Step 1: Demographics
  age: number;
  gender: string;
  height_cm: number;
  weight_kg: number;
  // Step 2: Health Conditions
  health_conditions: string[];
  // Step 3: Medications
  medications: string[];
  // Step 4: Physical Limitations & Allergies
  injuries: string[];
  allergies: string[];
  intolerances: string[];
  // Step 5: Goals & Preferences
  dietary_pref: string;
  fitness_level: string;
  primary_goal: string;
}

const HEALTH_CONDITIONS = [
  'Diabetes',
  'Hypertension',
  'Heart Disease',
  'Asthma',
  'Arthritis',
  'Thyroid Disorder',
  'PCOS',
  'Depression/Anxiety',
  'None',
];

const COMMON_ALLERGIES = [
  'Peanuts',
  'Tree Nuts',
  'Dairy',
  'Eggs',
  'Gluten',
  'Soy',
  'Shellfish',
  'None',
];

const DIETARY_PREFS = [
  { value: 'omnivore', label: 'Omnivore (eat everything)' },
  { value: 'vegetarian', label: 'Vegetarian' },
  { value: 'vegan', label: 'Vegan' },
  { value: 'pescatarian', label: 'Pescatarian' },
  { value: 'keto', label: 'Keto' },
];

const FITNESS_LEVELS = [
  { value: 'beginner', label: 'Beginner (new to exercise)' },
  { value: 'intermediate', label: 'Intermediate (exercise 2-3x/week)' },
  { value: 'advanced', label: 'Advanced (exercise 4+x/week)' },
];

const GOALS = [
  { value: 'lose_fat', label: 'Lose Weight' },
  { value: 'build_muscle', label: 'Build Muscle' },
  { value: 'maintain', label: 'Maintain Current Weight' },
  { value: 'improve_energy', label: 'Improve Energy & Health' },
];

/**
 * Main Onboarding component.
 */
export function Onboarding({ userId, onComplete }: OnboardingProps) {
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [data, setData] = useState<OnboardingData>({
    age: 18,
    gender: 'prefer_not_to_say',
    height_cm: 170,
    weight_kg: 70,
    health_conditions: [],
    medications: [],
    injuries: [],
    allergies: [],
    intolerances: [],
    dietary_pref: 'omnivore',
    fitness_level: 'beginner',
    primary_goal: 'maintain',
  });

  const [customMedication, setCustomMedication] = useState('');
  const [customInjury, setCustomInjury] = useState('');

  const totalSteps = 5;

  /**
   * Handle form submission.
   */
  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const profileData = {
        age: data.age,
        height_cm: data.height_cm,
        weight_kg: data.weight_kg,
        gender: data.gender,
        injuries: data.injuries,
        intolerances: data.intolerances,
        allergies: data.allergies.filter(a => a !== 'None'),
        health_conditions: data.health_conditions.filter(c => c !== 'None'),
        medications: data.medications,
        dietary_pref: data.dietary_pref,
        fitness_level: data.fitness_level,
        primary_goal: data.primary_goal,
      };

      const profile = await createProfile(userId, profileData);
      onComplete(profile);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create profile';

      // If profile already exists, try to get it and proceed
      if (errorMessage.includes('already exists')) {
        try {
          const { getProfile } = await import('@/lib/api');
          const existingProfile = await getProfile(userId);
          if (existingProfile) {
            onComplete(existingProfile);
            return;
          }
        } catch {
          // If we can't get the profile, show the original error
        }
      }

      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Toggle selection in array field.
   */
  const toggleArrayItem = (field: keyof OnboardingData, item: string) => {
    setData(prev => {
      const arr = prev[field] as string[];
      if (item === 'None') {
        return { ...prev, [field]: arr.includes('None') ? [] : ['None'] };
      }
      const withoutNone = arr.filter(i => i !== 'None');
      if (withoutNone.includes(item)) {
        return { ...prev, [field]: withoutNone.filter(i => i !== item) };
      }
      return { ...prev, [field]: [...withoutNone, item] };
    });
  };

  /**
   * Add custom item to array field.
   */
  const addCustomItem = (field: keyof OnboardingData, value: string, setter: (v: string) => void) => {
    if (value.trim()) {
      setData(prev => {
        const arr = (prev[field] as string[]).filter(i => i !== 'None');
        if (!arr.includes(value.trim())) {
          return { ...prev, [field]: [...arr, value.trim()] };
        }
        return prev;
      });
      setter('');
    }
  };

  /**
   * Render step content.
   */
  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Tell us about yourself</h2>
                <p className="text-gray-500 text-sm">Basic information to personalize your experience</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                <input
                  type="number"
                  min={13}
                  max={100}
                  value={data.age}
                  onChange={e => setData(prev => ({ ...prev, age: parseInt(e.target.value) || 18 }))}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                <select
                  value={data.gender}
                  onChange={e => setData(prev => ({ ...prev, gender: e.target.value }))}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="prefer_not_to_say">Prefer not to say</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Height (cm)</label>
                <input
                  type="number"
                  min={100}
                  max={250}
                  value={data.height_cm}
                  onChange={e => setData(prev => ({ ...prev, height_cm: parseFloat(e.target.value) || 170 }))}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg)</label>
                <input
                  type="number"
                  min={30}
                  max={300}
                  value={data.weight_kg}
                  onChange={e => setData(prev => ({ ...prev, weight_kg: parseFloat(e.target.value) || 70 }))}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                <Heart className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Health Conditions</h2>
                <p className="text-gray-500 text-sm">Select any conditions that apply (helps us provide safe advice)</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {HEALTH_CONDITIONS.map(condition => (
                <button
                  key={condition}
                  type="button"
                  onClick={() => toggleArrayItem('health_conditions', condition)}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    data.health_conditions.includes(condition)
                      ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  {condition}
                </button>
              ))}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                <Pill className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Current Medications</h2>
                <p className="text-gray-500 text-sm">List any medications you&apos;re taking (optional)</p>
              </div>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Enter medication name"
                value={customMedication}
                onChange={e => setCustomMedication(e.target.value)}
                onKeyPress={e => e.key === 'Enter' && addCustomItem('medications', customMedication, setCustomMedication)}
                className="flex-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => addCustomItem('medications', customMedication, setCustomMedication)}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
              >
                Add
              </button>
            </div>

            {data.medications.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {data.medications.map(med => (
                  <span
                    key={med}
                    className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                  >
                    {med}
                    <button
                      type="button"
                      onClick={() => setData(prev => ({ ...prev, medications: prev.medications.filter(m => m !== med) }))}
                      className="hover:text-purple-900"
                    >
                      &times;
                    </button>
                  </span>
                ))}
              </div>
            )}

            <p className="text-gray-400 text-sm">Press Enter or click Add to include each medication. Skip if none.</p>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                <Utensils className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Allergies & Physical Limitations</h2>
                <p className="text-gray-500 text-sm">Help us avoid recommending things that could harm you</p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Food Allergies</label>
              <div className="grid grid-cols-2 gap-2">
                {COMMON_ALLERGIES.map(allergy => (
                  <button
                    key={allergy}
                    type="button"
                    onClick={() => toggleArrayItem('allergies', allergy)}
                    className={`p-2 rounded-lg border text-sm transition-colors ${
                      data.allergies.includes(allergy)
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    {allergy}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Injuries or Physical Limitations</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g., knee injury, back pain"
                  value={customInjury}
                  onChange={e => setCustomInjury(e.target.value)}
                  onKeyPress={e => e.key === 'Enter' && addCustomItem('injuries', customInjury, setCustomInjury)}
                  className="flex-1 border rounded-lg px-3 py-2 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => addCustomItem('injuries', customInjury, setCustomInjury)}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
                >
                  Add
                </button>
              </div>
              {data.injuries.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {data.injuries.map(injury => (
                    <span
                      key={injury}
                      className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm flex items-center gap-2"
                    >
                      {injury}
                      <button
                        type="button"
                        onClick={() => setData(prev => ({ ...prev, injuries: prev.injuries.filter(i => i !== injury) }))}
                        className="hover:text-orange-900"
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <Target className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-xl font-semibold">Goals & Preferences</h2>
                <p className="text-gray-500 text-sm">What would you like to achieve?</p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Primary Goal</label>
              <div className="grid grid-cols-2 gap-2">
                {GOALS.map(goal => (
                  <button
                    key={goal.value}
                    type="button"
                    onClick={() => setData(prev => ({ ...prev, primary_goal: goal.value }))}
                    className={`p-3 rounded-lg border text-left transition-colors ${
                      data.primary_goal === goal.value
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    {goal.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Dietary Preference</label>
              <div className="space-y-2">
                {DIETARY_PREFS.map(pref => (
                  <button
                    key={pref.value}
                    type="button"
                    onClick={() => setData(prev => ({ ...prev, dietary_pref: pref.value }))}
                    className={`w-full p-3 rounded-lg border text-left transition-colors ${
                      data.dietary_pref === pref.value
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    {pref.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Current Fitness Level</label>
              <div className="space-y-2">
                {FITNESS_LEVELS.map(level => (
                  <button
                    key={level.value}
                    type="button"
                    onClick={() => setData(prev => ({ ...prev, fitness_level: level.value }))}
                    className={`w-full p-3 rounded-lg border text-left transition-colors ${
                      data.fitness_level === level.value
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-700'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    {level.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-lg p-6">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-500 mb-2">
            <span>Step {step} of {totalSteps}</span>
            <span>{Math.round((step / totalSteps) * 100)}%</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-600 transition-all duration-300"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Step content */}
        <div className="min-h-[400px]">
          {renderStep()}
        </div>

        {/* Error message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <button
            type="button"
            onClick={() => setStep(s => s - 1)}
            disabled={step === 1}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>

          {step < totalSteps ? (
            <button
              type="button"
              onClick={() => setStep(s => s + 1)}
              className="flex items-center gap-2 px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex items-center gap-2 px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Complete Setup
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
