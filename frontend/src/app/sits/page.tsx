'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { sitAPI } from '@/lib/api';
import {
  ClockIcon,
  VideoCameraIcon,
  UserIcon,
  CalendarIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  EyeIcon,
  PlayCircleIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/solid';
import { ActiveSitPanel } from '@/components/counters/ActiveSitPanel';
import { PostSitModal } from '@/components/counters/PostSitModal';

interface Sit {
  id: string;
  reporter_name: string;
  reported_player: string;
  report_type: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  outcome: string;
  detection_method: string;
  has_recording: boolean;
  player_rating: number | null;
  player_rating_credits: number | null;
}

interface SitStats {
  total_sits: number;
  total_duration_seconds: number;
  average_duration_seconds: number;
  sits_with_recordings: number;
  outcome_breakdown: Record<string, number>;
  detection_method_breakdown: Record<string, number>;
}

const OUTCOME_COLORS: Record<string, string> = {
  no_action: 'bg-gray-500',
  false_report: 'bg-yellow-500',
  verbal_warning: 'bg-blue-500',
  formal_warning: 'bg-orange-500',
  kick: 'bg-red-500',
  ban: 'bg-red-700',
  escalated: 'bg-purple-500',
  other: 'bg-gray-500',
};

const OUTCOME_LABELS: Record<string, string> = {
  no_action: 'No Action',
  false_report: 'False Report',
  verbal_warning: 'Verbal Warning',
  formal_warning: 'Formal Warning',
  kick: 'Kick',
  ban: 'Ban',
  escalated: 'Escalated',
  other: 'Other',
};

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function SitsPage() {
  const router = useRouter();
  const [sits, setSits] = useState<Sit[]>([]);
  const [stats, setStats] = useState<SitStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterOutcome, setFilterOutcome] = useState('');
  const [selectedSit, setSelectedSit] = useState<Sit | null>(null);
  const [showVideoModal, setShowVideoModal] = useState(false);

  // Load sits
  const loadSits = async () => {
    setIsLoading(true);
    try {
      const response = await sitAPI.list({
        page,
        status: filterOutcome || undefined,
      });
      setSits(response.data.results || response.data);
      setTotalPages(Math.ceil((response.data.count || response.data.length) / 10));
      setError(null);
    } catch (err) {
      setError('Failed to load sits');
      console.error('Failed to load sits:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Load stats
  const loadStats = async () => {
    try {
      const response = await sitAPI.getStats({ period: 'weekly' });
      setStats(response.data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  useEffect(() => {
    loadSits();
    loadStats();
  }, [page, filterOutcome]);

  // Filter sits by search query
  const filteredSits = sits.filter((sit) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      sit.reporter_name.toLowerCase().includes(query) ||
      sit.reported_player.toLowerCase().includes(query) ||
      sit.report_type.toLowerCase().includes(query)
    );
  });

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Header */}
      <div className="bg-dark-card border-b border-dark-border">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-white">Sit History</h1>
          <p className="text-gray-400 mt-1">View and manage your sit recordings</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Active Sit Panel */}
        <div className="mb-6">
          <ActiveSitPanel />
        </div>

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-dark-card rounded-lg p-4 border border-dark-border">
              <div className="text-sm text-gray-500">Total Sits (Week)</div>
              <div className="text-2xl font-bold text-white">{stats.total_sits}</div>
            </div>
            <div className="bg-dark-card rounded-lg p-4 border border-dark-border">
              <div className="text-sm text-gray-500">Total Time</div>
              <div className="text-2xl font-bold text-white">
                {formatDuration(stats.total_duration_seconds)}
              </div>
            </div>
            <div className="bg-dark-card rounded-lg p-4 border border-dark-border">
              <div className="text-sm text-gray-500">Avg Duration</div>
              <div className="text-2xl font-bold text-white">
                {formatDuration(Math.round(stats.average_duration_seconds))}
              </div>
            </div>
            <div className="bg-dark-card rounded-lg p-4 border border-dark-border">
              <div className="text-sm text-gray-500">With Recordings</div>
              <div className="text-2xl font-bold text-white">{stats.sits_with_recordings}</div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-dark-card rounded-lg border border-dark-border p-4 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
              <input
                type="text"
                placeholder="Search by player name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                  text-white focus:outline-none focus:border-primary-500"
              />
            </div>

            {/* Outcome Filter */}
            <div className="flex items-center gap-2">
              <FunnelIcon className="w-5 h-5 text-gray-500" />
              <select
                value={filterOutcome}
                onChange={(e) => {
                  setFilterOutcome(e.target.value);
                  setPage(1);
                }}
                className="px-4 py-2 bg-dark-hover border border-dark-border rounded-lg 
                  text-white focus:outline-none focus:border-primary-500"
              >
                <option value="">All Outcomes</option>
                {Object.entries(OUTCOME_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-900/30 border border-red-800 rounded-lg p-4 mb-6 text-red-400">
            {error}
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <div className="bg-dark-card rounded-lg border border-dark-border p-8 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto" />
            <p className="text-gray-400 mt-4">Loading sits...</p>
          </div>
        ) : (
          <>
            {/* Sits Table */}
            <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
              <table className="w-full">
                <thead className="bg-dark-hover">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Date</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Reporter</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Reported</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Type</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Duration</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Outcome</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Recording</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-400">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border">
                  {filteredSits.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                        No sits found
                      </td>
                    </tr>
                  ) : (
                    filteredSits.map((sit) => (
                      <tr key={sit.id} className="hover:bg-dark-hover transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <CalendarIcon className="w-4 h-4 text-gray-500" />
                            <span className="text-sm text-white">
                              {formatDate(sit.started_at)}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm text-white">
                            {sit.reporter_name || '-'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm text-white">
                            {sit.reported_player || '-'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm text-gray-400 uppercase">
                            {sit.report_type || '-'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <ClockIcon className="w-4 h-4 text-gray-500" />
                            <span className="text-sm text-white">
                              {sit.duration_seconds ? formatDuration(sit.duration_seconds) : '-'}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium 
                            ${OUTCOME_COLORS[sit.outcome] || 'bg-gray-500'} text-white`}>
                            {OUTCOME_LABELS[sit.outcome] || sit.outcome}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          {sit.has_recording ? (
                            <div className="flex items-center gap-1">
                              <CheckCircleIcon className="w-5 h-5 text-green-500" />
                              <span className="text-xs text-green-400">Yes</span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1">
                              <XCircleIcon className="w-5 h-5 text-gray-500" />
                              <span className="text-xs text-gray-500">No</span>
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setSelectedSit(sit)}
                              className="p-2 hover:bg-dark-border rounded-lg transition-colors"
                              title="View Details"
                            >
                              <EyeIcon className="w-4 h-4 text-gray-400" />
                            </button>
                            {sit.has_recording && (
                              <button
                                onClick={() => {
                                  setSelectedSit(sit);
                                  setShowVideoModal(true);
                                }}
                                className="p-2 hover:bg-dark-border rounded-lg transition-colors"
                                title="Play Recording"
                              >
                                <PlayCircleIcon className="w-4 h-4 text-primary-400" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <div className="text-sm text-gray-400">
                  Page {page} of {totalPages}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="p-2 bg-dark-card border border-dark-border rounded-lg 
                      hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronLeftIcon className="w-5 h-5 text-gray-400" />
                  </button>
                  <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages}
                    className="p-2 bg-dark-card border border-dark-border rounded-lg 
                      hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ChevronRightIcon className="w-5 h-5 text-gray-400" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Video Modal */}
      {showVideoModal && selectedSit && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-dark-card rounded-xl border border-dark-border max-w-4xl w-full">
            <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
              <h3 className="font-semibold text-white">
                Recording - {formatDate(selectedSit.started_at)}
              </h3>
              <button
                onClick={() => setShowVideoModal(false)}
                className="p-2 hover:bg-dark-hover rounded-lg"
              >
                <span className="text-gray-400">✕</span>
              </button>
            </div>
            <div className="p-4">
              {/* TODO: Add video player with recording URL */}
              <div className="aspect-video bg-black rounded-lg flex items-center justify-center">
                <p className="text-gray-500">Recording playback not yet implemented</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
