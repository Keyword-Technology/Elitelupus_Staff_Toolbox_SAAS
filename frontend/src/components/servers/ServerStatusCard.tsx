'use client';

import { useState } from 'react';
import { UsersIcon, MapIcon, SignalIcon, SignalSlashIcon, ChartBarIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import { serverAPI } from '@/lib/api';
import toast from 'react-hot-toast';

interface Player {
  name: string;
  score: number;
  duration: number;
  duration_formatted: string;
  is_staff: boolean;
  staff_rank: string;
}

interface Server {
  id: number;
  name: string;
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
}

interface ServerStatusCardProps {
  server: Server;
}

export function ServerStatusCard({ server }: ServerStatusCardProps) {
  const router = useRouter();
  const [showPlayerList, setShowPlayerList] = useState(false);
  const [players, setPlayers] = useState<Player[]>([]);
  const [loadingPlayers, setLoadingPlayers] = useState(false);
  
  const playerPercentage = server.max_players > 0 
    ? (server.current_players / server.max_players) * 100 
    : 0;

  const handleViewStats = () => {
    router.push(`/dashboard/servers/${server.id}/stats`);
  };

  const handleViewPlayers = async () => {
    setShowPlayerList(true);
    setLoadingPlayers(true);
    try {
      const response = await serverAPI.players(server.id);
      setPlayers(response.data.players || []);
    } catch (error) {
      toast.error('Failed to load player list');
      console.error('Error loading players:', error);
    } finally {
      setLoadingPlayers(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    const parts: string[] = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0 || parts.length === 0) parts.push(`${minutes}m`);
    
    return parts.join(' ');
  };

  return (
    <div className="bg-dark-card rounded-lg p-6 border border-dark-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          {server.is_online ? (
            <SignalIcon className="w-6 h-6 text-green-500" />
          ) : (
            <SignalSlashIcon className="w-6 h-6 text-red-500" />
          )}
          <div>
            <h3 className="text-lg font-semibold text-white">{server.name}</h3>
            <p className="text-sm text-gray-400">{server.server_name || 'Unknown'}</p>
          </div>
        </div>
        <span
          className={`px-2 py-1 text-xs font-medium rounded-full ${
            server.is_online
              ? 'bg-green-500/20 text-green-400'
              : 'bg-red-500/20 text-red-400'
          }`}
        >
          {server.is_online ? 'Online' : 'Offline'}
        </span>
      </div>

      {server.is_online && (
        <>
          <div className="flex items-center gap-2 text-gray-400 text-sm mb-4">
            <MapIcon className="w-4 h-4" />
            <span>{server.map_name || 'Unknown Map'}</span>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400 flex items-center gap-2">
                <UsersIcon className="w-4 h-4" />
                Players
              </span>
              <span className="text-white font-medium">
                {server.current_players} / {server.max_players}
              </span>
            </div>
            
            {/* Progress bar */}
            <div className="h-2 bg-dark-bg rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  playerPercentage > 90
                    ? 'bg-red-500'
                    : playerPercentage > 70
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${playerPercentage}%` }}
              />
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Staff Online</span>
              <span className="text-primary-400 font-medium">{server.staff_online}</span>
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-2 gap-2 mt-3">
              <button
                onClick={handleViewStats}
                className="flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 text-white py-2 px-4 rounded-lg transition-colors duration-200"
              >
                <ChartBarIcon className="w-4 h-4" />
                Stats
              </button>
              <button
                onClick={handleViewPlayers}
                className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors duration-200"
              >
                <UsersIcon className="w-4 h-4" />
                Players
              </button>
            </div>

            {/* Staff badges */}
            {server.staff_list && server.staff_list.length > 0 && (
              <div className="pt-3 border-t border-dark-border">
                <p className="text-xs text-gray-400 mb-2">Staff Members:</p>
                <div className="flex flex-wrap gap-2">
                  {server.staff_list.map((staff, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 text-xs rounded-full font-medium"
                      style={{
                        backgroundColor: `${staff.role_color}20`,
                        color: staff.role_color,
                      }}
                      title={`${staff.name} - ${staff.rank}`}
                    >
                      {staff.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {!server.is_online && (
        <div className="text-center py-4">
          <p className="text-gray-500">Server is currently offline</p>
        </div>
      )}

      {/* Player List Modal */}
      {showPlayerList && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setShowPlayerList(false)}>
          <div className="bg-dark-card rounded-lg border border-dark-border max-w-4xl w-full max-h-[80vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-dark-border">
              <div>
                <h2 className="text-xl font-bold text-white">Player List</h2>
                <p className="text-sm text-gray-400">{server.name} - {players.length} players</p>
              </div>
              <button
                onClick={() => setShowPlayerList(false)}
                className="p-2 rounded-lg hover:bg-dark-bg transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="overflow-auto max-h-[calc(80vh-80px)]">
              {loadingPlayers ? (
                <div className="flex items-center justify-center py-12">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
                </div>
              ) : players.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <p>No players currently online</p>
                </div>
              ) : (
                <table className="w-full">
                  <thead className="bg-dark-bg sticky top-0">
                    <tr>
                      <th className="text-left p-4 text-gray-400 font-medium">Player</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Score</th>
                      <th className="text-left p-4 text-gray-400 font-medium">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {players.map((player, idx) => (
                      <tr
                        key={idx}
                        className={`border-b border-dark-border hover:bg-dark-bg transition-colors ${
                          player.is_staff ? 'bg-primary-500/5' : ''
                        }`}
                      >
                        <td className="p-4">
                          <div className="flex items-center gap-2">
                            <span className="text-white font-medium">{player.name}</span>
                            {player.is_staff && player.staff_rank && (
                              <span className="px-2 py-0.5 text-xs rounded bg-primary-500/20 text-primary-400">
                                {player.staff_rank}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="p-4">
                          <span className="text-gray-300">{player.score}</span>
                        </td>
                        <td className="p-4">
                          <span className="text-gray-400">{formatDuration(player.duration)}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
