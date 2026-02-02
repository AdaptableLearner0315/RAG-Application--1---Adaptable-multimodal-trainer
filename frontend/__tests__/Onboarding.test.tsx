/**
 * Unit tests for Onboarding component.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Onboarding } from '../src/components/Onboarding';
import * as api from '../src/lib/api';

// Mock the API module
jest.mock('../src/lib/api');

describe('Onboarding Component', () => {
  const mockUserId = 'test_user_123';
  const mockOnComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render step 1 (demographics) initially', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    expect(screen.getByText('Tell us about yourself')).toBeInTheDocument();
    expect(screen.getByText('Step 1 of 5')).toBeInTheDocument();
    expect(screen.getByText('Age')).toBeInTheDocument();
    expect(screen.getByText('Gender')).toBeInTheDocument();
    expect(screen.getByText('Height (cm)')).toBeInTheDocument();
    expect(screen.getByText('Weight (kg)')).toBeInTheDocument();
  });

  it('should navigate to step 2 when Next is clicked', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    const nextButton = screen.getByRole('button', { name: /Next/i });
    fireEvent.click(nextButton);

    expect(screen.getByText('Health Conditions')).toBeInTheDocument();
    expect(screen.getByText('Step 2 of 5')).toBeInTheDocument();
  });

  it('should navigate back when Back is clicked', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Go to step 2
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    expect(screen.getByText('Step 2 of 5')).toBeInTheDocument();

    // Go back to step 1
    fireEvent.click(screen.getByRole('button', { name: /Back/i }));
    expect(screen.getByText('Step 1 of 5')).toBeInTheDocument();
  });

  it('should disable Back button on step 1', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    const backButton = screen.getByRole('button', { name: /Back/i });
    expect(backButton).toBeDisabled();
  });

  it('should update age input', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Get the age input by its role (number input)
    const ageInput = screen.getAllByRole('spinbutton')[0] as HTMLInputElement;
    fireEvent.change(ageInput, { target: { value: '25' } });

    expect(ageInput.value).toBe('25');
  });

  it('should toggle health condition selection', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Navigate to step 2
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));

    const diabetesButton = screen.getByRole('button', { name: 'Diabetes' });

    // Select Diabetes
    fireEvent.click(diabetesButton);
    expect(diabetesButton).toHaveClass('bg-emerald-50');

    // Deselect Diabetes
    fireEvent.click(diabetesButton);
    expect(diabetesButton).not.toHaveClass('bg-emerald-50');
  });

  it('should add custom medication', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Navigate to step 3
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));

    expect(screen.getByText('Current Medications')).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Enter medication name/i);
    fireEvent.change(input, { target: { value: 'Metformin' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add' }));

    expect(screen.getByText('Metformin')).toBeInTheDocument();
  });

  it('should toggle allergy selection on step 4', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Navigate to step 4
    for (let i = 0; i < 3; i++) {
      fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    }

    expect(screen.getByText('Allergies & Physical Limitations')).toBeInTheDocument();

    const dairyButton = screen.getByRole('button', { name: 'Dairy' });
    fireEvent.click(dairyButton);
    expect(dairyButton).toHaveClass('bg-emerald-50');
  });

  it('should add custom injury on step 4', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Navigate to step 4
    for (let i = 0; i < 3; i++) {
      fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    }

    const input = screen.getByPlaceholderText(/knee injury/i);
    fireEvent.change(input, { target: { value: 'Lower back pain' } });

    const addButtons = screen.getAllByRole('button', { name: 'Add' });
    fireEvent.click(addButtons[0]);

    expect(screen.getByText('Lower back pain')).toBeInTheDocument();
  });

  it('should select primary goal on step 5', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Navigate to step 5
    for (let i = 0; i < 4; i++) {
      fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    }

    expect(screen.getByText('Goals & Preferences')).toBeInTheDocument();

    const loseWeightButton = screen.getByRole('button', { name: 'Lose Weight' });
    fireEvent.click(loseWeightButton);
    expect(loseWeightButton).toHaveClass('bg-emerald-50');
  });

  it('should call createProfile and onComplete on submit', async () => {
    const mockProfile = {
      user_id: mockUserId,
      age: 18,
      height_cm: 170,
      weight_kg: 70,
      gender: 'prefer_not_to_say',
      injuries: [],
      intolerances: [],
      allergies: [],
      health_conditions: [],
      medications: [],
      dietary_pref: 'omnivore',
      fitness_level: 'beginner',
      primary_goal: 'maintain',
    };

    (api.createProfile as jest.Mock).mockResolvedValueOnce(mockProfile);

    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Navigate to step 5
    for (let i = 0; i < 4; i++) {
      fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    }

    // Click Complete Setup
    const completeButton = screen.getByRole('button', { name: /Complete Setup/i });
    fireEvent.click(completeButton);

    await waitFor(() => {
      expect(api.createProfile).toHaveBeenCalledWith(mockUserId, expect.any(Object));
      expect(mockOnComplete).toHaveBeenCalledWith(mockProfile);
    });
  });

  it('should show error message on profile creation failure', async () => {
    (api.createProfile as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Navigate to step 5
    for (let i = 0; i < 4; i++) {
      fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    }

    // Click Complete Setup
    fireEvent.click(screen.getByRole('button', { name: /Complete Setup/i }));

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('should update progress bar correctly', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Step 1: 20%
    expect(screen.getByText('20%')).toBeInTheDocument();

    // Step 2: 40%
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    expect(screen.getByText('40%')).toBeInTheDocument();

    // Step 3: 60%
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('should clear "None" when selecting a specific health condition', () => {
    render(<Onboarding userId={mockUserId} onComplete={mockOnComplete} />);

    // Navigate to step 2
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));

    // Select "None"
    const noneButton = screen.getByRole('button', { name: 'None' });
    fireEvent.click(noneButton);
    expect(noneButton).toHaveClass('bg-emerald-50');

    // Select "Diabetes" - should clear "None"
    const diabetesButton = screen.getByRole('button', { name: 'Diabetes' });
    fireEvent.click(diabetesButton);
    expect(diabetesButton).toHaveClass('bg-emerald-50');
    expect(noneButton).not.toHaveClass('bg-emerald-50');
  });
});
