'use client';

import { UsersIcon, MapIcon, SignalIcon, SignalSlashIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';

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
  
  const playerPercentage = server.max_players > 0 
    ? (server.current_players / server.max_players) * 100 
    : 0;

  const handleViewStats = () => {
    router.push(`/servers/${server.id}/stats`);
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

            {/* Stats Button */}
            <button
              onClick={handleViewStats}
              className="w-full mt-3 flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 text-white py-2 px-4 rounded-lg transition-colors duration-200"
            >
              <ChartBarIcon className="w-4 h-4" />
              View Server Stats
            </button>

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
    </div>
  );
}
