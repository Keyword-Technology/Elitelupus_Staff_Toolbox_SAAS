'use client';

import { useState, useEffect } from 'react';
import { sitAPI } from '@/lib/api';
import {
  VideoCameraIcon,
  MagnifyingGlassIcon,
  CogIcon,
  CheckIcon,
} from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';

interface SitPreferences {
  recording_enabled: boolean;
  ocr_enabled: boolean;
  auto_start_recording: boolean;
  auto_stop_recording: boolean;
  ocr_scan_interval_ms: number;
  ocr_popup_region_enabled: boolean;
  ocr_chat_region_enabled: boolean;
  video_quality: 'low' | 'medium' | 'high';
  max_recording_minutes: number;
  show_recording_preview: boolean;
  confirm_before_start: boolean;
}

const DEFAULT_PREFERENCES: SitPreferences = {
  recording_enabled: true,
  ocr_enabled: true,
  auto_start_recording: true,
  auto_stop_recording: true,
  ocr_scan_interval_ms: 1500,
  ocr_popup_region_enabled: true,
  ocr_chat_region_enabled: true,
  video_quality: 'medium',
  max_recording_minutes: 30,
  show_recording_preview: true,
  confirm_before_start: false,
};

interface SitRecordingSettingsProps {
  className?: string;
}

export function SitRecordingSettings({ className = '' }: SitRecordingSettingsProps) {
  const [preferences, setPreferences] = useState<SitPreferences>(DEFAULT_PREFERENCES);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  // Load preferences
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await sitAPI.getPreferences();
        setPreferences(response.data);
      } catch (err) {
        // Use defaults if no preferences exist
        console.log('Using default sit preferences');
      } finally {
        setIsLoading(false);
      }
    };

    loadPreferences();
  }, []);

  // Update a preference
  const updatePreference = <K extends keyof SitPreferences>(
    key: K,
    value: SitPreferences[K]
  ) => {
    setPreferences((prev) => ({ ...prev, [key]: value }));
    setIsDirty(true);
  };

  // Save preferences
  const savePreferences = async () => {
    setIsSaving(true);
    try {
      await sitAPI.updatePreferences(preferences);
      setIsDirty(false);
      toast.success('Sit recording preferences saved');
    } catch (err) {
      toast.error('Failed to save preferences');
      console.error('Failed to save preferences:', err);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className={`bg-dark-card rounded-lg border border-dark-border p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-dark-hover rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-dark-hover rounded w-full"></div>
            <div className="h-4 bg-dark-hover rounded w-3/4"></div>
            <div className="h-4 bg-dark-hover rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-dark-card rounded-lg border border-dark-border ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-dark-border flex items-center gap-3">
        <VideoCameraIcon className="w-6 h-6 text-primary-500" />
        <div>
          <h2 className="text-lg font-semibold text-white">Sit Recording Settings</h2>
          <p className="text-sm text-gray-400">Configure screen recording and OCR auto-detection</p>
        </div>
      </div>

      {/* Settings Form */}
      <div className="p-6 space-y-6">
        {/* Recording Section */}
        <div>
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <VideoCameraIcon className="w-4 h-4" />
            Recording
          </h3>
          <div className="space-y-4">
            {/* Enable Recording */}
            <label className="flex items-center justify-between">
              <div>
                <div className="text-white">Enable Recording</div>
                <div className="text-sm text-gray-500">Record your screen during sits</div>
              </div>
              <input
                type="checkbox"
                checked={preferences.recording_enabled}
                onChange={(e) => updatePreference('recording_enabled', e.target.checked)}
                className="w-5 h-5 rounded border-dark-border bg-dark-hover text-primary-500 
                  focus:ring-primary-500 focus:ring-offset-0"
              />
            </label>

            {/* Auto-start Recording */}
            <label className="flex items-center justify-between">
              <div>
                <div className="text-white">Auto-start Recording</div>
                <div className="text-sm text-gray-500">Start recording when sit begins</div>
              </div>
              <input
                type="checkbox"
                checked={preferences.auto_start_recording}
                onChange={(e) => updatePreference('auto_start_recording', e.target.checked)}
                disabled={!preferences.recording_enabled}
                className="w-5 h-5 rounded border-dark-border bg-dark-hover text-primary-500 
                  focus:ring-primary-500 focus:ring-offset-0 disabled:opacity-50"
              />
            </label>

            {/* Auto-stop Recording */}
            <label className="flex items-center justify-between">
              <div>
                <div className="text-white">Auto-stop Recording</div>
                <div className="text-sm text-gray-500">Stop recording when sit ends</div>
              </div>
              <input
                type="checkbox"
                checked={preferences.auto_stop_recording}
                onChange={(e) => updatePreference('auto_stop_recording', e.target.checked)}
                disabled={!preferences.recording_enabled}
                className="w-5 h-5 rounded border-dark-border bg-dark-hover text-primary-500 
                  focus:ring-primary-500 focus:ring-offset-0 disabled:opacity-50"
              />
            </label>

            {/* Video Quality */}
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white">Video Quality</div>
                <div className="text-sm text-gray-500">Higher quality = larger files</div>
              </div>
              <select
                value={preferences.video_quality}
                onChange={(e) => updatePreference('video_quality', e.target.value as 'low' | 'medium' | 'high')}
                disabled={!preferences.recording_enabled}
                className="px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                  text-white focus:outline-none focus:border-primary-500 disabled:opacity-50"
              >
                <option value="low">Low (1 Mbps)</option>
                <option value="medium">Medium (2.5 Mbps)</option>
                <option value="high">High (5 Mbps)</option>
              </select>
            </div>

            {/* Max Recording Duration */}
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white">Max Recording Duration</div>
                <div className="text-sm text-gray-500">Auto-stop after this time</div>
              </div>
              <select
                value={preferences.max_recording_minutes}
                onChange={(e) => updatePreference('max_recording_minutes', parseInt(e.target.value))}
                disabled={!preferences.recording_enabled}
                className="px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                  text-white focus:outline-none focus:border-primary-500 disabled:opacity-50"
              >
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
                <option value={45}>45 minutes</option>
                <option value={60}>60 minutes</option>
              </select>
            </div>

            {/* Show Recording Preview */}
            <label className="flex items-center justify-between">
              <div>
                <div className="text-white">Show Recording Preview</div>
                <div className="text-sm text-gray-500">Display preview in panel</div>
              </div>
              <input
                type="checkbox"
                checked={preferences.show_recording_preview}
                onChange={(e) => updatePreference('show_recording_preview', e.target.checked)}
                disabled={!preferences.recording_enabled}
                className="w-5 h-5 rounded border-dark-border bg-dark-hover text-primary-500 
                  focus:ring-primary-500 focus:ring-offset-0 disabled:opacity-50"
              />
            </label>
          </div>
        </div>

        {/* OCR Section */}
        <div className="pt-6 border-t border-dark-border">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <MagnifyingGlassIcon className="w-4 h-4" />
            OCR Auto-Detection
          </h3>
          <div className="space-y-4">
            {/* Enable OCR */}
            <label className="flex items-center justify-between">
              <div>
                <div className="text-white">Enable OCR Detection</div>
                <div className="text-sm text-gray-500">Auto-detect sit events from screen</div>
              </div>
              <input
                type="checkbox"
                checked={preferences.ocr_enabled}
                onChange={(e) => updatePreference('ocr_enabled', e.target.checked)}
                className="w-5 h-5 rounded border-dark-border bg-dark-hover text-primary-500 
                  focus:ring-primary-500 focus:ring-offset-0"
              />
            </label>

            {/* Chat Region */}
            <label className="flex items-center justify-between">
              <div>
                <div className="text-white">Scan Chat Region</div>
                <div className="text-sm text-gray-500">Detect [Elite Reports] messages</div>
              </div>
              <input
                type="checkbox"
                checked={preferences.ocr_chat_region_enabled}
                onChange={(e) => updatePreference('ocr_chat_region_enabled', e.target.checked)}
                disabled={!preferences.ocr_enabled}
                className="w-5 h-5 rounded border-dark-border bg-dark-hover text-primary-500 
                  focus:ring-primary-500 focus:ring-offset-0 disabled:opacity-50"
              />
            </label>

            {/* Popup Region */}
            <label className="flex items-center justify-between">
              <div>
                <div className="text-white">Scan Popup Region</div>
                <div className="text-sm text-gray-500">Detect report popup UI</div>
              </div>
              <input
                type="checkbox"
                checked={preferences.ocr_popup_region_enabled}
                onChange={(e) => updatePreference('ocr_popup_region_enabled', e.target.checked)}
                disabled={!preferences.ocr_enabled}
                className="w-5 h-5 rounded border-dark-border bg-dark-hover text-primary-500 
                  focus:ring-primary-500 focus:ring-offset-0 disabled:opacity-50"
              />
            </label>

            {/* Scan Interval */}
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white">Scan Interval</div>
                <div className="text-sm text-gray-500">Time between OCR scans</div>
              </div>
              <select
                value={preferences.ocr_scan_interval_ms}
                onChange={(e) => updatePreference('ocr_scan_interval_ms', parseInt(e.target.value))}
                disabled={!preferences.ocr_enabled}
                className="px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                  text-white focus:outline-none focus:border-primary-500 disabled:opacity-50"
              >
                <option value={1000}>1 second (faster, more CPU)</option>
                <option value={1500}>1.5 seconds (balanced)</option>
                <option value={2000}>2 seconds (slower, less CPU)</option>
                <option value={3000}>3 seconds (minimal)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Behavior Section */}
        <div className="pt-6 border-t border-dark-border">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
            <CogIcon className="w-4 h-4" />
            Behavior
          </h3>
          <div className="space-y-4">
            {/* Confirm Before Start */}
            <label className="flex items-center justify-between">
              <div>
                <div className="text-white">Confirm Before Auto-Start</div>
                <div className="text-sm text-gray-500">Show popup before auto-starting recording</div>
              </div>
              <input
                type="checkbox"
                checked={preferences.confirm_before_start}
                onChange={(e) => updatePreference('confirm_before_start', e.target.checked)}
                className="w-5 h-5 rounded border-dark-border bg-dark-hover text-primary-500 
                  focus:ring-primary-500 focus:ring-offset-0"
              />
            </label>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-dark-border flex justify-end">
        <button
          onClick={savePreferences}
          disabled={!isDirty || isSaving}
          className="flex items-center gap-2 px-6 py-2 bg-primary-600 hover:bg-primary-700 
            text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <CheckIcon className="w-4 h-4" />
              Save Changes
            </>
          )}
        </button>
      </div>
    </div>
  );
}

export default SitRecordingSettings;
