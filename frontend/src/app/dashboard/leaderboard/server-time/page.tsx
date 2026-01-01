'use client';

import { useState, useEffect } from 'react';
import { staffAPI } from '@/lib/api';
import { useRouter } from 'next/navigation';
import {
  TrophyIcon,
  ClockIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  FireIcon,
  ServerIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface LeaderboardEntry {
  rank: number;
  staff_id: number;
  steam_id: string;
  name: string;
  role: string;
  role_color: string;
  role_priority: number;
  total_seconds: number;
  total_time_formatted: string;
  session_count: number;
  avg_session_seconds: number;
}

interface LeaderboardData {
  period: string;
  period_label: string;
  period_start: string;
  period_end: string;
  offset: number;
  leaderboard: LeaderboardEntry[];
}

export default function ServerTimeLeaderboardPage() {
  const router = useRouter();
  const [data, setData] = useState<LeaderboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'weekly' | 'monthly'>('weekly');
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    fetchLeaderboard();
  }, [period, offset]);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const res = await staffAPI.serverTimeLeaderboard(period, offset);
      setData(res.data);
    } catch (error) {
      toast.error('Failed to load server time leaderboard');
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return '🥇';
      case 2:
        return '🥈';
      case 3:
        return '🥉';
      default:
        return `#${rank}`;
    }
  };

  const getRankBgClass = (rank: number) => {
    switch (rank) {
      case 1:
        return 'bg-yellow-500/10 border-yellow-500/30';
      case 2:
        return 'bg-gray-300/10 border-gray-400/30';
      case 3:
        return 'bg-orange-500/10 border-orange-500/30';
      default:
        return 'bg-dark-card border-dark-border';
    }
  };

  const formatAvgSession = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const leaderboard = data?.leaderboard || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ClockIcon className="w-8 h-8 text-primary-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">Server Time Leaderboard</h1>
            <p className="text-gray-400 text-sm">Top staff members by time spent on servers</p>
          </div>
        </div>
      </div>

      {/* Filters & Navigation */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-4">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          {/* Period Selector */}
          <div className="flex gap-2">
            <button
              onClick={() => { setPeriod('weekly'); setOffset(0); }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === 'weekly'
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              Weekly
            </button>
            <button
              onClick={() => { setPeriod('monthly'); setOffset(0); }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === 'monthly'
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              Monthly
            </button>
          </div>

          {/* Period Navigation */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setOffset(offset + 1)}
              className="p-2 rounded-lg bg-dark-bg hover:bg-dark-border transition-colors"
              title={`Previous ${period === 'weekly' ? 'week' : 'month'}`}
            >
              <ChevronLeftIcon className="w-5 h-5 text-gray-400" />
            </button>
            
            <div className="text-center min-w-[200px]">
              <p className="text-white font-medium">{data?.period_label || 'Loading...'}</p>
              {offset > 0 && (
                <p className="text-xs text-gray-500">
                  {offset} {period === 'weekly' ? 'week' : 'month'}{offset > 1 ? 's' : ''} ago
                </p>
              )}
            </div>
            
            <button
              onClick={() => setOffset(Math.max(0, offset - 1))}
              disabled={offset === 0}
              className={`p-2 rounded-lg transition-colors ${
                offset === 0 
                  ? 'bg-dark-bg text-gray-600 cursor-not-allowed' 
                  : 'bg-dark-bg hover:bg-dark-border text-gray-400'
              }`}
              title={`Next ${period === 'weekly' ? 'week' : 'month'}`}
            >
              <ChevronRightIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Top 3 Podium */}
      {leaderboard.length >= 3 && (
        <div className="grid grid-cols-3 gap-4">
          {/* Second Place */}
          <div className="bg-dark-card rounded-lg border border-gray-400/30 p-6 pt-10 text-center">
            <div className="text-4xl mb-2">🥈</div>
            <p className="text-white font-semibold">
              {leaderboard[1]?.name}
            </p>
            <span
              className="text-xs px-2 py-1 rounded mt-1 inline-block"
              style={{
                backgroundColor: `${leaderboard[1]?.role_color}20`,
                color: leaderboard[1]?.role_color,
              }}
            >
              {leaderboard[1]?.role}
            </span>
            <p className="text-2xl font-bold text-gray-300 mt-3">
              {leaderboard[1]?.total_time_formatted}
            </p>
            <p className="text-gray-500 text-sm">{leaderboard[1]?.session_count} sessions</p>
          </div>

          {/* First Place */}
          <div className="bg-dark-card rounded-lg border-2 border-yellow-500/50 p-6 text-center transform -translate-y-4 shadow-lg shadow-yellow-500/20">
            <FireIcon className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
            <div className="text-5xl mb-2">🥇</div>
            <p className="text-white font-bold text-lg">
              {leaderboard[0]?.name}
            </p>
            <span
              className="text-xs px-2 py-1 rounded mt-1 inline-block"
              style={{
                backgroundColor: `${leaderboard[0]?.role_color}20`,
                color: leaderboard[0]?.role_color,
              }}
            >
              {leaderboard[0]?.role}
            </span>
            <p className="text-3xl font-bold text-yellow-400 mt-3">
              {leaderboard[0]?.total_time_formatted}
            </p>
            <p className="text-gray-400 text-sm">{leaderboard[0]?.session_count} sessions</p>
          </div>

          {/* Third Place */}
          <div className="bg-dark-card rounded-lg border border-orange-500/30 p-6 pt-12 text-center">
            <div className="text-4xl mb-2">🥉</div>
            <p className="text-white font-semibold">
              {leaderboard[2]?.name}
            </p>
            <span
              className="text-xs px-2 py-1 rounded mt-1 inline-block"
              style={{
                backgroundColor: `${leaderboard[2]?.role_color}20`,
                color: leaderboard[2]?.role_color,
              }}
            >
              {leaderboard[2]?.role}
            </span>
            <p className="text-2xl font-bold text-orange-300 mt-3">
              {leaderboard[2]?.total_time_formatted}
            </p>
            <p className="text-gray-500 text-sm">{leaderboard[2]?.session_count} sessions</p>
          </div>
        </div>
      )}

      {/* Full Leaderboard */}
      <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
        <div className="p-4 border-b border-dark-border">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <TrophyIcon className="w-5 h-5 text-primary-400" />
            Full Rankings
          </h2>
        </div>
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
          </div>
        ) : leaderboard.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <ServerIcon className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <p className="text-lg">No server time data for this period</p>
            <p className="text-sm mt-1">Staff server sessions will appear here once tracked</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {leaderboard.map((entry) => (
              <div
                key={entry.staff_id}
                onClick={() => router.push(`/dashboard/staff/${entry.staff_id}`)}
                className={`flex items-center p-4 ${getRankBgClass(entry.rank)} hover:bg-dark-bg/50 transition-colors cursor-pointer`}
              >
                <div className="w-12 text-center">
                  <span
                    className={`text-lg font-bold ${
                      entry.rank <= 3 ? 'text-2xl' : 'text-gray-400'
                    }`}
                  >
                    {getRankIcon(entry.rank)}
                  </span>
                </div>
                <div className="flex-1 ml-4">
                  <p className="text-white font-medium">{entry.name}</p>
                  <span
                    className="text-xs px-2 py-0.5 rounded"
                    style={{
                      backgroundColor: `${entry.role_color}20`,
                      color: entry.role_color,
                    }}
                  >
                    {entry.role}
                  </span>
                </div>
                <div className="flex gap-8 text-right">
                  <div>
                    <p className="text-lg font-bold text-primary-400">{entry.total_time_formatted}</p>
                    <p className="text-xs text-gray-500">Total Time</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-blue-400">{entry.session_count}</p>
                    <p className="text-xs text-gray-500">Sessions</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-green-400">{formatAvgSession(entry.avg_session_seconds)}</p>
                    <p className="text-xs text-gray-500">Avg Session</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
