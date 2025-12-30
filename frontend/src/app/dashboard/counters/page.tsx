'use client';

import { useState, useEffect } from 'react';
import { CounterCard } from '@/components/counters/CounterCard';
import { counterAPI } from '@/lib/api';
import { useWebSocket } from '@/contexts/WebSocketContext';
import {
  ChartBarIcon,
  ClockIcon,
  CalendarIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface CounterStats {
  sits: {
    total: number;
    today: number;
    week: number;
    month: number;
  };
  tickets: {
    total: number;
    today: number;
    week: number;
    month: number;
  };
}

interface HistoryEntry {
  id: number;
  counter_type: string;
  action: string;
  value: number;
  note: string;
  created_at: string;
}

export default function CountersPage() {
  const [stats, setStats] = useState<CounterStats | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const { isConnected } = useWebSocket();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, historyRes] = await Promise.all([
        counterAPI.stats(),
        counterAPI.history(),
      ]);
      setStats(statsRes.data);
      setHistory(historyRes.data.results || historyRes.data);
    } catch (error) {
      toast.error('Failed to load counter data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Sit & Ticket Counters</h1>
          <p className="text-gray-400 mt-1">
            Track your sits and tickets in real-time
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

      {/* Counter Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CounterCard
          title="Sits"
          count={stats?.sits.total || 0}
          todayCount={stats?.sits.today || 0}
          type="sit"
        />
        <CounterCard
          title="Tickets"
          count={stats?.tickets.total || 0}
          todayCount={stats?.tickets.today || 0}
          type="ticket"
        />
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Today's Sits"
          value={stats?.sits.today || 0}
          icon={ClockIcon}
          color="blue"
        />
        <StatCard
          title="This Week's Sits"
          value={stats?.sits.week || 0}
          icon={CalendarIcon}
          color="green"
        />
        <StatCard
          title="Today's Tickets"
          value={stats?.tickets.today || 0}
          icon={ClockIcon}
          color="purple"
        />
        <StatCard
          title="This Week's Tickets"
          value={stats?.tickets.week || 0}
          icon={CalendarIcon}
          color="orange"
        />
      </div>

      {/* Monthly Overview */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <ChartBarIcon className="w-5 h-5 text-primary-400" />
          Monthly Overview
        </h2>
        <div className="grid grid-cols-2 gap-8">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Monthly Sits</span>
              <span className="text-2xl font-bold text-white">
                {stats?.sits.month || 0}
              </span>
            </div>
            <div className="h-2 bg-dark-bg rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all duration-500"
                style={{
                  width: `${Math.min(100, ((stats?.sits.month || 0) / 100) * 100)}%`,
                }}
              />
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Monthly Tickets</span>
              <span className="text-2xl font-bold text-white">
                {stats?.tickets.month || 0}
              </span>
            </div>
            <div className="h-2 bg-dark-bg rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all duration-500"
                style={{
                  width: `${Math.min(100, ((stats?.tickets.month || 0) / 100) * 100)}%`,
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <ArrowTrendingUpIcon className="w-5 h-5 text-primary-400" />
          Recent Activity
        </h2>
        <div className="space-y-3">
          {history.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No recent activity</p>
          ) : (
            history.slice(0, 10).map((entry) => (
              <div
                key={entry.id}
                className="flex items-center justify-between py-2 border-b border-dark-border last:border-0"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      entry.counter_type === 'sit' ? 'bg-blue-500' : 'bg-purple-500'
                    }`}
                  />
                  <span className="text-white capitalize">
                    {entry.counter_type}
                  </span>
                  <span
                    className={`text-sm ${
                      entry.action === 'increment'
                        ? 'text-green-400'
                        : 'text-red-400'
                    }`}
                  >
                    {entry.action === 'increment' ? '+' : '-'}{entry.value}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(entry.created_at).toLocaleString()}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  color: 'blue' | 'green' | 'purple' | 'orange';
}

function StatCard({ title, value, icon: Icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500/20 text-blue-400',
    green: 'bg-green-500/20 text-green-400',
    purple: 'bg-purple-500/20 text-purple-400',
    orange: 'bg-orange-500/20 text-orange-400',
  };

  return (
    <div className="bg-dark-card rounded-lg border border-dark-border p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}
