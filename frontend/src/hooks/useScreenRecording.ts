'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

export interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  isSupported: boolean;
  hasPermission: boolean;
  duration: number;
  recordedBlob: Blob | null;
  previewUrl: string | null;
  error: string | null;
}

export interface RecordingOptions {
  videoQuality?: 'low' | 'medium' | 'high';
  maxDurationMinutes?: number;
  onChunkReady?: (chunk: Blob, chunkNumber: number) => void;
  onStop?: (blob: Blob, duration: number) => void;
  onError?: (error: string) => void;
}

const VIDEO_BITRATES: Record<string, number> = {
  low: 1_000_000,     // 1 Mbps
  medium: 2_500_000,  // 2.5 Mbps
  high: 5_000_000,    // 5 Mbps
};

export function useScreenRecording(options: RecordingOptions = {}) {
  const {
    videoQuality = 'medium',
    maxDurationMinutes = 30,
    onChunkReady,
    onStop,
    onError,
  } = options;

  const [state, setState] = useState<RecordingState>({
    isRecording: false,
    isPaused: false,
    isSupported: false,
    hasPermission: false,
    duration: 0,
    recordedBlob: null,
    previewUrl: null,
    error: null,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const chunkNumberRef = useRef(0);
  const startTimeRef = useRef<number>(0);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Check if screen recording is supported
  useEffect(() => {
    const isSupported = 
      typeof navigator !== 'undefined' &&
      'mediaDevices' in navigator &&
      'getDisplayMedia' in navigator.mediaDevices;
    
    setState(prev => ({ ...prev, isSupported }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (state.previewUrl) {
        URL.revokeObjectURL(state.previewUrl);
      }
    };
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, error: null }));

      // Request screen capture
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          displaySurface: 'window',
          frameRate: { ideal: 30, max: 60 },
        },
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });

      streamRef.current = stream;

      // Handle user stopping the share via browser UI
      stream.getVideoTracks()[0].addEventListener('ended', () => {
        stopRecording();
      });

      // Determine MIME type support
      const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp9')
        ? 'video/webm;codecs=vp9'
        : MediaRecorder.isTypeSupported('video/webm;codecs=vp8')
        ? 'video/webm;codecs=vp8'
        : 'video/webm';

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        videoBitsPerSecond: VIDEO_BITRATES[videoQuality],
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      chunkNumberRef.current = 0;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
          chunkNumberRef.current++;
          
          if (onChunkReady) {
            onChunkReady(event.data, chunkNumberRef.current);
          }
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const duration = Math.round((Date.now() - startTimeRef.current) / 1000);
        const previewUrl = URL.createObjectURL(blob);

        setState(prev => ({
          ...prev,
          isRecording: false,
          isPaused: false,
          recordedBlob: blob,
          previewUrl,
          duration,
        }));

        if (onStop) {
          onStop(blob, duration);
        }

        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }

        // Clear duration interval
        if (durationIntervalRef.current) {
          clearInterval(durationIntervalRef.current);
          durationIntervalRef.current = null;
        }
      };

      mediaRecorder.onerror = (event: Event) => {
        const error = 'Recording error occurred';
        setState(prev => ({ ...prev, error }));
        if (onError) onError(error);
      };

      // Start recording with 10 second chunks for progressive upload
      mediaRecorder.start(10000);
      startTimeRef.current = Date.now();

      // Update duration every second
      durationIntervalRef.current = setInterval(() => {
        const currentDuration = Math.round((Date.now() - startTimeRef.current) / 1000);
        setState(prev => ({ ...prev, duration: currentDuration }));

        // Auto-stop if max duration reached
        if (currentDuration >= maxDurationMinutes * 60) {
          stopRecording();
        }
      }, 1000);

      setState(prev => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        hasPermission: true,
        recordedBlob: null,
        previewUrl: null,
        duration: 0,
      }));
    } catch (err) {
      let errorMessage = 'Failed to start recording';
      
      if (err instanceof DOMException) {
        if (err.name === 'NotAllowedError') {
          errorMessage = 'Screen capture permission denied';
        } else if (err.name === 'NotFoundError') {
          errorMessage = 'No screen to capture found';
        } else if (err.name === 'NotReadableError') {
          errorMessage = 'Screen capture not available';
        }
      }

      setState(prev => ({ ...prev, error: errorMessage }));
      if (onError) onError(errorMessage);
    }
  }, [videoQuality, maxDurationMinutes, onChunkReady, onStop, onError]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.pause();
      setState(prev => ({ ...prev, isPaused: true }));
    }
  }, []);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
      mediaRecorderRef.current.resume();
      setState(prev => ({ ...prev, isPaused: false }));
    }
  }, []);

  const discardRecording = useCallback(() => {
    if (state.previewUrl) {
      URL.revokeObjectURL(state.previewUrl);
    }
    
    chunksRef.current = [];
    chunkNumberRef.current = 0;
    
    setState(prev => ({
      ...prev,
      recordedBlob: null,
      previewUrl: null,
      duration: 0,
    }));
  }, [state.previewUrl]);

  const getStream = useCallback(() => streamRef.current, []);

  return {
    ...state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    discardRecording,
    getStream,
  };
}

export default useScreenRecording;
