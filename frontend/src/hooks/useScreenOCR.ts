'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { createWorker, Worker } from 'tesseract.js';

// OCR Detection patterns for Elitelupus servers
export const OCR_PATTERNS = {
  // Chat message patterns
  CLAIM_PATTERN: /\[Elite Reports\]\s*(\w+)\s+claimed\s+(.+?)['']s\s+report/i,
  CLOSE_PATTERN: /\[Elite Reports\]\s*You have closed\s+(.+?)['']s\s+report/i,
  RATING_PATTERN: /\[Elite Admin Stats\]\s*Your performance has earned you\s*(\d+)\s*credits/i,
  
  // Popup detection patterns
  POPUP_CLAIM_BUTTON: /CLAIM\s*REPORT/i,
  POPUP_CLOSE_BUTTON: /CLOSE\s*REPORT/i,
  POPUP_REPORTER: /Reporter:\s*(.+)/i,
  POPUP_TARGET: /Accused:\s*(.+)/i,
  POPUP_REASON: /Reason:\s*(.+)/i,
};

export interface OCRDetectionEvent {
  type: 'claim' | 'close' | 'rating';
  timestamp: Date;
  detectionMethod: 'ocr_chat' | 'ocr_popup';
  rawText: string;
  parsedData: {
    staffName?: string;
    reporterName?: string;
    targetName?: string;
    reason?: string;
    credits?: number;
    stars?: number;
  };
}

export interface OCRState {
  isScanning: boolean;
  isInitialized: boolean;
  lastScanTime: Date | null;
  lastDetectedText: string;
  scanCount: number;
  error: string | null;
  detectionEvents: OCRDetectionEvent[];
}

export interface OCROptions {
  scanIntervalMs?: number;
  enableChatRegion?: boolean;
  enablePopupRegion?: boolean;
  onDetection?: (event: OCRDetectionEvent) => void;
  onError?: (error: string) => void;
}

// Default OCR region definitions (percentages of screen)
export const DEFAULT_REGIONS = {
  chat: {
    // Lower-left chat area (typical GMod chat position)
    x: 0,
    y: 0.7,
    width: 0.4,
    height: 0.25,
  },
  popup: {
    // Center of screen where report popup appears
    x: 0.3,
    y: 0.3,
    width: 0.4,
    height: 0.4,
  },
};

// Convert credits to stars (Elitelupus rating system)
function creditsToStars(credits: number): number {
  if (credits >= 25) return 5;
  if (credits >= 20) return 4;
  if (credits >= 15) return 3;
  if (credits >= 10) return 2;
  if (credits >= 5) return 1;
  return 0;
}

export function useScreenOCR(stream: MediaStream | null, options: OCROptions = {}) {
  const {
    scanIntervalMs = 1500,
    enableChatRegion = true,
    enablePopupRegion = true,
    onDetection,
    onError,
  } = options;

  const [state, setState] = useState<OCRState>({
    isScanning: false,
    isInitialized: false,
    lastScanTime: null,
    lastDetectedText: '',
    scanCount: 0,
    error: null,
    detectionEvents: [],
  });

  const workerRef = useRef<Worker | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const scanIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isActiveRef = useRef(false);

  // Initialize Tesseract worker
  const initializeWorker = useCallback(async () => {
    try {
      const worker = await createWorker('eng', 1, {
        // Optimize for game text
        logger: () => {}, // Silence logs
      });

      // Set whitelist for faster recognition (common characters in game chat)
      await worker.setParameters({
        tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789[]:\' .-_',
      });

      workerRef.current = worker;
      setState(prev => ({ ...prev, isInitialized: true, error: null }));
      return true;
    } catch (err) {
      const error = 'Failed to initialize OCR engine';
      setState(prev => ({ ...prev, error }));
      if (onError) onError(error);
      return false;
    }
  }, [onError]);

  // Cleanup worker on unmount
  useEffect(() => {
    return () => {
      isActiveRef.current = false;
      if (scanIntervalRef.current) {
        clearInterval(scanIntervalRef.current);
      }
      if (workerRef.current) {
        workerRef.current.terminate();
      }
    };
  }, []);

  // Create canvas and video elements for frame capture
  useEffect(() => {
    if (typeof document !== 'undefined') {
      canvasRef.current = document.createElement('canvas');
      videoRef.current = document.createElement('video');
      videoRef.current.autoplay = true;
      videoRef.current.muted = true;
    }
  }, []);

  // Connect video element to stream when it changes
  useEffect(() => {
    if (videoRef.current && stream) {
      console.log('[OCR] 🎥 Connecting stream to video element...');
      videoRef.current.srcObject = stream;
      
      // Wait for video to be ready
      const video = videoRef.current;
      const onLoadedMetadata = () => {
        console.log('[OCR] ✅ Video metadata loaded:', {
          videoWidth: video.videoWidth,
          videoHeight: video.videoHeight,
          readyState: video.readyState
        });
      };
      
      const onCanPlay = () => {
        console.log('[OCR] ✅ Video can play - ready for capture');
      };
      
      video.addEventListener('loadedmetadata', onLoadedMetadata);
      video.addEventListener('canplay', onCanPlay);
      
      // Force play
      video.play().catch(err => {
        console.error('[OCR] ❌ Failed to play video:', err);
      });
      
      return () => {
        video.removeEventListener('loadedmetadata', onLoadedMetadata);
        video.removeEventListener('canplay', onCanPlay);
      };
    }
  }, [stream]);

  // Capture a region from the video frame
  const captureRegion = useCallback((
    region: { x: number; y: number; width: number; height: number }
  ): ImageData | null => {
    if (!canvasRef.current || !videoRef.current || !stream) {
      console.warn('[OCR] ⚠️ Cannot capture - missing elements:', {
        hasCanvas: !!canvasRef.current,
        hasVideo: !!videoRef.current,
        hasStream: !!stream
      });
      return null;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) {
      console.warn('[OCR] ⚠️ Cannot get canvas context');
      return null;
    }

    // Get video dimensions
    const videoWidth = video.videoWidth;
    const videoHeight = video.videoHeight;
    if (videoWidth === 0 || videoHeight === 0) {
      console.warn('[OCR] ⚠️ Video not ready:', {
        videoWidth,
        videoHeight,
        readyState: video.readyState,
        srcObject: !!video.srcObject
      });
      return null;
    }

    // Calculate pixel coordinates from percentages
    const pixelX = Math.round(region.x * videoWidth);
    const pixelY = Math.round(region.y * videoHeight);
    const pixelWidth = Math.round(region.width * videoWidth);
    const pixelHeight = Math.round(region.height * videoHeight);

    // Set canvas size to region size
    canvas.width = pixelWidth;
    canvas.height = pixelHeight;

    // Draw the region from the video
    ctx.drawImage(
      video,
      pixelX, pixelY, pixelWidth, pixelHeight,
      0, 0, pixelWidth, pixelHeight
    );

    // Apply image preprocessing for better OCR
    const imageData = ctx.getImageData(0, 0, pixelWidth, pixelHeight);
    
    // Simple grayscale conversion and contrast boost
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      // Convert to grayscale
      const gray = data[i] * 0.299 + data[i + 1] * 0.587 + data[i + 2] * 0.114;
      // Boost contrast
      const enhanced = Math.min(255, Math.max(0, (gray - 128) * 1.5 + 128));
      data[i] = enhanced;
      data[i + 1] = enhanced;
      data[i + 2] = enhanced;
    }
    ctx.putImageData(imageData, 0, 0);

    return imageData;
  }, [stream]);

  // Perform OCR on a region and parse results
  const scanRegion = useCallback(async (
    region: { x: number; y: number; width: number; height: number },
    regionType: 'chat' | 'popup'
  ): Promise<OCRDetectionEvent | null> => {
    if (!workerRef.current || !canvasRef.current) return null;

    try {
      // Capture the region
      captureRegion(region);
      
      // Perform OCR
      const result = await workerRef.current.recognize(canvasRef.current);
      const text = result.data.text;

      setState(prev => ({
        ...prev,
        lastDetectedText: text,
        lastScanTime: new Date(),
        scanCount: prev.scanCount + 1,
      }));

      // Debug logging
      console.log(`[OCR ${regionType}] Scan #${state.scanCount + 1}:`, {
        textLength: text.length,
        preview: text.substring(0, 100),
        fullText: text
      });

      // Parse the text for detection events
      let event: OCRDetectionEvent | null = null;

      // Check for claim event (chat message)
      const claimMatch = text.match(OCR_PATTERNS.CLAIM_PATTERN);
      if (claimMatch) {
        event = {
          type: 'claim',
          timestamp: new Date(),
          detectionMethod: regionType === 'chat' ? 'ocr_chat' : 'ocr_popup',
          rawText: text,
          parsedData: {
            staffName: claimMatch[1],
            reporterName: claimMatch[2],
          },
        };
      }

      // Check for claim button in popup (alternative detection)
      if (!event && regionType === 'popup') {
        const claimButtonMatch = text.match(OCR_PATTERNS.POPUP_CLAIM_BUTTON);
        if (claimButtonMatch) {
          // Also try to extract reporter/target info from popup
          const reporterMatch = text.match(OCR_PATTERNS.POPUP_REPORTER);
          const targetMatch = text.match(OCR_PATTERNS.POPUP_TARGET);
          const reasonMatch = text.match(OCR_PATTERNS.POPUP_REASON);
          
          event = {
            type: 'claim',
            timestamp: new Date(),
            detectionMethod: 'ocr_popup',
            rawText: text,
            parsedData: {
              reporterName: reporterMatch?.[1]?.trim(),
              targetName: targetMatch?.[1]?.trim(),
              reason: reasonMatch?.[1]?.trim(),
            },
          };
        }
      }

      // Check for close event (chat message)
      const closeMatch = text.match(OCR_PATTERNS.CLOSE_PATTERN);
      if (closeMatch) {
        event = {
          type: 'close',
          timestamp: new Date(),
          detectionMethod: regionType === 'chat' ? 'ocr_chat' : 'ocr_popup',
          rawText: text,
          parsedData: {
            reporterName: closeMatch[1],
          },
        };
      }

      // Check for close button in popup (alternative detection)
      if (!event && regionType === 'popup') {
        const closeButtonMatch = text.match(OCR_PATTERNS.POPUP_CLOSE_BUTTON);
        if (closeButtonMatch) {
          event = {
            type: 'close',
            timestamp: new Date(),
            detectionMethod: 'ocr_popup',
            rawText: text,
            parsedData: {},
          };
        }
      }

      // Check for rating event
      const ratingMatch = text.match(OCR_PATTERNS.RATING_PATTERN);
      if (ratingMatch) {
        const credits = parseInt(ratingMatch[1], 10);
        event = {
          type: 'rating',
          timestamp: new Date(),
          detectionMethod: regionType === 'chat' ? 'ocr_chat' : 'ocr_popup',
          rawText: text,
          parsedData: {
            credits,
            stars: creditsToStars(credits),
          },
        };
      }

      return event;
    } catch (err) {
      console.error('OCR scan error:', err);
      return null;
    }
  }, [captureRegion]);

  // Main scan loop
  const performScan = useCallback(async () => {
    if (!isActiveRef.current || !workerRef.current) {
      console.log('[OCR] Scan skipped - not active or no worker');
      return;
    }

    console.log('[OCR] 🔍 Starting scan cycle...');
    const events: OCRDetectionEvent[] = [];

    // Scan chat region
    if (enableChatRegion) {
      const chatEvent = await scanRegion(DEFAULT_REGIONS.chat, 'chat');
      if (chatEvent) events.push(chatEvent);
    }

    // Scan popup region
    if (enablePopupRegion) {
      const popupEvent = await scanRegion(DEFAULT_REGIONS.popup, 'popup');
      if (popupEvent) events.push(popupEvent);
    }

    // Process detected events
    if (events.length > 0) {
      console.log(`[OCR] ✅ Found ${events.length} detection event(s)`);
    }
    
    for (const event of events) {
      setState(prev => ({
        ...prev,
        detectionEvents: [...prev.detectionEvents.slice(-99), event], // Keep last 100 events
      }));

      if (onDetection) {
        onDetection(event);
      }
    }
    
    console.log('[OCR] 🏁 Scan cycle complete');
  }, [enableChatRegion, enablePopupRegion, scanRegion, onDetection]);

  // Start scanning
  const startScanning = useCallback(async (providedStream?: MediaStream) => {
    // Use provided stream or fall back to the one from props
    const streamToUse = providedStream || stream;
    
    console.log('[OCR] 🚀 Starting OCR scanning...', { 
      hasStream: !!streamToUse, 
      streamActive: streamToUse?.active,
      providedStream: !!providedStream,
      propsStream: !!stream
    });
    
    if (!streamToUse) {
      const error = 'No screen stream available for OCR';
      console.error('[OCR] ❌', error);
      setState(prev => ({ ...prev, error }));
      if (onError) onError(error);
      return;
    }

    // Update the stream ref if a new one was provided
    if (providedStream && videoRef.current) {
      console.log('[OCR] 🎥 Updating video element with provided stream...');
      videoRef.current.srcObject = providedStream;
      // Force play
      videoRef.current.play().catch(err => {
        console.error('[OCR] ❌ Failed to play video:', err);
      });
    }

    // Initialize worker if needed
    if (!workerRef.current) {
      console.log('[OCR] Initializing Tesseract worker...');
      const success = await initializeWorker();
      if (!success) {
        console.error('[OCR] ❌ Worker initialization failed');
        return;
      }
      console.log('[OCR] ✅ Worker initialized');
    }

    // Wait for video to be ready before starting scans
    const video = videoRef.current;
    if (video) {
      if (video.readyState < 2) {
        console.log('[OCR] ⏳ Waiting for video to be ready (readyState: ' + video.readyState + ')...');
        await new Promise<void>((resolve) => {
          const checkReady = () => {
            if (video.readyState >= 2) {
              console.log('[OCR] ✅ Video ready:', {
                videoWidth: video.videoWidth,
                videoHeight: video.videoHeight,
                readyState: video.readyState
              });
              resolve();
            } else {
              console.log('[OCR] ⏳ Video readyState:', video.readyState, '- waiting...');
              setTimeout(checkReady, 100);
            }
          };
          checkReady();
        });
      } else {
        console.log('[OCR] ✅ Video already ready:', {
          videoWidth: video.videoWidth,
          videoHeight: video.videoHeight,
          readyState: video.readyState
        });
      }
    } else {
      console.warn('[OCR] ⚠️ No video element available!');
    }

    isActiveRef.current = true;
    setState(prev => ({ ...prev, isScanning: true, error: null }));

    console.log(`[OCR] ✅ Scanning started - interval: ${scanIntervalMs}ms`);

    // Start scan interval
    scanIntervalRef.current = setInterval(performScan, scanIntervalMs);
    
    // Perform initial scan immediately
    performScan();
  }, [stream, initializeWorker, performScan, scanIntervalMs, onError]);

  // Stop scanning
  const stopScanning = useCallback(() => {
    isActiveRef.current = false;
    
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }

    setState(prev => ({ ...prev, isScanning: false }));
  }, []);

  // Clear detection history
  const clearDetections = useCallback(() => {
    setState(prev => ({
      ...prev,
      detectionEvents: [],
      lastDetectedText: '',
    }));
  }, []);

  return {
    ...state,
    startScanning,
    stopScanning,
    clearDetections,
  };
}

export default useScreenOCR;
