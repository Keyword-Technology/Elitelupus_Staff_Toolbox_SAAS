'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  PlusIcon, 
  MinusIcon,
  ArrowsPointingOutIcon,
  XMarkIcon,
} from '@heroicons/react/24/solid';

interface Region {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface OCRRegionAdjusterProps {
  stream: MediaStream | null;
  onRegionsChange: (regions: { chat: Region; popup: Region }) => void;
  onClose: () => void;
}

const STEP = 0.05; // 5% step for adjustments
const MIN_SIZE = 0.1; // Minimum 10% size

export function OCRRegionAdjuster({ stream, onRegionsChange, onClose }: OCRRegionAdjusterProps) {
  // Load regions from localStorage or use defaults
  const [regions, setRegions] = useState<{ chat: Region; popup: Region }>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('ocrRegions');
      if (saved) {
        try {
          return JSON.parse(saved);
        } catch (e) {
          console.error('Failed to parse saved regions:', e);
        }
      }
    }
    return {
      chat: { x: 0, y: 0.7, width: 0.35, height: 0.25 },
      popup: { x: 0, y: 0.1, width: 0.3, height: 0.4 },
    };
  });

  const [activeRegion, setActiveRegion] = useState<'chat' | 'popup'>('chat');
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Connect video to stream
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
      videoRef.current.play().catch(console.error);
    }
  }, [stream]);

  // Draw region overlays
  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const drawOverlay = () => {
      const ctx = canvas.getContext('2d');
      if (!ctx || video.videoWidth === 0 || video.videoHeight === 0) {
        requestAnimationFrame(drawOverlay);
        return;
      }

      // Match canvas size to video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw video frame
      ctx.drawImage(video, 0, 0);

      // Draw semi-transparent overlay
      ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Helper function to draw region
      const drawRegion = (region: Region, color: string, label: string, isActive: boolean) => {
        const x = region.x * canvas.width;
        const y = region.y * canvas.height;
        const w = region.width * canvas.width;
        const h = region.height * canvas.height;

        // Clear region (show video)
        ctx.clearRect(x, y, w, h);
        ctx.drawImage(video, x, y, w, h, x, y, w, h);

        // Draw border
        ctx.strokeStyle = color;
        ctx.lineWidth = isActive ? 4 : 2;
        ctx.setLineDash(isActive ? [10, 5] : []);
        ctx.strokeRect(x, y, w, h);

        // Draw label
        ctx.fillStyle = color;
        ctx.fillRect(x, y - 30, 150, 30);
        ctx.fillStyle = 'white';
        ctx.font = 'bold 14px sans-serif';
        ctx.fillText(label, x + 10, y - 10);

        // Draw dimensions
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(x, y + h + 5, 200, 25);
        ctx.fillStyle = 'white';
        ctx.font = '12px monospace';
        ctx.fillText(
          `${(region.width * 100).toFixed(0)}% × ${(region.height * 100).toFixed(0)}%`,
          x + 5,
          y + h + 20
        );
      };

      // Draw both regions
      drawRegion(regions.chat, '#22c55e', 'Chat Region', activeRegion === 'chat');
      drawRegion(regions.popup, '#3b82f6', 'Popup Region', activeRegion === 'popup');

      requestAnimationFrame(drawOverlay);
    };

    const rafId = requestAnimationFrame(drawOverlay);
    return () => cancelAnimationFrame(rafId);
  }, [regions, activeRegion]);

  // Save regions and notify parent
  const updateRegions = (newRegions: typeof regions) => {
    setRegions(newRegions);
    localStorage.setItem('ocrRegions', JSON.stringify(newRegions));
    onRegionsChange(newRegions);
  };

  // Adjust functions
  const adjustRegion = (dimension: 'x' | 'y' | 'width' | 'height', delta: number) => {
    const region = activeRegion;
    const updated = { ...regions };
    let newValue = updated[region][dimension] + delta;

    // Clamp values
    if (dimension === 'width' || dimension === 'height') {
      newValue = Math.max(MIN_SIZE, Math.min(1, newValue));
    } else {
      newValue = Math.max(0, Math.min(1 - updated[region].width, newValue));
    }

    updated[region][dimension] = newValue;
    updateRegions(updated);
  };

  const resetRegions = () => {
    const defaults = {
      chat: { x: 0, y: 0.7, width: 0.35, height: 0.25 },
      popup: { x: 0, y: 0.1, width: 0.3, height: 0.4 },
    };
    updateRegions(defaults);
  };

  const region = regions[activeRegion];

  return (
    <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
      <div className="bg-dark-card rounded-lg border border-dark-border w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-dark-border flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ArrowsPointingOutIcon className="w-6 h-6 text-primary-400" />
            <div>
              <h2 className="text-xl font-bold text-white">Adjust OCR Scan Regions</h2>
              <p className="text-sm text-gray-400">Fine-tune which areas of your screen are scanned</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
          >
            <XMarkIcon className="w-6 h-6 text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 flex gap-4">
          {/* Video Preview */}
          <div className="flex-1 relative bg-black rounded-lg overflow-hidden">
            <video
              ref={videoRef}
              className="absolute inset-0 w-full h-full object-contain opacity-0"
              muted
              playsInline
            />
            <canvas
              ref={canvasRef}
              className="w-full h-full object-contain"
            />
            {!stream && (
              <div className="absolute inset-0 flex items-center justify-center">
                <p className="text-gray-400">No video stream available</p>
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="w-80 space-y-4">
            {/* Region Selector */}
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-300">Select Region</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setActiveRegion('chat')}
                  className={`flex-1 py-2 px-3 rounded-lg transition-colors ${
                    activeRegion === 'chat'
                      ? 'bg-green-600 text-white'
                      : 'bg-dark-hover text-gray-400 hover:bg-dark-hover/70'
                  }`}
                >
                  Chat
                </button>
                <button
                  onClick={() => setActiveRegion('popup')}
                  className={`flex-1 py-2 px-3 rounded-lg transition-colors ${
                    activeRegion === 'popup'
                      ? 'bg-blue-600 text-white'
                      : 'bg-dark-hover text-gray-400 hover:bg-dark-hover/70'
                  }`}
                >
                  Popup
                </button>
              </div>
            </div>

            {/* Position Controls */}
            <div className="space-y-3 p-4 bg-dark-hover rounded-lg">
              <h3 className="text-sm font-semibold text-gray-300">Position</h3>
              
              {/* X Position */}
              <div className="space-y-1">
                <label className="text-xs text-gray-400">X (Horizontal)</label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => adjustRegion('x', -STEP)}
                    className="p-2 bg-dark-card hover:bg-dark-card/70 rounded"
                  >
                    <MinusIcon className="w-4 h-4 text-gray-300" />
                  </button>
                  <div className="flex-1 text-center">
                    <span className="text-sm font-mono text-white">
                      {(region.x * 100).toFixed(0)}%
                    </span>
                  </div>
                  <button
                    onClick={() => adjustRegion('x', STEP)}
                    className="p-2 bg-dark-card hover:bg-dark-card/70 rounded"
                  >
                    <PlusIcon className="w-4 h-4 text-gray-300" />
                  </button>
                </div>
              </div>

              {/* Y Position */}
              <div className="space-y-1">
                <label className="text-xs text-gray-400">Y (Vertical)</label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => adjustRegion('y', -STEP)}
                    className="p-2 bg-dark-card hover:bg-dark-card/70 rounded"
                  >
                    <MinusIcon className="w-4 h-4 text-gray-300" />
                  </button>
                  <div className="flex-1 text-center">
                    <span className="text-sm font-mono text-white">
                      {(region.y * 100).toFixed(0)}%
                    </span>
                  </div>
                  <button
                    onClick={() => adjustRegion('y', STEP)}
                    className="p-2 bg-dark-card hover:bg-dark-card/70 rounded"
                  >
                    <PlusIcon className="w-4 h-4 text-gray-300" />
                  </button>
                </div>
              </div>
            </div>

            {/* Size Controls */}
            <div className="space-y-3 p-4 bg-dark-hover rounded-lg">
              <h3 className="text-sm font-semibold text-gray-300">Size</h3>
              
              {/* Width */}
              <div className="space-y-1">
                <label className="text-xs text-gray-400">Width</label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => adjustRegion('width', -STEP)}
                    className="p-2 bg-dark-card hover:bg-dark-card/70 rounded"
                  >
                    <MinusIcon className="w-4 h-4 text-gray-300" />
                  </button>
                  <div className="flex-1 text-center">
                    <span className="text-sm font-mono text-white">
                      {(region.width * 100).toFixed(0)}%
                    </span>
                  </div>
                  <button
                    onClick={() => adjustRegion('width', STEP)}
                    className="p-2 bg-dark-card hover:bg-dark-card/70 rounded"
                  >
                    <PlusIcon className="w-4 h-4 text-gray-300" />
                  </button>
                </div>
              </div>

              {/* Height */}
              <div className="space-y-1">
                <label className="text-xs text-gray-400">Height</label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => adjustRegion('height', -STEP)}
                    className="p-2 bg-dark-card hover:bg-dark-card/70 rounded"
                  >
                    <MinusIcon className="w-4 h-4 text-gray-300" />
                  </button>
                  <div className="flex-1 text-center">
                    <span className="text-sm font-mono text-white">
                      {(region.height * 100).toFixed(0)}%
                    </span>
                  </div>
                  <button
                    onClick={() => adjustRegion('height', STEP)}
                    className="p-2 bg-dark-card hover:bg-dark-card/70 rounded"
                  >
                    <PlusIcon className="w-4 h-4 text-gray-300" />
                  </button>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2">
              <button
                onClick={resetRegions}
                className="w-full py-2 px-4 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
              >
                Reset to Defaults
              </button>
              <button
                onClick={onClose}
                className="w-full py-2 px-4 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                Save & Close
              </button>
            </div>

            {/* Info */}
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <p className="text-xs text-blue-400">
                <strong>Tip:</strong> The colored rectangles show what will be scanned. 
                Adjust the regions to cover your game's chat area and sit notification cards.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
