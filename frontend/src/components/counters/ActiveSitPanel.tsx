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

  // Check if we have a valid active sit (not just isActive flag)
  const hasValidActiveSit = isActive && sit && sit.started_at && !isNaN(duration);

  // Idle state - no active sit or invalid sit data
  if (!hasValidActiveSit) {
    return (
      <div className={`bg-dark-card rounded-lg border border-dark-border p-6 ${className}`}>
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className="p-4 bg-primary-500/20 rounded-full">
              {ocr.isScanning ? (
                <MagnifyingGlassIcon className="w-12 h-12 text-primary-400 animate-pulse" />
              ) : (
                <VideoCameraIcon className="w-12 h-12 text-primary-400" />
              )}
            </div>
          </div>
          <div>
            <h3 className="text-xl font-semibold text-white mb-2">
              {ocr.isScanning ? 'OCR Monitoring Active' : 'Sit Recording Ready'}
            </h3>
            <p className="text-gray-400 text-sm mb-4">
              {ocr.isScanning 
                ? 'Scanning your screen for sit events. A sit will automatically start when detected.'
                : preferences?.ocr_enabled 
                  ? 'OCR monitoring will automatically detect when you claim a sit, or you can start manually.'
                  : 'Click the button below to manually start recording a sit.'}
            </p>
          </div>
          <div className="flex gap-3 justify-center">
            {!ocr.isScanning ? (
              <>
                <button
                  onClick={() => startSit()}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 
                    text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <PlayIcon className="w-5 h-5" />
                  <span>Start Sit Manually</span>
                </button>
                {preferences?.ocr_enabled && (
                  <button
                    onClick={async () => {
                      console.log('[UI] Start OCR Monitoring clicked');
                      try {
                        // First, request screen capture permission and start stream
                        console.log('[UI] Requesting screen capture...');
                        await recording.startRecording();
                        console.log('[UI] Screen capture started');
                        
                        // Wait for stream to be fully ready and check it's available
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        
                        const currentStream = recording.getStream();
                        console.log('[UI] Stream status:', { 
                          hasStream: !!currentStream,
                          active: currentStream?.active,
                          tracks: currentStream?.getTracks().length 
                        });
                        
                        if (!currentStream || !currentStream.active) {
                          throw new Error('Screen capture stream not available');
                        }
                        
                        console.log('[UI] Starting OCR scanning...');
                        await ocr.startScanning(currentStream); // Pass the stream directly
                        console.log('[UI] OCR scanning started successfully');
                      } catch (err) {
                        console.error('[UI] Failed to start monitoring:', err);
                        alert('Failed to start monitoring: ' + (err instanceof Error ? err.message : 'Unknown error'));
                      }
                    }}
                    disabled={isLoading || recording.isRecording}
                    className="flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 
                      text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <MagnifyingGlassIcon className="w-5 h-5" />
                    <span>{recording.isRecording ? 'Initializing...' : 'Start OCR Monitoring'}</span>
                  </button>
                )}
              </>
            ) : (
              <button
                onClick={() => {
                  ocr.stopScanning();
                  recording.stopRecording();
                }}
                className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 
                  text-white rounded-lg transition-colors"
              >
                <StopIcon className="w-5 h-5" />
                <span>Stop Monitoring</span>
              </button>
            )}
          </div>
          {ocr.isScanning && (
            <div className="mt-4 space-y-3">
              <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    <span className="text-blue-400 text-sm font-medium">
                      Monitoring: {ocr.scanCount} scans performed
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 text-center space-y-1">
                    <div>Chat: "Elite Reports", "claimed", "closed", "report", "rating"</div>
                    <div>Popup Buttons: "CLAIM REPORT", "CLOSE REPORT"</div>
                  </div>
                </div>
              </div>
              
              {/* Debug panel - shows last detected text */}
              <div className="p-3 bg-gray-800 border border-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-semibold text-gray-300">DEBUG: Last Scan Text</span>
                  <span className="text-xs text-gray-500">
                    {ocr.lastScanTime ? new Date(ocr.lastScanTime).toLocaleTimeString() : 'Never'}
                  </span>
                </div>
                <div className="text-xs font-mono text-gray-300 bg-gray-900 p-2 rounded max-h-32 overflow-y-auto whitespace-pre-wrap break-all">
                  {ocr.lastDetectedText || 'No text detected yet...'}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {ocr.lastDetectedText ? `${ocr.lastDetectedText.length} characters` : 'Waiting for scan...'}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
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
