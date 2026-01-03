'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import {
  CheckIcon,
  ClockIcon,
  EnvelopeIcon,
  LockClosedIcon,
  VideoCameraIcon,
  MagnifyingGlassIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface SetupWizardData {
  timezone: string;
  email: string;
  password: string;
  auto_sit_detection_enabled: boolean;
  auto_recording_enabled: boolean;
}

interface SystemSettings {
  sit_recording_available: boolean;
  ocr_available: boolean;
}

// Base steps - Features step will be conditionally added
const BASE_STEPS = [
  { id: 1, name: 'Timezone', icon: ClockIcon },
  { id: 2, name: 'Email', icon: EnvelopeIcon },
  { id: 3, name: 'Password', icon: LockClosedIcon },
];

const FEATURES_STEP = { id: 4, name: 'Features', icon: VideoCameraIcon };

export function SetupWizard() {
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  const [timezones, setTimezones] = useState<Array<{ value: string; label: string }>>([]);
  
  const [formData, setFormData] = useState<SetupWizardData>({
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    email: '',
    password: '',
    auto_sit_detection_enabled: true,
    auto_recording_enabled: true,
  });

  const [showPassword, setShowPassword] = useState(false);

  // Dynamically build steps based on system settings
  const STEPS = systemSettings?.sit_recording_available || systemSettings?.ocr_available
    ? [...BASE_STEPS, FEATURES_STEP]
    : BASE_STEPS;

  useEffect(() => {
    // Fetch system settings and timezones
    const fetchData = async () => {
      try {
        const [settingsRes, timezonesRes] = await Promise.all([
          api.get('/auth/setup-wizard/'),
          api.get('/auth/timezones/'),
        ]);
        setSystemSettings(settingsRes.data.system_settings);
        setTimezones(timezonesRes.data);
      } catch (error) {
        console.error('Error fetching setup data:', error);
      }
    };
    fetchData();
  }, []);

  const handleNext = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const submitData: any = {
        timezone: formData.timezone,
        auto_sit_detection_enabled: formData.auto_sit_detection_enabled,
        auto_recording_enabled: formData.auto_recording_enabled,
      };

      // Only include email if provided
      if (formData.email.trim()) {
        submitData.email = formData.email;
      }

      // Only include password if provided
      if (formData.password.trim()) {
        submitData.password = formData.password;
      }

      await api.post('/auth/setup-wizard/', submitData);
      
      toast.success('Setup completed successfully!');
      await refreshUser();
      router.push('/dashboard');
    } catch (error: any) {
      console.error('Setup wizard error:', error);
      toast.error(error?.response?.data?.error || 'Failed to complete setup');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <ClockIcon className="w-16 h-16 text-primary-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Select Your Timezone</h2>
              <p className="text-gray-400">
                This helps us display times correctly for your location.
              </p>
            </div>
            
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">
                Timezone
              </label>
              <select
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                className="w-full px-4 py-3 bg-dark-hover border border-dark-border rounded-lg 
                  text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              >
                {timezones.map((tz) => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </select>
              <div className="flex items-start gap-2 mt-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <InformationCircleIcon className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-300">
                  Your timezone is used for displaying sit timestamps, activity logs, and scheduling features.
                  You can change this later in your settings.
                </p>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <EnvelopeIcon className="w-16 h-16 text-primary-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Add Your Email</h2>
              <p className="text-gray-400">
                Optional, but recommended for account recovery and notifications.
              </p>
            </div>
            
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">
                Email Address (Optional)
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="your.email@example.com"
                className="w-full px-4 py-3 bg-dark-hover border border-dark-border rounded-lg 
                  text-white placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <div className="flex items-start gap-2 mt-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <InformationCircleIcon className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-300">
                  Your email will be used for account recovery, important notifications, and future features.
                  We will never share your email with third parties. You can skip this step and add it later.
                </p>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <LockClosedIcon className="w-16 h-16 text-primary-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Set a Password</h2>
              <p className="text-gray-400">
                {user?.steam_id || user?.discord_id 
                  ? 'Set a password to enable traditional login alongside OAuth.'
                  : 'Secure your account with a strong password.'
                }
              </p>
            </div>
            
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-300">
                Password (Optional)
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Enter a strong password (min. 8 characters)"
                  className="w-full px-4 py-3 bg-dark-hover border border-dark-border rounded-lg 
                    text-white placeholder-gray-500 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              <div className="flex items-start gap-2 mt-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <InformationCircleIcon className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-300">
                  {user?.steam_id || user?.discord_id ? (
                    <>
                      Since you logged in with {user.steam_id ? 'Steam' : 'Discord'}, a password is optional.
                      Setting one allows you to also log in with username/password.
                    </>
                  ) : (
                    <>
                      Choose a strong password with at least 8 characters. Include a mix of letters, numbers,
                      and special characters for better security.
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <VideoCameraIcon className="w-16 h-16 text-primary-500 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">Enable Smart Features</h2>
              <p className="text-gray-400">
                Configure automatic sit detection and recording features.
              </p>
            </div>
            
            <div className="space-y-4">
              {/* Auto Sit Detection */}
              <div className="p-4 bg-dark-hover border border-dark-border rounded-lg">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.auto_sit_detection_enabled}
                    onChange={(e) =>
                      setFormData({ ...formData, auto_sit_detection_enabled: e.target.checked })
                    }
                    className="mt-1 w-5 h-5 rounded border-gray-600 text-primary-500 
                      focus:ring-primary-500 focus:ring-offset-0"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <MagnifyingGlassIcon className="w-5 h-5 text-primary-400" />
                      <span className="font-semibold text-white">Auto Sit Detection (OCR)</span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">
                      Automatically detect when you claim and close sits by scanning your game screen.
                      Uses browser-based OCR to identify sit events in real-time.
                    </p>
                    <div className="mt-2 p-2 bg-blue-500/10 border border-blue-500/20 rounded text-xs text-blue-300">
                      <strong>How it works:</strong> When enabled, the toolbox will scan specific regions of your
                      Garry's Mod screen for sit-related text (like "[Elite Reports] You claimed..."). This happens
                      entirely in your browser using OCR technology.
                    </div>
                  </div>
                </label>
              </div>

              {/* Auto Recording */}
              {systemSettings?.sit_recording_available && (
                <div className="p-4 bg-dark-hover border border-dark-border rounded-lg">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.auto_recording_enabled}
                      onChange={(e) =>
                        setFormData({ ...formData, auto_recording_enabled: e.target.checked })
                      }
                      className="mt-1 w-5 h-5 rounded border-gray-600 text-primary-500 
                        focus:ring-primary-500 focus:ring-offset-0"
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <VideoCameraIcon className="w-5 h-5 text-red-400" />
                        <span className="font-semibold text-white">Auto Screen Recording</span>
                      </div>
                      <p className="text-sm text-gray-400 mt-1">
                        Automatically start and stop screen recording during sits for evidence and review purposes.
                      </p>
                      <div className="mt-2 p-2 bg-blue-500/10 border border-blue-500/20 rounded text-xs text-blue-300">
                        <strong>How it works:</strong> When you claim a sit, screen recording starts automatically.
                        When you close the sit, recording stops and uploads. This requires the "Screen Capture API"
                        which is supported in modern browsers (Chrome, Edge, Firefox).
                      </div>
                    </div>
                  </label>
                </div>
              )}

              <div className="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <InformationCircleIcon className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-yellow-300">
                  <strong>Note:</strong> You can change these settings anytime from your dashboard settings.
                  Both features work entirely in your browser and don't send any data until you explicitly
                  save a sit recording.
                </p>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              const isCompleted = currentStep > step.id;
              const isCurrent = currentStep === step.id;
              
              return (
                <div key={step.id} className="flex items-center flex-1">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors ${
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isCurrent
                          ? 'bg-primary-500 text-white'
                          : 'bg-dark-hover text-gray-500'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckIcon className="w-6 h-6" />
                      ) : (
                        <Icon className="w-6 h-6" />
                      )}
                    </div>
                    <span
                      className={`mt-2 text-sm font-medium ${
                        isCurrent ? 'text-white' : 'text-gray-500'
                      }`}
                    >
                      {step.name}
                    </span>
                  </div>
                  {index < STEPS.length - 1 && (
                    <div
                      className={`flex-1 h-1 mx-2 mb-6 transition-colors ${
                        isCompleted ? 'bg-green-500' : 'bg-dark-hover'
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Content Card */}
        <div className="bg-dark-card rounded-xl border border-dark-border p-8">
          {renderStepContent()}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-dark-border">
            <button
              onClick={handlePrevious}
              disabled={currentStep === 1}
              className="px-6 py-2 rounded-lg border border-dark-border text-gray-300 
                hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            
            {currentStep < STEPS.length ? (
              <button
                onClick={handleNext}
                className="px-6 py-2 rounded-lg bg-primary-500 text-white 
                  hover:bg-primary-600 transition-colors"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="px-6 py-2 rounded-lg bg-green-500 text-white 
                  hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Completing...' : 'Complete Setup'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SetupWizard;
