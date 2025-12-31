'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { counterAPI, serverAPI } from '@/lib/api';
import { CounterCard } from '@/components/counters/CounterCard';
import { ServerStatusCard } from '@/components/servers/ServerStatusCard';
import { useEffect } from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';

export default function DashboardPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { onCounterUpdate } = useWebSocket();

  const { data: counters } = useQuery({
    queryKey: ['counters'],
    queryFn: async () => {
      const response = await counterAPI.get();
      return response.data;
    },
  });

  const { data: stats } = useQuery({
    queryKey: ['counter-stats'],
    queryFn: async () => {
      const response = await counterAPI.stats();
      return response.data;
    },
  });

  const { data: serverStatus } = useQuery({
    queryKey: ['server-status'],
    queryFn: async () => {
      const response = await serverAPI.status();
      return response.data;
    },
    refetchInterval: 60000, // Refresh every minute
  });

  useEffect(() => {
    const unsubscribe = onCounterUpdate(() => {
      // Invalidate counter-related queries to refetch updated stats
      queryClient.invalidateQueries({ queryKey: ['counter-stats'] });
      queryClient.invalidateQueries({ queryKey: ['counters'] });
    });

    return unsubscribe;
  }, [onCounterUpdate, queryClient]);

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-dark-card rounded-lg p-6 border border-dark-border">
        <h1 className="text-2xl font-bold text-white mb-2">
          Welcome back, {user?.display_name || user?.username}!
        </h1>
        <p className="text-gray-400">
          <span
            className="font-medium"
            style={{ color: user?.role_color }}
          >
            {user?.role}
          </span>
          {user?.is_active_staff && ' • Active Staff Member'}
        </p>
      </div>

      {/* Counters Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CounterCard
          title="Sits"
          count={counters?.sits?.count || 0}
          todayCount={stats?.today_sits || 0}
          type="sit"
        />
        <CounterCard
          title="Tickets"
          count={counters?.tickets?.count || 0}
          todayCount={stats?.today_tickets || 0}
          type="ticket"
        />
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="bg-dark-card rounded-lg p-6 border border-dark-border">
          <h2 className="text-lg font-semibold text-white mb-4">Your Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatBox label="Total Sits" value={stats.total_sits} />
            <StatBox label="Total Tickets" value={stats.total_tickets} />
            <StatBox label="Weekly Sits" value={stats.weekly_sits} />
            <StatBox label="Weekly Tickets" value={stats.weekly_tickets} />
          </div>
        </div>
      )}

      {/* Server Status */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Server Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {serverStatus?.map((server: any) => (
            <ServerStatusCard key={server.id} server={server} />
          ))}
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-dark-bg rounded-lg p-4">
      <p className="text-gray-400 text-sm">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}
