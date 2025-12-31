'use client';

import { useState, useEffect } from 'react';
import { ServerStatusCard } from '@/components/servers/ServerStatusCard';
import { serverAPI } from '@/lib/api';
import { useWebSocket } from '@/contexts/WebSocketContext';
import {
  ArrowPathIcon,
  ServerIcon,
  UsersIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface Server {
  id: number;
  name: string;
  ip_address: string;
  port: number;
  server_name: string;
  map_name: string;
  current_players: number;
  max_players: number;
  is_online: boolean;
  staff_online: number;
  staff_list?: Array<{
    name: string;
    rank: string;
    role_color: string;
    steam_id: string;
  }>;
  last_updated: string;
}

interface StaffDistribution {
  server_id: number;
  server_name: string;
  staff: Array<{
    username: string;
    display_name: string;
    role: string;
    role_color: string;
  }>;
}

export default function ServersPage() {
  const [servers, setServers] = useState<Server[]>([]);
  const [distribution, setDistribution] = useState<StaffDistribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { onServerUpdate, isConnected } = useWebSocket();

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    const unsubscribe = onServerUpdate((data) => {
      if (data.type === 'server_update') {
        setServers((prev) =>
          prev.map((s) =>
            s.id === data.server_id ? { ...s, ...data.status } : s
          )
        );
      }
    });

    return unsubscribe;
  }, [onServerUpdate]);

  const fetchData = async () => {
    try {
      const [serversRes, distRes] = await Promise.all([
        serverAPI.status(),
        serverAPI.distribution(),
      ]);
      setServers(serversRes.data);
      setDistribution(distRes.data);
    } catch (error) {
      toast.error('Failed to load server data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await serverAPI.refresh();
      await fetchData();
      toast.success('Server status refreshed');
    } catch (error) {
      toast.error('Failed to refresh servers');
    } finally {
      setRefreshing(false);
    }
  };

  const totalPlayers = servers.reduce((acc, s) => acc + s.current_players, 0);
  const totalMaxPlayers = servers.reduce((acc, s) => acc + s.max_players, 0);
  const onlineServers = servers.filter((s) => s.is_online).length;
  const totalStaff = servers.reduce((acc, s) => acc + s.staff_online, 0);

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
          <h1 className="text-2xl font-bold text-white">Server Status</h1>
          <p className="text-gray-400 mt-1">
            Monitor Elitelupus game servers in real-time
          </p>
        </div>
        <div className="flex items-center gap-4">
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
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-primary flex items-center gap-2"
          >
            <ArrowPathIcon
              className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
            />
            Refresh
          </button>
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <ServerIcon className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Servers Online</p>
              <p className="text-2xl font-bold text-white">
                {onlineServers} / {servers.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/20">
              <UsersIcon className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total Players</p>
              <p className="text-2xl font-bold text-white">
                {totalPlayers} / {totalMaxPlayers}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/20">
              <ChartBarIcon className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Staff Online</p>
              <p className="text-2xl font-bold text-white">{totalStaff}</p>
            </div>
          </div>
        </div>
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-orange-500/20">
              <ChartBarIcon className="w-5 h-5 text-orange-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Server Capacity</p>
              <p className="text-2xl font-bold text-white">
                {totalMaxPlayers > 0
                  ? Math.round((totalPlayers / totalMaxPlayers) * 100)
                  : 0}
                %
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Server Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {servers.map((server) => (
          <ServerStatusCard key={server.id} server={server} />
        ))}
      </div>

      {/* Staff Distribution */}
      {distribution.length > 0 && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            Staff Distribution
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {distribution.map((dist) => (
              <div key={dist.server_id}>
                <h3 className="text-md font-medium text-gray-300 mb-3">
                  {dist.server_name}
                </h3>
                {dist.staff.length === 0 ? (
                  <p className="text-gray-500 text-sm">No staff online</p>
                ) : (
                  <div className="space-y-2">
                    {dist.staff.map((member, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between py-2 px-3 bg-dark-bg rounded-lg"
                      >
                        <span className="text-white">
                          {member.display_name || member.username}
                        </span>
                        <span
                          className="text-sm font-medium px-2 py-1 rounded"
                          style={{
                            backgroundColor: `${member.role_color}20`,
                            color: member.role_color,
                          }}
                        >
                          {member.role}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
