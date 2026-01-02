'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  VideoCameraIcon,
  StopIcon,
  PlayIcon,
  PauseIcon,
  XMarkIcon,
  ClockIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  PlusIcon,
  UserIcon,
  ExclamationTriangleIcon,
  CheckIcon,
  DocumentTextIcon,
  StarIcon,
} from '@heroicons/react/24/solid';
import { useActiveSit, SitData, SitPreferences } from '@/hooks/useActiveSit';
import { OCRRegionAdjuster } from '@/components/counters/OCRRegionAdjuster';
import { sitAPI } from '@/lib/api';
import toast from 'react-hot-toast';

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

const OUTCOME_OPTIONS = [
  { value: 'no_action', label: 'No Action Taken', color: 'bg-gray-600' },
  { value: 'false_report', label: 'False Report', color: 'bg-yellow-600' },
  { value: 'verbal_warning', label: 'Verbal Warning', color: 'bg-blue-600' },
  { value: 'formal_warning', label: 'Formal Warning', color: 'bg-orange-600' },
  { value: 'kick', label: 'Kick', color: 'bg-red-600' },
  { value: 'ban', label: 'Ban', color: 'bg-red-800' },
  { value: 'escalated', label: 'Escalated to Higher Staff', color: 'bg-purple-600' },
  { value: 'other', label: 'Other', color: 'bg-gray-500' },
];

const BAN_DURATION_OPTIONS = [
  { value: '1h', label: '1 Hour' },
  { value: '6h', label: '6 Hours' },
  { value: '12h', label: '12 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '3d', label: '3 Days' },
  { value: '1w', label: '1 Week' },
  { value: '2w', label: '2 Weeks' },
  { value: '1m', label: '1 Month' },
  { value: 'perm', label: 'Permanent' },
];

const QUICK_ACTIONS = [
  { label: 'RDM', value: 'rdm' },
  { label: 'NLR', value: 'nlr' },
  { label: 'RDA', value: 'rda' },
  { label: 'FailRP', value: 'failrp' },
  { label: 'Prop Abuse', value: 'propblock' },
  { label: 'Harassment', value: 'harassment' },
];

interface SitNote {
  id: string;
  content: string;
  timestamp_seconds: number;
  created_at: string;
}

export default function OCRSitsPage() {
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
    forceReset,
  } = useActiveSit();

  // Local state
  const [showRegionAdjuster, setShowRegionAdjuster] = useState(false);
  const [notes, setNotes] = useState<SitNote[]>([]);
  const [newNote, setNewNote] = useState('');
  const [steamIdReporter, setSteamIdReporter] = useState('');
  const [steamIdReported, setSteamIdReported] = useState('');
  const [editingSit, setEditingSit] = useState<Partial<SitData>>({});
  
  // Post-sit modal state
  const [outcomeData, setOutcomeData] = useState({
    outcome: 'no_action',
    outcome_notes: '',
    ban_duration: '',
  });

  const notesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new notes added
  useEffect(() => {
    notesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [notes]);

  // Load notes when sit is active
  useEffect(() => {
    if (sit?.id) {
      loadNotes();
    } else {
      setNotes([]);
    }
  }, [sit?.id]);

  const loadNotes = async () => {
    if (!sit?.id) return;
    try {
      const response = await sitAPI.getNotes(sit.id);
      setNotes(response.data || []);
    } catch (err) {
      console.error('Failed to load notes:', err);
    }
  };

  const addNote = async () => {
    if (!sit?.id || !newNote.trim()) return;
    
    try {
      await sitAPI.createNote(sit.id, {
        note_type: 'general',
        content: newNote,
        timestamp_seconds: duration,
      });
      setNewNote('');
      loadNotes();
      toast.success('Note added');
    } catch (err) {
      toast.error('Failed to add note');
    }
  };

  const addQuickNote = async (type: string) => {
    if (!sit?.id) return;
    
    try {
      await sitAPI.createNote(sit.id, {
        note_type: 'quick_action',
        content: `Quick action: ${type.toUpperCase()}`,
        timestamp_seconds: duration,
      });
      // Also update the report type
      await updateSit({ report_type: type });
      loadNotes();
      toast.success(`Added ${type.toUpperCase()}`);
    } catch (err) {
      toast.error('Failed to add quick note');
    }
  };

  const handleStartMonitoring = async () => {
    console.log('[OCRSitsPage] Start OCR Monitoring clicked');
    try {
      console.log('[OCRSitsPage] Requesting screen capture...');
      await recording.startRecording();
      console.log('[OCRSitsPage] Screen capture started');
      
      // Wait for stream to be ready
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const currentStream = recording.getStream();
      console.log('[OCRSitsPage] Stream status:', {
        hasStream: !!currentStream,
        active: currentStream?.active,
        tracks: currentStream?.getTracks().length,
      });
      
      if (!currentStream || !currentStream.active) {
        throw new Error('Screen capture stream not available');
      }
      
      console.log('[OCRSitsPage] Starting OCR scanning...');
      await ocr.startScanning(currentStream);
      console.log('[OCRSitsPage] OCR scanning started successfully');
    } catch (err) {
      console.error('[OCRSitsPage] Failed to start monitoring:', err);
      toast.error('Failed to start monitoring: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const handleStopMonitoring = () => {
    ocr.stopScanning();
    recording.stopRecording();
  };

  const handleCompleteSit = async () => {
    if (!sit?.id) return;
    
    try {
      // Update sit with outcome
      await sitAPI.update(sit.id, {
        outcome: outcomeData.outcome,
        outcome_notes: outcomeData.outcome_notes,
        ban_duration: outcomeData.outcome === 'ban' ? outcomeData.ban_duration : '',
      });
      
      toast.success('Sit completed!');
      
      // Reset outcome form
      setOutcomeData({
        outcome: 'no_action',
        outcome_notes: '',
        ban_duration: '',
      });
      
      // Complete and reset for next sit
      completeSit();
    } catch (err) {
      toast.error('Failed to complete sit');
      console.error('Failed to complete sit:', err);
    }
  };

  const handleDiscardSit = async () => {
    if (!sit?.id) return;
    
    try {
      await sitAPI.delete(sit.id);
      toast.success('Sit discarded');
      completeSit();
    } catch (err) {
      toast.error('Failed to discard sit');
    }
  };

  // Check for valid active sit
  const hasValidActiveSit = isActive && sit && sit.started_at && !isNaN(duration);

  if (!isFeatureEnabled) {
    return (
      <div className="min-h-screen bg-dark-bg">
        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="text-center">
            <VideoCameraIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">OCR Sits Feature Disabled</h2>
            <p className="text-gray-400">
              The OCR sit recording feature is currently disabled. Please contact an administrator.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Header */}
      <div className="bg-dark-card border-b border-dark-border">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <MagnifyingGlassIcon className="w-7 h-7 text-primary-400" />
                OCR Sit Recording
              </h1>
              <p className="text-gray-400 mt-1">
                Automatic sit detection with screen recording
              </p>
            </div>
            {/* Status indicator */}
            <div className="flex items-center gap-4">
              {ocr.isScanning && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 border border-blue-500/30 rounded-full">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                  <span className="text-sm text-blue-400">OCR Active</span>
                </div>
              )}
              {recording.isRecording && (
                <div className="flex items-center gap-2 px-3 py-1.5 bg-red-500/20 border border-red-500/30 rounded-full">
                  <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                  <span className="text-sm text-red-400">Recording</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 bg-red-900/30 border border-red-800 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Stuck state warning */}
        {isActive && (!sit || !sit.started_at) && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-400 font-semibold">⚠️ Stuck Sit Detected</p>
                <p className="text-red-300/70 text-sm mt-1">
                  Sit is marked as active but no valid data found.
                </p>
              </div>
              <button
                onClick={() => forceReset()}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Reset
              </button>
            </div>
          </div>
        )}

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Main panel */}
          <div className="lg:col-span-2 space-y-6">
            {/* Active Sit Card / Start Panel */}
            <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
              {!hasValidActiveSit && !showPostSitModal ? (
                // Idle / Monitoring state
                <div className="p-6">
                  <div className="text-center space-y-4">
                    <div className="flex justify-center">
                      <div className="p-4 bg-primary-500/20 rounded-full">
                        {ocr.isScanning ? (
                          <MagnifyingGlassIcon className="w-16 h-16 text-primary-400 animate-pulse" />
                        ) : (
                          <VideoCameraIcon className="w-16 h-16 text-primary-400" />
                        )}
                      </div>
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-white mb-2">
                        {ocr.isScanning ? 'OCR Monitoring Active' : 'Ready to Monitor'}
                      </h3>
                      <p className="text-gray-400 text-sm">
                        {ocr.isScanning
                          ? 'Scanning your screen for sit events. A sit will automatically start when detected.'
                          : 'Start monitoring to automatically detect when you claim a sit in-game.'}
                      </p>
                    </div>
                    
                    {/* Control buttons */}
                    <div className="flex gap-3 justify-center pt-2">
                      {!ocr.isScanning ? (
                        <>
                          <button
                            onClick={() => startSit()}
                            disabled={isLoading}
                            className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 
                              text-white rounded-lg transition-colors disabled:opacity-50"
                          >
                            <PlayIcon className="w-5 h-5" />
                            <span>Start Manually</span>
                          </button>
                          <button
                            onClick={handleStartMonitoring}
                            disabled={isLoading}
                            className="flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 
                              text-white rounded-lg transition-colors disabled:opacity-50"
                          >
                            <MagnifyingGlassIcon className="w-5 h-5" />
                            <span>Start OCR Monitoring</span>
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={handleStopMonitoring}
                            className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 
                              text-white rounded-lg transition-colors"
                          >
                            <StopIcon className="w-5 h-5" />
                            <span>Stop Monitoring</span>
                          </button>
                          <button
                            onClick={() => setShowRegionAdjuster(true)}
                            className="flex items-center gap-2 px-6 py-3 bg-gray-600 hover:bg-gray-700 
                              text-white rounded-lg transition-colors"
                          >
                            <AdjustmentsHorizontalIcon className="w-5 h-5" />
                            <span>Adjust Regions</span>
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* OCR Debug Panel when monitoring */}
                  {ocr.isScanning && (
                    <div className="mt-6 space-y-4">
                      <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                        <div className="flex items-center gap-2 justify-center mb-2">
                          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                          <span className="text-blue-400 font-medium">
                            {ocr.scanCount} scans performed
                          </span>
                        </div>
                        <div className="text-xs text-gray-400 text-center">
                          Looking for: "Elite Reports", "claimed", "closed", "CLAIM REPORT", "CLOSE REPORT"
                        </div>
                      </div>
                      
                      {/* Debug output */}
                      <div className="p-3 bg-gray-800 border border-gray-700 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-semibold text-gray-300">Last Scan Text</span>
                          <span className="text-xs text-gray-500">
                            {ocr.lastScanTime ? new Date(ocr.lastScanTime).toLocaleTimeString() : 'Never'}
                          </span>
                        </div>
                        <div className="text-xs font-mono text-gray-300 bg-gray-900 p-2 rounded max-h-24 overflow-y-auto whitespace-pre-wrap break-all">
                          {ocr.lastDetectedText || 'No text detected yet...'}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : showPostSitModal ? (
                // Post-sit completion form
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-green-500/20 rounded-full">
                      <CheckIcon className="w-6 h-6 text-green-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-white">Complete Sit Report</h3>
                      <p className="text-sm text-gray-400">Select outcome and add any final notes</p>
                    </div>
                  </div>

                  {/* Sit Summary */}
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    <div className="bg-dark-hover rounded-lg p-3 text-center">
                      <ClockIcon className="w-5 h-5 text-primary-400 mx-auto mb-1" />
                      <div className="text-xs text-gray-500">Duration</div>
                      <div className="text-white font-semibold">{formatDuration(duration)}</div>
                    </div>
                    <div className="bg-dark-hover rounded-lg p-3 text-center">
                      <UserIcon className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                      <div className="text-xs text-gray-500">Reporter</div>
                      <div className="text-white font-semibold text-sm truncate">
                        {sit?.reporter_name || 'Unknown'}
                      </div>
                    </div>
                    <div className="bg-dark-hover rounded-lg p-3 text-center">
                      <ExclamationTriangleIcon className="w-5 h-5 text-orange-400 mx-auto mb-1" />
                      <div className="text-xs text-gray-500">Type</div>
                      <div className="text-white font-semibold text-sm">
                        {sit?.report_type?.toUpperCase() || 'N/A'}
                      </div>
                    </div>
                  </div>

                  {/* Recording Preview */}
                  {recording.previewUrl && (
                    <div className="mb-6 border border-dark-border rounded-lg overflow-hidden">
                      <div className="px-3 py-2 bg-dark-hover border-b border-dark-border flex items-center gap-2">
                        <VideoCameraIcon className="w-4 h-4 text-red-400" />
                        <span className="text-sm text-gray-400">Recording Preview</span>
                        <span className="text-xs text-gray-500 ml-auto">
                          {formatDuration(recording.duration)}
                        </span>
                      </div>
                      <video
                        src={recording.previewUrl}
                        controls
                        className="w-full max-h-48 object-contain bg-black"
                      />
                    </div>
                  )}

                  {/* Outcome Selection */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-300 mb-3">
                      Outcome
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {OUTCOME_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setOutcomeData({ ...outcomeData, outcome: option.value })}
                          className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                            outcomeData.outcome === option.value
                              ? `${option.color} text-white ring-2 ring-white/30`
                              : 'bg-dark-hover text-gray-300 hover:bg-dark-border'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Ban Duration (conditional) */}
                  {outcomeData.outcome === 'ban' && (
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Ban Duration
                      </label>
                      <select
                        value={outcomeData.ban_duration}
                        onChange={(e) => setOutcomeData({ ...outcomeData, ban_duration: e.target.value })}
                        className="w-full px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                          text-white focus:outline-none focus:border-primary-500"
                      >
                        <option value="">Select duration...</option>
                        {BAN_DURATION_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Outcome Notes */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Additional Notes
                    </label>
                    <textarea
                      value={outcomeData.outcome_notes}
                      onChange={(e) => setOutcomeData({ ...outcomeData, outcome_notes: e.target.value })}
                      placeholder="Any additional notes about this sit..."
                      rows={3}
                      className="w-full px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                        text-white focus:outline-none focus:border-primary-500 resize-none"
                    />
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <button
                      onClick={handleCompleteSit}
                      disabled={isLoading}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-3 
                        bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      <CheckIcon className="w-5 h-5" />
                      <span>Complete & Save</span>
                    </button>
                    <button
                      onClick={handleDiscardSit}
                      disabled={isLoading}
                      className="px-4 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      <XMarkIcon className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ) : (
                // Active sit panel
                <div>
                  {/* Active sit header */}
                  <div className="px-4 py-3 bg-dark-hover border-b border-dark-border flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
                      <h3 className="font-semibold text-white">Active Sit</h3>
                      <span className="text-2xl font-mono text-white">{formatDuration(duration)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {recording.isRecording && (
                        <div className="flex items-center gap-1 text-sm text-red-400">
                          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                          <span>REC</span>
                        </div>
                      )}
                      {ocr.isScanning && (
                        <div className="flex items-center gap-1 text-sm text-blue-400">
                          <MagnifyingGlassIcon className="w-4 h-4" />
                          <span>{ocr.scanCount}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Sit details */}
                  <div className="p-4 space-y-4">
                    {/* Quick info */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Reporter</label>
                        <input
                          type="text"
                          value={editingSit.reporter_name ?? sit?.reporter_name ?? ''}
                          onChange={(e) => setEditingSit({ ...editingSit, reporter_name: e.target.value })}
                          onBlur={() => editingSit.reporter_name && updateSit({ reporter_name: editingSit.reporter_name })}
                          placeholder="Auto-detected or enter name"
                          className="w-full px-3 py-2 bg-dark-hover border border-dark-border rounded-lg 
                            text-white text-sm focus:outline-none focus:border-primary-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Reported Player</label>
                        <input
                          type="text"
                          value={editingSit.reported_player ?? sit?.reported_player ?? ''}
                          onChange={(e) => setEditingSit({ ...editingSit, reported_player: e.target.value })}
                          onBlur={() => editingSit.reported_player && updateSit({ reported_player: editingSit.reported_player })}
                          placeholder="Enter player name"
                          className="w-full px-3 py-2 bg-dark-hover border border-dark-border rounded-lg 
                            text-white text-sm focus:outline-none focus:border-primary-500"
                        />
                      </div>
                    </div>

                    {/* Report type */}
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

                    {/* Quick Actions */}
                    <div>
                      <label className="block text-xs text-gray-500 mb-2">Quick Actions</label>
                      <div className="flex flex-wrap gap-2">
                        {QUICK_ACTIONS.map((action) => (
                          <button
                            key={action.value}
                            onClick={() => addQuickNote(action.value)}
                            className="px-3 py-1.5 bg-primary-600/30 hover:bg-primary-600/50 
                              text-primary-300 text-sm rounded-lg transition-colors border border-primary-600/30"
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Detection Method Indicator */}
                    <div className="text-xs text-gray-500 flex items-center gap-2">
                      <span>Detection:</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        sit?.detection_method === 'manual' 
                          ? 'bg-gray-600 text-gray-300'
                          : 'bg-blue-600/30 text-blue-400'
                      }`}>
                        {sit?.detection_method === 'manual' ? 'Manual' :
                         sit?.detection_method === 'ocr_chat' ? 'OCR (Chat)' :
                         sit?.detection_method === 'ocr_popup' ? 'OCR (Popup)' : 'Unknown'}
                      </span>
                    </div>

                    {/* Recording Preview */}
                    {recording.previewUrl && (
                      <div className="border border-dark-border rounded-lg overflow-hidden">
                        <video
                          src={recording.previewUrl}
                          controls
                          className="w-full max-h-32 object-contain bg-black"
                        />
                      </div>
                    )}

                    {/* Control Buttons */}
                    <div className="flex gap-2 pt-2">
                      {recording.isRecording && (
                        <button
                          onClick={() => recording.isPaused ? recording.resumeRecording() : recording.pauseRecording()}
                          className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 
                            text-white rounded-lg transition-colors"
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
                      <button
                        onClick={() => endSit()}
                        disabled={isLoading}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 
                          bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50"
                      >
                        <StopIcon className="w-4 h-4" />
                        <span>End Sit</span>
                      </button>
                      <button
                        onClick={() => cancelSit()}
                        disabled={isLoading}
                        className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50"
                        title="Cancel & Discard"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right column - Notes panel */}
          <div className="space-y-6">
            {/* Notes Panel */}
            <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
              <div className="px-4 py-3 bg-dark-hover border-b border-dark-border">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <DocumentTextIcon className="w-5 h-5 text-primary-400" />
                  Sit Notes
                </h3>
              </div>
              
              <div className="p-4">
                {/* Notes list */}
                <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
                  {notes.length === 0 ? (
                    <p className="text-gray-500 text-sm text-center py-4">
                      {hasValidActiveSit ? 'No notes yet. Add a note below.' : 'Start a sit to add notes.'}
                    </p>
                  ) : (
                    notes.map((note) => (
                      <div key={note.id} className="bg-dark-hover rounded-lg p-3">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm text-white">{note.content}</p>
                          <span className="text-xs text-gray-500 whitespace-nowrap">
                            [{formatDuration(note.timestamp_seconds)}]
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                  <div ref={notesEndRef} />
                </div>

                {/* Add note input */}
                {hasValidActiveSit && (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newNote}
                      onChange={(e) => setNewNote(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && addNote()}
                      placeholder="Add a note..."
                      className="flex-1 px-3 py-2 bg-dark-hover border border-dark-border rounded-lg 
                        text-white text-sm focus:outline-none focus:border-primary-500"
                    />
                    <button
                      onClick={addNote}
                      disabled={!newNote.trim()}
                      className="px-3 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg 
                        transition-colors disabled:opacity-50"
                    >
                      <PlusIcon className="w-5 h-5" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Steam ID Panel */}
            <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
              <div className="px-4 py-3 bg-dark-hover border-b border-dark-border">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <UserIcon className="w-5 h-5 text-blue-400" />
                  Steam IDs
                </h3>
              </div>
              
              <div className="p-4 space-y-4">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Reporter Steam ID</label>
                  <input
                    type="text"
                    value={steamIdReporter}
                    onChange={(e) => setSteamIdReporter(e.target.value)}
                    placeholder="STEAM_0:1:123456789"
                    className="w-full px-3 py-2 bg-dark-hover border border-dark-border rounded-lg 
                      text-white text-sm font-mono focus:outline-none focus:border-primary-500"
                    disabled={!hasValidActiveSit}
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Reported Steam ID</label>
                  <input
                    type="text"
                    value={steamIdReported}
                    onChange={(e) => setSteamIdReported(e.target.value)}
                    placeholder="STEAM_0:1:123456789"
                    className="w-full px-3 py-2 bg-dark-hover border border-dark-border rounded-lg 
                      text-white text-sm font-mono focus:outline-none focus:border-primary-500"
                    disabled={!hasValidActiveSit}
                  />
                </div>
                <p className="text-xs text-gray-500">
                  Paste Steam IDs from in-game console for record-keeping.
                </p>
              </div>
            </div>

            {/* Player Rating (if detected) */}
            {sit?.player_rating !== undefined && sit?.player_rating !== null && (
              <div className="bg-dark-card rounded-lg border border-yellow-800/50 overflow-hidden">
                <div className="px-4 py-3 bg-yellow-900/20 border-b border-yellow-800/30">
                  <h3 className="font-semibold text-yellow-400 flex items-center gap-2">
                    <StarIcon className="w-5 h-5" />
                    Player Rating Received
                  </h3>
                </div>
                <div className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <StarIcon
                          key={star}
                          className={`w-6 h-6 ${
                            star <= (sit.player_rating || 0) ? 'text-yellow-400' : 'text-gray-600'
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-gray-400 text-sm">
                      ({sit.player_rating_credits || 0} credits)
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Region Adjuster Modal */}
      {showRegionAdjuster && (
        <OCRRegionAdjuster
          stream={recording.getStream()}
          onRegionsChange={(newRegions) => {
            console.log('[OCRSitsPage] Regions updated:', newRegions);
          }}
          onClose={() => setShowRegionAdjuster(false)}
        />
      )}
    </div>
  );
}
