'use client';

import { useState, useEffect } from 'react';
import { counterAPI } from '@/lib/api';
import { useWebSocket } from '@/contexts/WebSocketContext';
import {
  TrophyIcon,
  ArrowTrendingUpIcon,
  CalendarIcon,
  FireIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  display_name: string;
  role: string;
  role_color: string;
  sit_count: number;
  ticket_count: number;
  total_count: number;
}

export default function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly' | 'all'>('weekly');
  const [type, setType] = useState<'all' | 'sit' | 'ticket'>('all');
  const { onLeaderboardUpdate, isConnected } = useWebSocket();

  useEffect(() => {
    fetchLeaderboard();
  }, [period, type]);

  useEffect(() => {
    const unsubscribe = onLeaderboardUpdate((data) => {
      // Real-time leaderboard updates
      fetchLeaderboard();
    });
    return unsubscribe;
  }, [onLeaderboardUpdate]);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const res = await counterAPI.leaderboard(period, type);
      setLeaderboard(res.data.results || res.data);
    } catch (error) {
      toast.error('Failed to load leaderboard');
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <TrophyIcon className="w-7 h-7 text-yellow-400" />
            Leaderboard
          </h1>
          <p className="text-gray-400 mt-1">
            Top performers across all staff members
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-400">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex gap-2">
            <button
              onClick={() => setPeriod('daily')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === 'daily'
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              Today
            </button>
            <button
              onClick={() => setPeriod('weekly')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === 'weekly'
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              This Week
            </button>
            <button
              onClick={() => setPeriod('monthly')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === 'monthly'
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              This Month
            </button>
            <button
              onClick={() => setPeriod('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                period === 'all'
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              All Time
            </button>
          </div>

          <div className="flex gap-2 md:ml-auto">
            <button
              onClick={() => setType('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                type === 'all'
                  ? 'bg-purple-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setType('sit')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                type === 'sit'
                  ? 'bg-blue-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              Sits
            </button>
            <button
              onClick={() => setType('ticket')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                type === 'ticket'
                  ? 'bg-green-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              }`}
            >
              Tickets
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
              {leaderboard[1]?.display_name || leaderboard[1]?.username}
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
              {type === 'all'
                ? leaderboard[1]?.total_count
                : type === 'sit'
                ? leaderboard[1]?.sit_count
                : leaderboard[1]?.ticket_count}
            </p>
            <p className="text-gray-500 text-sm">
              {type === 'all' ? 'Total' : type === 'sit' ? 'Sits' : 'Tickets'}
            </p>
          </div>

          {/* First Place */}
          <div className="bg-dark-card rounded-lg border-2 border-yellow-500/50 p-6 text-center transform -translate-y-4 shadow-lg shadow-yellow-500/20">
            <FireIcon className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
            <div className="text-5xl mb-2">🥇</div>
            <p className="text-white font-bold text-lg">
              {leaderboard[0]?.display_name || leaderboard[0]?.username}
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
              {type === 'all'
                ? leaderboard[0]?.total_count
                : type === 'sit'
                ? leaderboard[0]?.sit_count
                : leaderboard[0]?.ticket_count}
            </p>
            <p className="text-gray-400 text-sm">
              {type === 'all' ? 'Total' : type === 'sit' ? 'Sits' : 'Tickets'}
            </p>
          </div>

          {/* Third Place */}
          <div className="bg-dark-card rounded-lg border border-orange-500/30 p-6 pt-12 text-center">
            <div className="text-4xl mb-2">🥉</div>
            <p className="text-white font-semibold">
              {leaderboard[2]?.display_name || leaderboard[2]?.username}
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
              {type === 'all'
                ? leaderboard[2]?.total_count
                : type === 'sit'
                ? leaderboard[2]?.sit_count
                : leaderboard[2]?.ticket_count}
            </p>
            <p className="text-gray-500 text-sm">
              {type === 'all' ? 'Total' : type === 'sit' ? 'Sits' : 'Tickets'}
            </p>
          </div>
        </div>
      )}

      {/* Full Leaderboard */}
      <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
        <div className="p-4 border-b border-dark-border">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <ArrowTrendingUpIcon className="w-5 h-5 text-primary-400" />
            Full Rankings
          </h2>
        </div>
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
          </div>
        ) : leaderboard.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No data for this period
          </div>
        ) : (
          <div className="divide-y divide-dark-border">
            {leaderboard.map((entry, index) => (
              <div
                key={entry.user_id}
                className={`flex items-center p-4 ${getRankBgClass(
                  entry.rank
                )} hover:bg-dark-bg/50 transition-colors`}
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
                  <p className="text-white font-medium">
                    {entry.display_name || entry.username}
                  </p>
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
                  {(type === 'all' || type === 'sit') && (
                    <div>
                      <p className="text-lg font-bold text-blue-400">
                        {entry.sit_count}
                      </p>
                      <p className="text-xs text-gray-500">Sits</p>
                    </div>
                  )}
                  {(type === 'all' || type === 'ticket') && (
                    <div>
                      <p className="text-lg font-bold text-green-400">
                        {entry.ticket_count}
                      </p>
                      <p className="text-xs text-gray-500">Tickets</p>
                    </div>
                  )}
                  {type === 'all' && (
                    <div>
                      <p className="text-lg font-bold text-purple-400">
                        {entry.total_count}
                      </p>
                      <p className="text-xs text-gray-500">Total</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
