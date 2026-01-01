'use client';

import { useState, useEffect } from 'react';
import {
  VideoCameraIcon,
  StopIcon,
  PlayIcon,
  PauseIcon,
  XMarkIcon,
  ClockIcon,
  EyeIcon,
  CogIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/solid';
import { useActiveSit, SitData } from '@/hooks/useActiveSit';

interface ActiveSitPanelProps {
  className?: string;
  compact?: boolean;
}

// Format seconds to MM:SS or HH:MM:SS
function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

export function ActiveSitPanel({ className = '', compact = false }: ActiveSitPanelProps) {
  const {
    isActive,
    sit,
    duration,
    isLoading,
    error,
    preferences,
    isFeatureEnabled,
    recording,
    ocr,
    startSit,
    endSit,
    cancelSit,
    showPostSitModal,
    closePostSitModal,
    completeSit,
    updateSit,
  } = useActiveSit();

  const [showSettings, setShowSettings] = useState(false);
  const [showDetails, setShowDetails] = useState(!compact);
  const [editingSit, setEditingSit] = useState<Partial<SitData>>({});

  // Don't render if feature is disabled
  if (!isFeatureEnabled) {
    return null;
  }

  // Compact idle state
  if (!isActive && compact) {
    return (
      <button
        onClick={() => startSit()}
        disabled={isLoading}
        className={`flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 
          text-white rounded-lg transition-colors disabled:opacity-50 ${className}`}
      >
        <VideoCameraIcon className="w-5 h-5" />
        <span>Start Sit Recording</span>
      </button>
    );
  }

  return (
    <div className={`bg-dark-card rounded-lg border border-dark-border overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 bg-dark-hover border-b border-dark-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-red-500 animate-pulse' : 'bg-gray-500'}`} />
          <h3 className="font-semibold text-white">
            {isActive ? 'Active Sit' : 'Sit Recording'}
          </h3>
          {isActive && (
            <span className="text-lg font-mono text-white">
              {formatDuration(duration)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isActive && preferences?.show_recording_preview && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-2 hover:bg-dark-border rounded-lg transition-colors"
              title={showDetails ? 'Hide details' : 'Show details'}
            >
              <EyeIcon className="w-5 h-5 text-gray-400" />
            </button>
          )}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 hover:bg-dark-border rounded-lg transition-colors"
            title="Settings"
          >
            <CogIcon className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Recording Status */}
      {isActive && recording.isRecording && (
        <div className="px-4 py-2 bg-red-900/20 border-b border-red-900/30 flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          <span className="text-sm text-red-400">Recording</span>
          <span className="text-sm text-gray-400 ml-auto">
            {formatDuration(recording.duration)}
          </span>
        </div>
      )}

      {/* OCR Status */}
      {isActive && ocr.isScanning && (
        <div className="px-4 py-2 bg-blue-900/20 border-b border-blue-900/30 flex items-center gap-2">
          <MagnifyingGlassIcon className="w-4 h-4 text-blue-400 animate-pulse" />
          <span className="text-sm text-blue-400">OCR Scanning</span>
          <span className="text-sm text-gray-400 ml-auto">
            {ocr.scanCount} scans
          </span>
        </div>
      )}

      {/* Main Content */}
      <div className="p-4">
        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-400">
            {error}
          </div>
        )}

        {!isActive ? (
          // Not Active - Start Button
          <div className="text-center">
            <p className="text-gray-400 mb-4">
              Start a sit to begin recording and auto-detect report events.
            </p>
            <button
              onClick={() => startSit()}
              disabled={isLoading}
              className="flex items-center justify-center gap-2 w-full px-4 py-3 
                bg-green-600 hover:bg-green-700 text-white rounded-lg 
                transition-colors disabled:opacity-50"
            >
              <PlayIcon className="w-5 h-5" />
              <span>Start Sit Recording</span>
            </button>
          </div>
        ) : (
          // Active Sit UI
          <div className="space-y-4">
            {/* Sit Details */}
            {showDetails && (
              <div className="space-y-3">
                {/* Reporter */}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Reporter</label>
                  <input
                    type="text"
                    value={editingSit.reporter_name ?? sit?.reporter_name ?? ''}
                    onChange={(e) => setEditingSit({ ...editingSit, reporter_name: e.target.value })}
                    onBlur={() => {
                      if (editingSit.reporter_name !== undefined) {
                        updateSit({ reporter_name: editingSit.reporter_name });
                      }
                    }}
                    placeholder="Auto-detected or enter name"
                    className="w-full px-3 py-2 bg-dark-hover border border-dark-border rounded-lg 
                      text-white text-sm focus:outline-none focus:border-primary-500"
                  />
                </div>

                {/* Reported Player */}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Reported Player</label>
                  <input
                    type="text"
                    value={editingSit.reported_player ?? sit?.reported_player ?? ''}
                    onChange={(e) => setEditingSit({ ...editingSit, reported_player: e.target.value })}
                    onBlur={() => {
                      if (editingSit.reported_player !== undefined) {
                        updateSit({ reported_player: editingSit.reported_player });
                      }
                    }}
                    placeholder="Enter reported player name"
                    className="w-full px-3 py-2 bg-dark-hover border border-dark-border rounded-lg 
                      text-white text-sm focus:outline-none focus:border-primary-500"
                  />
                </div>

                {/* Report Type */}
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Report Type</label>
                  <select
                    value={editingSit.report_type ?? sit?.report_type ?? ''}
                    onChange={(e) => {
                      setEditingSit({ ...editingSit, report_type: e.target.value });
                      updateSit({ report_type: e.target.value });
                    }}
                    className="w-full px-3 py-2 bg-dark-hover border border-dark-border rounded-lg 
                      text-white text-sm focus:outline-none focus:border-primary-500"
                  >
                    <option value="">Select type...</option>
                    <option value="rdm">RDM</option>
                    <option value="nlr">NLR</option>
                    <option value="rda">RDA</option>
                    <option value="failrp">FailRP</option>
                    <option value="propblock">Prop Block/Abuse</option>
                    <option value="harassment">Harassment</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                {/* Detection Method Indicator */}
                <div className="text-xs text-gray-500">
                  Detection: {sit?.detection_method === 'manual' ? 'Manual' : 
                    sit?.detection_method === 'ocr_chat' ? 'OCR (Chat)' : 
                    sit?.detection_method === 'ocr_popup' ? 'OCR (Popup)' : 'Unknown'}
                </div>
              </div>
            )}

            {/* Recording Preview */}
            {recording.previewUrl && preferences?.show_recording_preview && (
              <div className="border border-dark-border rounded-lg overflow-hidden">
                <video
                  src={recording.previewUrl}
                  controls
                  className="w-full max-h-48 object-contain bg-black"
                />
              </div>
            )}

            {/* Control Buttons */}
            <div className="flex gap-2">
              {/* Pause/Resume Recording */}
              {recording.isRecording && (
                <button
                  onClick={() => recording.isPaused ? recording.resumeRecording() : recording.pauseRecording()}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 
                    bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
                >
                  {recording.isPaused ? (
                    <>
                      <PlayIcon className="w-4 h-4" />
                      <span>Resume</span>
                    </>
                  ) : (
                    <>
                      <PauseIcon className="w-4 h-4" />
                      <span>Pause</span>
                    </>
                  )}
                </button>
              )}

              {/* End Sit */}
              <button
                onClick={() => endSit()}
                disabled={isLoading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 
                  bg-primary-600 hover:bg-primary-700 text-white rounded-lg 
                  transition-colors disabled:opacity-50"
              >
                <StopIcon className="w-4 h-4" />
                <span>End Sit</span>
              </button>

              {/* Cancel */}
              <button
                onClick={() => cancelSit()}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 px-4 py-2 
                  bg-red-600 hover:bg-red-700 text-white rounded-lg 
                  transition-colors disabled:opacity-50"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="px-4 py-3 border-t border-dark-border bg-dark-hover">
          <h4 className="text-sm font-semibold text-white mb-3">Quick Settings</h4>
          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={preferences?.recording_enabled ?? true}
                onChange={() => {/* TODO: Update preference */}}
                className="rounded border-dark-border bg-dark-card text-primary-500 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-400">Enable Recording</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={preferences?.ocr_enabled ?? true}
                onChange={() => {/* TODO: Update preference */}}
                className="rounded border-dark-border bg-dark-card text-primary-500 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-400">Enable OCR Auto-Detection</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={preferences?.auto_start_recording ?? true}
                onChange={() => {/* TODO: Update preference */}}
                className="rounded border-dark-border bg-dark-card text-primary-500 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-400">Auto-start Recording</span>
            </label>
          </div>
        </div>
      )}
    </div>
  );
}

export default ActiveSitPanel;
