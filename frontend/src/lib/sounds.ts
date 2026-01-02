/**
 * Sound notification utilities for sit detection events
 */

// Audio context for generating tones
let audioContext: AudioContext | null = null;

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  return audioContext;
}

/**
 * Play a notification sound using Web Audio API
 * @param frequency - Tone frequency in Hz
 * @param duration - Duration in milliseconds
 * @param volume - Volume (0-1)
 */
function playTone(frequency: number, duration: number, volume: number = 0.3): void {
  try {
    const ctx = getAudioContext();
    const oscillator = ctx.createOscillator();
    const gainNode = ctx.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(ctx.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(volume, ctx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration / 1000);

    oscillator.start(ctx.currentTime);
    oscillator.stop(ctx.currentTime + duration / 1000);
  } catch (err) {
    console.warn('[Sound] Failed to play tone:', err);
  }
}

/**
 * Play a pleasant "sit opened" notification sound
 * Two-tone ascending sequence
 */
export function playSitOpenedSound(): void {
  console.log('[Sound] 🔔 Playing sit opened sound');
  
  // First tone (C5 - 523 Hz)
  playTone(523, 150, 0.3);
  
  // Second tone (E5 - 659 Hz) slightly delayed
  setTimeout(() => {
    playTone(659, 150, 0.3);
  }, 120);
  
  // Third tone (G5 - 784 Hz) for a pleasant chord
  setTimeout(() => {
    playTone(784, 200, 0.25);
  }, 240);
}

/**
 * Play a gentle "sit closed" notification sound
 * Two-tone descending sequence
 */
export function playSitClosedSound(): void {
  console.log('[Sound] 🔕 Playing sit closed sound');
  
  // First tone (G5 - 784 Hz)
  playTone(784, 150, 0.25);
  
  // Second tone (E5 - 659 Hz) slightly delayed
  setTimeout(() => {
    playTone(659, 150, 0.25);
  }, 120);
  
  // Third tone (C5 - 523 Hz) for completion
  setTimeout(() => {
    playTone(523, 200, 0.2);
  }, 240);
}

/**
 * Play a test sound to check volume/functionality
 */
export function playTestSound(): void {
  console.log('[Sound] 🔊 Playing test sound');
  playTone(440, 200, 0.3); // A4 note
}

/**
 * Initialize audio context on user interaction (required by browsers)
 * Call this on first user click/interaction
 */
export function initializeAudioContext(): void {
  try {
    const ctx = getAudioContext();
    if (ctx.state === 'suspended') {
      ctx.resume();
    }
  } catch (err) {
    console.warn('[Sound] Failed to initialize audio context:', err);
  }
}
