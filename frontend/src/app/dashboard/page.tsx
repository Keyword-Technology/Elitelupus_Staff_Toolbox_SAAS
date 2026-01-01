'use client';

import { useAuth } from '@/contexts/AuthContext';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { counterAPI, serverAPI } from '@/lib/api';
import { CounterCard } from '@/components/counters/CounterCard';
import { ServerStatusCard } from '@/components/servers/ServerStatusCard';
import { useEffect, useState } from 'react';
import { useWebSocket } from '@/contexts/WebSocketContext';

export default function DashboardPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { onCounterUpdate, onServerUpdate, connectionStatus } = useWebSocket();
  const [servers, setServers] = useState<any[]>([]);

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

  // Initial server fetch
  useEffect(() => {
    serverAPI.status().then((res) => {
      setServers(res.data);
    }).catch(() => {
      // Fallback silently
    });
  }, []);

  // Handle real-time server updates
  useEffect(() => {
    const unsubscribe = onServerUpdate((data) => {
      if (data.type === 'status_update' && data.data) {
        setServers(data.data);
      } else if (data.type === 'initial_data' && data.data) {
        setServers(data.data);
      } else if (data.type === 'server_update') {
        setServers((prev) =>
          prev.map((s) =>
            s.id === data.server_id ? { ...s, ...data.status } : s
          )
        );
      }
    });
    return unsubscribe;
  }, [onServerUpdate]);

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
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Server Status</h2>
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-dark-bg text-xs">
            <span className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-400' :
              connectionStatus === 'reconnecting' ? 'bg-yellow-400 animate-pulse' :
              'bg-red-400'
            }`} />
            <span className={
              connectionStatus === 'connected' ? 'text-green-400' :
              connectionStatus === 'reconnecting' ? 'text-yellow-400' :
              'text-red-400'
            }>
              {connectionStatus === 'connected' ? 'Live Updates' :
               connectionStatus === 'reconnecting' ? 'Reconnecting...' :
               'Offline'}
            </span>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {servers.map((server: any) => (
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
