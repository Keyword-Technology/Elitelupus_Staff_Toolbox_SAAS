'use client';

import { useState, useEffect, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import {
  XMarkIcon,
  CheckIcon,
  VideoCameraIcon,
  ClockIcon,
  UserIcon,
  ExclamationTriangleIcon,
  StarIcon,
  DocumentTextIcon,
} from '@heroicons/react/24/solid';
import { sitAPI } from '@/lib/api';
import { SitData } from '@/hooks/useActiveSit';
import toast from 'react-hot-toast';

interface PostSitModalProps {
  isOpen: boolean;
  onClose: () => void;
  sit: SitData | null;
  recordingBlob?: Blob | null;
  recordingPreviewUrl?: string | null;
  recordingDuration?: number;
  onComplete: () => void;
}

const OUTCOME_OPTIONS = [
  { value: 'no_action', label: 'No Action Taken', color: 'gray' },
  { value: 'false_report', label: 'False Report', color: 'yellow' },
  { value: 'verbal_warning', label: 'Verbal Warning', color: 'blue' },
  { value: 'formal_warning', label: 'Formal Warning', color: 'orange' },
  { value: 'kick', label: 'Kick', color: 'red' },
  { value: 'ban', label: 'Ban', color: 'red' },
  { value: 'escalated', label: 'Escalated to Higher Staff', color: 'purple' },
  { value: 'other', label: 'Other', color: 'gray' },
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

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
}

export function PostSitModal({
  isOpen,
  onClose,
  sit,
  recordingBlob,
  recordingPreviewUrl,
  recordingDuration,
  onComplete,
}: PostSitModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    outcome: sit?.outcome || 'no_action',
    outcome_notes: sit?.outcome_notes || '',
    ban_duration: sit?.ban_duration || '',
    reported_player: sit?.reported_player || '',
    report_type: sit?.report_type || '',
    report_reason: sit?.report_reason || '',
  });
  const [note, setNote] = useState('');
  const [steamId, setSteamId] = useState('');

  // Reset form when sit changes
  useEffect(() => {
    if (sit) {
      setFormData({
        outcome: sit.outcome || 'no_action',
        outcome_notes: sit.outcome_notes || '',
        ban_duration: sit.ban_duration || '',
        reported_player: sit.reported_player || '',
        report_type: sit.report_type || '',
        report_reason: sit.report_reason || '',
      });
    }
  }, [sit]);

  const handleSubmit = async () => {
    if (!sit?.id) return;

    setIsSubmitting(true);
    try {
      // Update sit with final details
      await sitAPI.update(sit.id, {
        ...formData,
        ended_at: sit.ended_at || new Date().toISOString(),
      });

      // Add note if provided
      if (note.trim()) {
        await sitAPI.createNote(sit.id, {
          note_type: 'general',
          content: note,
        });
      }

      // Add Steam ID note if provided
      if (steamId.trim()) {
        await sitAPI.createNote(sit.id, {
          note_type: 'steam_id',
          content: `Steam ID: ${steamId}`,
          steam_id: steamId,
        });
      }

      toast.success('Sit saved successfully');
      onComplete();
    } catch (err) {
      toast.error('Failed to save sit');
      console.error('Failed to save sit:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDiscard = async () => {
    if (!sit?.id) return;

    setIsSubmitting(true);
    try {
      await sitAPI.delete(sit.id);
      toast.success('Sit discarded');
      onComplete();
    } catch (err) {
      toast.error('Failed to discard sit');
      console.error('Failed to discard sit:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!sit) return null;

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/70" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-xl 
                bg-dark-card border border-dark-border shadow-xl transition-all">
                {/* Header */}
                <div className="px-6 py-4 border-b border-dark-border flex items-center justify-between">
                  <Dialog.Title className="text-lg font-semibold text-white flex items-center gap-2">
                    <DocumentTextIcon className="w-5 h-5 text-primary-500" />
                    Complete Sit Report
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-dark-hover rounded-lg transition-colors"
                  >
                    <XMarkIcon className="w-5 h-5 text-gray-400" />
                  </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
                  {/* Sit Summary */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-dark-hover rounded-lg p-3">
                      <div className="text-xs text-gray-500 mb-1">Duration</div>
                      <div className="text-white font-semibold flex items-center gap-1">
                        <ClockIcon className="w-4 h-4 text-primary-500" />
                        {formatDuration(sit.duration_seconds || 0)}
                      </div>
                    </div>
                    <div className="bg-dark-hover rounded-lg p-3">
                      <div className="text-xs text-gray-500 mb-1">Reporter</div>
                      <div className="text-white font-semibold flex items-center gap-1">
                        <UserIcon className="w-4 h-4 text-blue-500" />
                        {sit.reporter_name || 'Unknown'}
                      </div>
                    </div>
                    <div className="bg-dark-hover rounded-lg p-3">
                      <div className="text-xs text-gray-500 mb-1">Detection</div>
                      <div className="text-white font-semibold text-sm">
                        {sit.detection_method === 'manual' ? 'Manual' : 
                         sit.detection_method === 'ocr_chat' ? 'OCR Chat' : 'OCR Popup'}
                      </div>
                    </div>
                    <div className="bg-dark-hover rounded-lg p-3">
                      <div className="text-xs text-gray-500 mb-1">Recording</div>
                      <div className="text-white font-semibold flex items-center gap-1">
                        <VideoCameraIcon className={`w-4 h-4 ${sit.has_recording ? 'text-green-500' : 'text-gray-500'}`} />
                        {sit.has_recording ? formatDuration(recordingDuration || 0) : 'None'}
                      </div>
                    </div>
                  </div>

                  {/* Recording Preview */}
                  {recordingPreviewUrl && (
                    <div className="border border-dark-border rounded-lg overflow-hidden">
                      <div className="px-3 py-2 bg-dark-hover border-b border-dark-border">
                        <span className="text-sm text-gray-400">Recording Preview</span>
                      </div>
                      <video
                        src={recordingPreviewUrl}
                        controls
                        className="w-full max-h-64 object-contain bg-black"
                      />
                    </div>
                  )}

                  {/* Player Rating (if detected) */}
                  {sit.player_rating !== undefined && sit.player_rating !== null && (
                    <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <StarIcon className="w-5 h-5 text-yellow-500" />
                        <span className="font-semibold text-yellow-400">Player Rating Received</span>
                      </div>
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
                        <span className="text-gray-400">
                          ({sit.player_rating_credits || 0} credits)
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Reported Player */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Reported Player
                    </label>
                    <input
                      type="text"
                      value={formData.reported_player}
                      onChange={(e) => setFormData({ ...formData, reported_player: e.target.value })}
                      placeholder="Enter player name"
                      className="w-full px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                        text-white focus:outline-none focus:border-primary-500"
                    />
                  </div>

                  {/* Report Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Report Type
                    </label>
                    <select
                      value={formData.report_type}
                      onChange={(e) => setFormData({ ...formData, report_type: e.target.value })}
                      className="w-full px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                        text-white focus:outline-none focus:border-primary-500"
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

                  {/* Outcome */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Outcome
                    </label>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {OUTCOME_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => setFormData({ ...formData, outcome: option.value })}
                          className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors
                            ${formData.outcome === option.value
                              ? 'bg-primary-600 text-white border-2 border-primary-400'
                              : 'bg-dark-hover text-gray-300 border border-dark-border hover:border-gray-600'
                            }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Ban Duration (conditional) */}
                  {formData.outcome === 'ban' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Ban Duration
                      </label>
                      <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
                        {BAN_DURATION_OPTIONS.map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => setFormData({ ...formData, ban_duration: option.value })}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors
                              ${formData.ban_duration === option.value
                                ? 'bg-red-600 text-white border-2 border-red-400'
                                : 'bg-dark-hover text-gray-300 border border-dark-border hover:border-gray-600'
                              }`}
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Outcome Notes */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Outcome Notes
                    </label>
                    <textarea
                      value={formData.outcome_notes}
                      onChange={(e) => setFormData({ ...formData, outcome_notes: e.target.value })}
                      placeholder="Add notes about the outcome..."
                      rows={3}
                      className="w-full px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                        text-white focus:outline-none focus:border-primary-500 resize-none"
                    />
                  </div>

                  {/* Additional Note */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Additional Note (Optional)
                    </label>
                    <textarea
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      placeholder="Add any additional notes..."
                      rows={2}
                      className="w-full px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                        text-white focus:outline-none focus:border-primary-500 resize-none"
                    />
                  </div>

                  {/* Steam ID */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Steam ID (Optional)
                    </label>
                    <input
                      type="text"
                      value={steamId}
                      onChange={(e) => setSteamId(e.target.value)}
                      placeholder="STEAM_0:1:12345678"
                      className="w-full px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                        text-white focus:outline-none focus:border-primary-500"
                    />
                  </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-dark-border flex justify-between">
                  <button
                    onClick={handleDiscard}
                    disabled={isSubmitting}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg 
                      font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                  >
                    <ExclamationTriangleIcon className="w-4 h-4" />
                    Discard Sit
                  </button>
                  <div className="flex gap-3">
                    <button
                      onClick={onClose}
                      disabled={isSubmitting}
                      className="px-4 py-2 bg-dark-hover hover:bg-dark-border text-gray-300 
                        rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSubmit}
                      disabled={isSubmitting}
                      className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg 
                        font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                      <CheckIcon className="w-4 h-4" />
                      Save Sit
                    </button>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

export default PostSitModal;
