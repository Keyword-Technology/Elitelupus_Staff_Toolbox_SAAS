'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { createWorker, Worker } from 'tesseract.js';

// OCR Detection patterns for Elitelupus servers
export const OCR_PATTERNS = {
  // Chat message patterns - more flexible to handle OCR errors
  // Made more lenient: allows for missing characters, flexible spacing, possessive variations
  CLAIM_PATTERN: /\[Elite\s*Reports?\]\s*(\w+)\s+claim(?:ed)?\s+(.+?)['']?s?\s+rep(?:o[rt]?|or|ort)/i,
  CLOSE_PATTERN: /You\s+have\s+clos(?:ed)?\s+(.+?)['']?s?\s+rep(?:o[rt]?|or|ort)/i,
  RATING_PATTERN: /\[Elite Admin Stats\]\s*Your performance has earned you\s*(\d+)\s*credits/i,
  
  // Popup detection patterns - matches actual game UI
  // The game shows: "PlayerName's Report" with "Claim" and "Close" buttons
  POPUP_REPORT_HEADER: /(.+?)['']?s?\s*Report/i,  // Matches "HeGe Jimbbo's Report", "GA Gambler's Report"
  POPUP_CLAIM_BUTTON: /\bClaim\b/i,  // Just "Claim" button
  POPUP_CLOSE_BUTTON: /\bClose\b/i,  // Just "Close" button
  POPUP_GO_TO_BUTTON: /\bGo\s*To\b/i,  // "Go To" button
  POPUP_BRING_BUTTON: /\bBring\b/i,  // "Bring" button
  POPUP_REPORT_TYPE: /Report\s*Type:\s*(.+)/i,
  POPUP_REPORTED_PLAYER: /Reported\s*Player:\s*(.+)/i,
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
    reportType?: string;  // Report type from popup (RDM, NLR, FailRP, etc.)
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

export interface OCRRegion {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface OCROptions {
  scanIntervalMs?: number;
  enableChatRegion?: boolean;
  enablePopupRegion?: boolean;
  customRegions?: { chat: OCRRegion; popup: OCRRegion };
  onDetection?: (event: OCRDetectionEvent) => void;
  onError?: (error: string) => void;
}

// Default OCR region definitions (percentages of screen)
// Optimized to scan only left side of screen for performance
export const DEFAULT_REGIONS = {
  chat: {
    // Lower-left chat area (typical GMod chat position)
    x: 0,
    y: 0.7,
    width: 0.35,  // Reduced from 0.4 to focus on left side only
    height: 0.25,
  },
  popup: {
    // Left side popup area (sit cards, counter widgets, report notifications)
    x: 0,
    y: 0.1,
    width: 0.3,  // Reduced from 0.4, focused on left side
    height: 0.4, // Covers upper-left to mid-left for sit cards
  },
};

// Load custom regions from localStorage if available
function loadSavedRegions(): { chat: OCRRegion; popup: OCRRegion } | null {
  if (typeof window === 'undefined') return null;
  try {
    const saved = localStorage.getItem('ocrRegions');
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

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
    scanIntervalMs = 1500,  // Faster interval to catch more events (was 2000ms)
    enableChatRegion = true,
    enablePopupRegion = false,  // Disabled by default for better performance
    customRegions,
    onDetection,
    onError,
  } = options;

  // Use custom regions or saved regions or defaults
  const regions = customRegions || loadSavedRegions() || DEFAULT_REGIONS;

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
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const activeStream = video?.srcObject as MediaStream | null;
    
    if (!canvas || !video || !activeStream) {
      console.warn('[OCR] ⚠️ Cannot capture - missing elements:', {
        hasCanvas: !!canvas,
        hasVideo: !!video,
        hasStream: !!activeStream,
        videoSrcObject: !!video?.srcObject
      });
      return null;
    }

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

    // Lightweight grayscale conversion for performance
    // Skip contrast enhancement to reduce CPU usage
    const imageData = ctx.getImageData(0, 0, pixelWidth, pixelHeight);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      // Simple grayscale (slightly faster than weighted average)
      const gray = (data[i] + data[i + 1] + data[i + 2]) / 3;
      data[i] = data[i + 1] = data[i + 2] = gray;
    }
    ctx.putImageData(imageData, 0, 0);

    return imageData;
  }, []); // Removed stream dependency - now uses video.srcObject directly

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

      // Reduced logging for performance - only log if text detected
      if (text.trim().length > 0) {
        console.log(`[OCR ${regionType}] Scan #${state.scanCount + 1}:`, {
          textLength: text.length,
          preview: text.substring(0, 100)
        });
        
        // Debug: Check if keywords are present but pattern didn't match
        const hasEliteReports = /Elite Reports/i.test(text);
        const hasClaimed = /claimed/i.test(text);
        const hasClosed = /closed/i.test(text);
        const hasReport = /repo[rt]/i.test(text);
        
        if ((hasEliteReports && hasClaimed && hasReport) || (hasClosed && hasReport)) {
          console.log('[OCR] ⚠️ Keywords detected but pattern may not match:', {
            hasEliteReports,
            hasClaimed,
            hasClosed,
            hasReport,
            textSample: text.substring(0, 200)
          });
        }
      }

      // Parse the text for detection events
      let event: OCRDetectionEvent | null = null;

      // Check for claim event (chat message)
      const claimMatch = text.match(OCR_PATTERNS.CLAIM_PATTERN);
      if (claimMatch) {
        console.log('[OCR] 🎯 CLAIM DETECTED:', {
          staffName: claimMatch[1],
          reporterName: claimMatch[2],
          fullMatch: claimMatch[0],
          textLength: text.length
        });
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
      } else {
        // Enhanced debug: Show why the pattern didn't match if keywords are present
        if (text.includes('Elite') && text.includes('claim') && text.includes('rep')) {
          console.log('[OCR] ⚠️ Claim keywords found but pattern did NOT match. Text sample:', {
            sample: text.substring(0, 300),
            hasEliteReports: /Elite\s*Reports?/i.test(text),
            hasClaim: /claim(?:ed)?/i.test(text),
            hasReport: /rep(?:o[rt]?|or|ort)/i.test(text),
            testPattern: OCR_PATTERNS.CLAIM_PATTERN.toString(),
          });
        }
      }

      // Check for CLAIMED report popup (has Go To/Bring buttons)
      // When a report is claimed, the popup changes from "Claim" button to "Go To" + "Bring" buttons
      // This is an alternative detection method to the chat message
      if (!event && regionType === 'popup') {
        const hasGoToButton = OCR_PATTERNS.POPUP_GO_TO_BUTTON.test(text);
        const hasBringButton = OCR_PATTERNS.POPUP_BRING_BUTTON.test(text);
        const hasClaimButton = OCR_PATTERNS.POPUP_CLAIM_BUTTON.test(text);
        const hasCloseButton = OCR_PATTERNS.POPUP_CLOSE_BUTTON.test(text);
        const reportHeaderMatch = text.match(OCR_PATTERNS.POPUP_REPORT_HEADER);
        const reportTypeMatch = text.match(OCR_PATTERNS.POPUP_REPORT_TYPE);
        const reportedPlayerMatch = text.match(OCR_PATTERNS.POPUP_REPORTED_PLAYER);
        
        // Debug logging if we detect any report structure
        if (reportHeaderMatch) {
          console.log('[OCR] 📋 Report popup detected - checking buttons:', {
            reporterName: reportHeaderMatch?.[1]?.trim(),
            hasGoToButton,
            hasBringButton,
            hasClaimButton,
            hasCloseButton,
            fullText: text,
            textLength: text.length,
          });
        }
        
        // Detect CLAIMED report: has Go To or Bring buttons + report structure
        const isClaimedReport = (hasGoToButton || hasBringButton) && reportHeaderMatch;
        
        if (isClaimedReport) {
          const reporterName = reportHeaderMatch?.[1]?.trim();
          console.log('[OCR] 🎯 CLAIMED REPORT DETECTED in popup (sit starting):', {
            reporterName,
            reportType: reportTypeMatch?.[1]?.trim(),
            reportedPlayer: reportedPlayerMatch?.[1]?.trim(),
            hasGoToButton,
            hasBringButton,
            textPreview: text.substring(0, 200)
          });
          
          // Extract additional info from popup
          const reasonMatch = text.match(OCR_PATTERNS.POPUP_REASON);
          
          event = {
            type: 'claim',
            timestamp: new Date(),
            detectionMethod: 'ocr_popup',
            rawText: text,
            parsedData: {
              reporterName: reporterName,
              reportType: reportTypeMatch?.[1]?.trim(),
              targetName: reportedPlayerMatch?.[1]?.trim(),
              reason: reasonMatch?.[1]?.trim(),
            },
          };
        }
      }

      // Check for close event (ONLY from chat message, not popup)
      // The "Close" button on a popup just closes the window, not the sit
      // Only "You have closed X's report" in chat means the sit is done
      if (regionType === 'chat') {
        const closeMatch = text.match(OCR_PATTERNS.CLOSE_PATTERN);
        if (closeMatch) {
          console.log('[OCR] 🎯 CLOSE DETECTED in chat:', {
            reporterName: closeMatch[1],
            fullMatch: closeMatch[0]
          });
          event = {
            type: 'close',
            timestamp: new Date(),
            detectionMethod: 'ocr_chat',
            rawText: text,
            parsedData: {
              reporterName: closeMatch[1],
            },
          };
        }
      }

      // Check for rating event
      const ratingMatch = text.match(OCR_PATTERNS.RATING_PATTERN);
      if (ratingMatch) {
        const credits = parseInt(ratingMatch[1], 10);
        console.log('[OCR] 🎯 RATING DETECTED:', {
          credits,
          stars: creditsToStars(credits)
        });
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
  }, [captureRegion, regions]); // Added regions dependency

  // Main scan loop
  const performScan = useCallback(async () => {
    if (!isActiveRef.current || !workerRef.current) {
      return;
    }

    const events: OCRDetectionEvent[] = [];

    // Scan chat region (primary - always enabled)
    if (enableChatRegion) {
      const chatEvent = await scanRegion(regions.chat, 'chat');
      if (chatEvent) events.push(chatEvent);
    }

    // Scan popup region (optional - for sit cards/counters)
    if (enablePopupRegion) {
      const popupEvent = await scanRegion(regions.popup, 'popup');
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
