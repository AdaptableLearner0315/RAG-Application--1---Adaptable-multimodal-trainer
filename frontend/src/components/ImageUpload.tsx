'use client';

/**
 * Image upload component for food photo analysis.
 */

import React, { useRef, useState } from 'react';
import { Camera, Loader, X } from 'lucide-react';
import { analyzeImage, ImageResponse } from '@/lib/api';

interface ImageUploadProps {
  onUpload: (base64: string) => void;
  userId: string;
}

/**
 * Image upload button with preview.
 */
export function ImageUpload({ onUpload, userId }: ImageUploadProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<ImageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /**
   * Handle file selection.
   */
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image must be smaller than 10MB');
      return;
    }

    setError(null);

    // Read file as base64
    const reader = new FileReader();
    reader.onloadend = async () => {
      const base64 = (reader.result as string).split(',')[1];
      setPreview(reader.result as string);

      // Analyze image
      setIsAnalyzing(true);
      try {
        const result = await analyzeImage({
          image_base64: base64,
          user_id: userId,
        });
        setAnalysisResult(result);
        onUpload(base64);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to analyze image';
        setError(message);
      } finally {
        setIsAnalyzing(false);
      }
    };

    reader.readAsDataURL(file);

    // Reset input
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  /**
   * Clear preview and result.
   */
  const handleClear = () => {
    setPreview(null);
    setAnalysisResult(null);
    setError(null);
  };

  /**
   * Trigger file input click.
   */
  const handleClick = () => {
    inputRef.current?.click();
  };

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileChange}
        className="hidden"
      />

      <button
        type="button"
        onClick={handleClick}
        disabled={isAnalyzing}
        className={`p-2 rounded-lg transition-colors ${
          preview
            ? 'bg-emerald-100 text-emerald-600'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        } ${isAnalyzing ? 'opacity-50 cursor-not-allowed' : ''}`}
        title="Upload food photo"
      >
        {isAnalyzing ? (
          <Loader className="w-5 h-5 animate-spin" />
        ) : (
          <Camera className="w-5 h-5" />
        )}
      </button>

      {/* Analysis result popup */}
      {analysisResult && preview && (
        <div className="absolute bottom-full left-0 mb-2 w-64 bg-white border rounded-lg shadow-lg p-3">
          <div className="flex justify-between items-start mb-2">
            <span className="font-medium text-sm">Food Detected</span>
            <button onClick={handleClear} className="text-gray-400 hover:text-gray-600">
              <X className="w-4 h-4" />
            </button>
          </div>

          <img
            src={preview}
            alt="Food preview"
            className="w-full h-24 object-cover rounded mb-2"
          />

          {analysisResult.detected_foods.length > 0 ? (
            <ul className="text-xs space-y-1">
              {analysisResult.detected_foods.map((food, i) => (
                <li key={i} className="flex justify-between">
                  <span>{food.name}</span>
                  {food.estimated_calories && (
                    <span className="text-gray-500">{food.estimated_calories} cal</span>
                  )}
                </li>
              ))}
              {analysisResult.total_calories && (
                <li className="flex justify-between font-medium border-t pt-1 mt-1">
                  <span>Total</span>
                  <span>{analysisResult.total_calories} cal</span>
                </li>
              )}
            </ul>
          ) : (
            <p className="text-xs text-gray-500">{analysisResult.message}</p>
          )}

          {analysisResult.low_confidence && (
            <p className="text-xs text-amber-600 mt-2">
              Low confidence - estimates may be inaccurate
            </p>
          )}
        </div>
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
