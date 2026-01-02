'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { sitAPI } from '@/lib/api';
import { useScreenRecording, RecordingOptions } from './useScreenRecording';
import { useScreenOCR, OCRDetectionEvent, OCROptions } from './useScreenOCR';
import { playSitOpenedSound, playSitClosedSound } from '@/lib/sounds';

export interface SitData {
  id?: string;
  reporter_name: string;
  reported_player: string;
  report_type: string;
  report_reason: string;
  started_at: string;
  ended_at?: string;
  duration_seconds?: number;
  outcome: string;
  outcome_notes: string;
  ban_duration?: string;
  player_rating?: number;
  player_rating_credits?: number;
  detection_method: 'manual' | 'ocr_chat' | 'ocr_popup';
  has_recording: boolean;
}

export interface SitPreferences {
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

export interface ActiveSitState {
  isActive: boolean;
  sit: SitData | null;
  duration: number;
  isLoading: boolean;
  error: string | null;
  preferences: SitPreferences | null;
  isFeatureEnabled: boolean;
  showPostSitModal: boolean;
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

/**
 * Normalize OCR-extracted report type to match backend choices.
 * Backend accepts: rdm, nlr, rda, failrp, propblock, harassment, other
 */
function normalizeReportType(ocrType: string | undefined): string {
  if (!ocrType) return '';
  
  const normalized = ocrType.toLowerCase().trim();
  
  // Map common OCR variations to valid backend choices
  const mappings: Record<string, string> = {
    'rdm': 'rdm',
    'rom': 'rdm',  // Common OCR misread
    'rdn': 'rdm',  // Common OCR misread
    'nlr': 'nlr',
    'rda': 'rda',
    'failrp': 'failrp',
    'fail rp': 'failrp',
    'propblock': 'propblock',
    'prop block': 'propblock',
    'prop abuse': 'propblock',
    'harassment': 'harassment',
  };
  
  // Check if normalized value matches a known type
  if (mappings[normalized]) {
    return mappings[normalized];
  }
  
  // Check if it starts with a known type
  for (const [key, value] of Object.entries(mappings)) {
    if (normalized.startsWith(key) || key.startsWith(normalized)) {
      return value;
    }
  }
  
  // Default to 'other' for unrecognized types
  return 'other';
}

export function useActiveSit() {
  const [state, setState] = useState<ActiveSitState>({
    isActive: false,
    sit: null,
    duration: 0,
    isLoading: true,
    error: null,
    preferences: null,
    isFeatureEnabled: false,
    showPostSitModal: false,
  });

  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const sitIdRef = useRef<string | null>(null);
  const ocrDetectionCallbackRef = useRef<((event: OCRDetectionEvent) => void) | null>(null);

  // Screen recording hook
  const recording = useScreenRecording({
    videoQuality: state.preferences?.video_quality || 'medium',
    maxDurationMinutes: state.preferences?.max_recording_minutes || 30,
    onStop: async (blob, duration) => {
      // Upload recording when stopped
      if (sitIdRef.current && blob.size > 0) {
        try {
          const formData = new FormData();
          formData.append('recording', blob, 'sit_recording.webm');
          formData.append('duration_seconds', duration.toString());
          await sitAPI.uploadRecording(sitIdRef.current, formData);
        } catch (err) {
          console.error('Failed to upload recording:', err);
        }
      }
    },
  });

  // Screen OCR hook - use callback ref to avoid stale closures
  const ocr = useScreenOCR(recording.stream, {
    scanIntervalMs: state.preferences?.ocr_scan_interval_ms || 1500,
    enableChatRegion: state.preferences?.ocr_chat_region_enabled ?? true,
    enablePopupRegion: state.preferences?.ocr_popup_region_enabled ?? true,
    onDetection: (event) => {
      console.log('[useActiveSit] OCR detection callback triggered:', event.type);
      if (ocrDetectionCallbackRef.current) {
        ocrDetectionCallbackRef.current(event);
      } else {
        console.warn('[useActiveSit] OCR detection callback ref is null!');
      }
    },
  });

  // Load preferences and check if feature is enabled
  const loadSettings = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true }));
    
    try {
      // Check if feature is enabled system-wide
      const enabledResponse = await sitAPI.isEnabled();
      const isEnabled = enabledResponse.data?.system_enabled && enabledResponse.data?.user_recording_enabled;
      
      // Load user preferences
      let preferences = DEFAULT_PREFERENCES;
      try {
        const prefsResponse = await sitAPI.getPreferences();
        preferences = prefsResponse.data;
      } catch {
        // Use defaults if no preferences exist
      }

      // Check for any active sit
      let activeSit = null;
      try {
        console.log('[useActiveSit] 🔍 Checking for active sits from backend...');
        const activeResponse = await sitAPI.getActive();
        console.log('[useActiveSit] Backend response:', activeResponse);
        
        if (activeResponse.data) {
          activeSit = activeResponse.data;
          console.log('[useActiveSit] Active sit data received:', activeSit);
          
          // Validate sit data
          if (!activeSit.started_at || !activeSit.id) {
            console.warn('[useActiveSit] ⚠️ Active sit has invalid data, ignoring:', activeSit);
            activeSit = null;
          } else {
            sitIdRef.current = activeSit.id;
            console.log('[useActiveSit] ✅ Valid active sit found');
          }
        } else {
          console.log('[useActiveSit] No active sit in response');
        }
      } catch (err) {
        // No active sit or error fetching
        console.log('[useActiveSit] No active sit found or error:', err);
      }

      setState(prev => ({
        ...prev,
        isFeatureEnabled: isEnabled,
        preferences,
        sit: activeSit,
        isActive: !!activeSit,
        isLoading: false,
        error: null,
      }));

      // Resume duration counter if there's an active sit
      if (activeSit) {
        console.log('[useActiveSit] Resuming active sit:', {
          id: activeSit.id,
          reporter: activeSit.reporter_name,
          startedAt: activeSit.started_at,
        });
        const startTime = new Date(activeSit.started_at).getTime();
        startDurationTimer(startTime);
      } else {
        console.log('[useActiveSit] No active sit to resume');
      }
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to load sit recording settings',
      }));
    }
  }, []);

  // Start duration timer
  const startDurationTimer = useCallback((startTimeMs: number) => {
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }

    const updateDuration = () => {
      const duration = Math.round((Date.now() - startTimeMs) / 1000);
      setState(prev => ({ ...prev, duration }));
    };

    updateDuration();
    durationIntervalRef.current = setInterval(updateDuration, 1000);
  }, []);

  // Handle OCR detection events
  const handleOCRDetection = useCallback(async (event: OCRDetectionEvent) => {
    console.log('[useActiveSit] handleOCRDetection called:', {
      type: event.type,
      isFeatureEnabled: state.isFeatureEnabled,
      ocrEnabled: state.preferences?.ocr_enabled,
      isActive: state.isActive,
      reporterName: event.parsedData.reporterName,
      staffName: event.parsedData.staffName,
    });

    if (!state.isFeatureEnabled || !state.preferences?.ocr_enabled) {
      console.log('[useActiveSit] OCR detection ignored: feature disabled');
      return;
    }

    if (event.type === 'claim' && !state.isActive) {
      console.log('[useActiveSit] 🎯 Claim detected - starting new sit');
      
      // Play sound notification
      playSitOpenedSound();
      
      // Auto-start sit when claim detected
      const sitData: Partial<SitData> = {
        reporter_name: event.parsedData.reporterName || '',
        reported_player: event.parsedData.targetName || '',  // Use detected target name
        report_type: normalizeReportType(event.parsedData.reportType),  // Normalize OCR report type to valid backend choice
        report_reason: event.parsedData.reason || '',  // Use detected reason
        detection_method: event.detectionMethod,
        // Note: has_recording is NOT sent to the backend - it's a read-only field set by the server
      };

      if (state.preferences.confirm_before_start) {
        console.log('[useActiveSit] Showing confirmation modal');
        // Show confirmation before starting
        setState(prev => ({ ...prev, showPostSitModal: true }));
      } else {
        console.log('[useActiveSit] Auto-starting sit without confirmation');
        await startSit(sitData);
      }
    } else if (event.type === 'close' && state.isActive) {
      console.log('[useActiveSit] 🎯 Close detected - ending sit');
      
      // Play sound notification
      playSitClosedSound();
      
      // Auto-close sit when close detected
      await endSit();
    } else if (event.type === 'rating' && state.sit) {
      console.log('[useActiveSit] 🎯 Rating detected - updating sit');
      // Update sit with rating
      await updateSit({
        player_rating_credits: event.parsedData.credits,
        player_rating: event.parsedData.stars,
      });
    } else {
      console.log('[useActiveSit] OCR detection ignored:', {
        type: event.type,
        isActive: state.isActive,
        hasSit: !!state.sit,
      });
    }
  }, [state.isActive, state.isFeatureEnabled, state.preferences, state.sit]);

  // Update the OCR detection callback ref whenever handleOCRDetection changes
  useEffect(() => {
    console.log('[useActiveSit] Updating OCR detection callback ref');
    ocrDetectionCallbackRef.current = handleOCRDetection;
  }, [handleOCRDetection]);

  // Start a new sit
  const startSit = useCallback(async (sitData?: Partial<SitData>) => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      const response = await sitAPI.create({
        reporter_name: sitData?.reporter_name || '',
        reported_player: sitData?.reported_player || '',
        report_type: sitData?.report_type || '',
        report_reason: sitData?.report_reason || '',
        started_at: new Date().toISOString(),
        detection_method: sitData?.detection_method || 'manual',
      });

      const newSit = response.data;
      sitIdRef.current = newSit.id;

      setState(prev => ({
        ...prev,
        sit: newSit,
        isActive: true,
        isLoading: false,
        duration: 0,
      }));

      startDurationTimer(Date.now());

      // Auto-start recording if enabled AND not already recording
      // (When sit is detected via OCR, recording is already running from the OCR monitoring)
      if (state.preferences?.recording_enabled && state.preferences?.auto_start_recording) {
        if (!recording.isRecording) {
          console.log('[useActiveSit] Starting new recording');
          await recording.startRecording();
        } else {
          console.log('[useActiveSit] Recording already active, not starting a new one');
        }
        
        // Start OCR if enabled AND not already scanning
        if (state.preferences?.ocr_enabled && !ocr.isScanning) {
          console.log('[useActiveSit] Starting OCR scanning');
          ocr.startScanning();
        } else if (ocr.isScanning) {
          console.log('[useActiveSit] OCR already scanning, not starting again');
        }
      }

      return newSit;
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to start sit',
      }));
      return null;
    }
  }, [state.preferences, recording, ocr, startDurationTimer]);

  // Update current sit
  const updateSit = useCallback(async (updates: Partial<SitData>) => {
    if (!state.sit?.id) return;

    try {
      const response = await sitAPI.update(state.sit.id, updates);
      setState(prev => ({
        ...prev,
        sit: { ...prev.sit!, ...response.data },
      }));
    } catch (err) {
      console.error('Failed to update sit:', err);
    }
  }, [state.sit?.id]);

  // End current sit
  const endSit = useCallback(async (outcome?: string, outcomeNotes?: string) => {
    if (!state.sit?.id) return;

    try {
      setState(prev => ({ ...prev, isLoading: true }));

      // Stop recording first
      if (recording.isRecording) {
        recording.stopRecording();
      }

      // Stop OCR scanning
      if (ocr.isScanning) {
        ocr.stopScanning();
      }

      // Clear duration timer
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }

      // Update sit with end time and outcome
      await sitAPI.update(state.sit.id, {
        ended_at: new Date().toISOString(),
        duration_seconds: state.duration,
        outcome: outcome || 'no_action',
        outcome_notes: outcomeNotes || '',
      });

      // Show post-sit modal
      setState(prev => ({
        ...prev,
        showPostSitModal: true,
        isLoading: false,
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to end sit',
      }));
    }
  }, [state.sit?.id, state.duration, recording, ocr]);

  // Cancel current sit (discard without saving)
  const cancelSit = useCallback(async () => {
    if (!state.sit?.id) return;

    try {
      // Stop recording
      if (recording.isRecording) {
        recording.stopRecording();
      }
      recording.discardRecording();

      // Stop OCR
      if (ocr.isScanning) {
        ocr.stopScanning();
      }

      // Clear duration timer
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }

      // Delete the sit
      await sitAPI.delete(state.sit.id);

      sitIdRef.current = null;
      setState(prev => ({
        ...prev,
        sit: null,
        isActive: false,
        duration: 0,
        showPostSitModal: false,
      }));
    } catch (err) {
      setState(prev => ({
        ...prev,
        error: 'Failed to cancel sit',
      }));
    }
  }, [state.sit?.id, recording, ocr]);

  // Complete and close modal
  const completeSit = useCallback(() => {
    sitIdRef.current = null;
    setState(prev => ({
      ...prev,
      sit: null,
      isActive: false,
      duration: 0,
      showPostSitModal: false,
    }));

    // Discard recording preview
    recording.discardRecording();
    ocr.clearDetections();
  }, [recording, ocr]);

  // Update preferences
  const updatePreferences = useCallback(async (updates: Partial<SitPreferences>) => {
    try {
      const response = await sitAPI.updatePreferences(updates);
      setState(prev => ({
        ...prev,
        preferences: response.data,
      }));
    } catch (err) {
      console.error('Failed to update preferences:', err);
    }
  }, []);

  // Load settings on mount
  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, []);

  // Force reset sit state (for debugging stuck sits)
  const forceReset = useCallback(() => {
    console.log('[useActiveSit] 🔄 Force resetting sit state');
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }
    sitIdRef.current = null;
    setState({
      isActive: false,
      sit: null,
      duration: 0,
      isLoading: false,
      error: null,
      preferences: state.preferences,
      isFeatureEnabled: state.isFeatureEnabled,
      showPostSitModal: false,
    });
  }, [state.preferences, state.isFeatureEnabled]);

  return {
    ...state,
    recording,
    ocr,
    loadSettings,
    startSit,
    updateSit,
    endSit,
    cancelSit,
    completeSit,
    updatePreferences,
    forceReset,
    closePostSitModal: () => setState(prev => ({ ...prev, showPostSitModal: false })),
  };
}

export default useActiveSit;
