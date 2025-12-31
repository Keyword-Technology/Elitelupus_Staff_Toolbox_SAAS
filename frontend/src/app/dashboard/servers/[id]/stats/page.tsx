'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { ArrowLeftIcon, ClockIcon, UsersIcon } from '@heroicons/react/24/outline';
import { serverAPI } from '@/lib/api';

interface ServerStatsData {
  server: {
    id: number;
    name: string;
    server_name: string;
    is_online: boolean;
  };
  current_staff: number;
  last_24h: Array<{
    timestamp: string;
    staff_count: number;
    player_count: number;
    is_online: boolean;
  }>;
  hourly_averages: Array<{
    hour: number;
    avg_staff: number;
    avg_players: number;
    sample_count: number;
  }>;
  stats_period: {
    start: string;
    end: string;
    average_period_days: number;
  };
}

export default function ServerStatsPage() {
  const params = useParams();
  const router = useRouter();
  const serverId = params?.id as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statsData, setStatsData] = useState<ServerStatsData | null>(null);

  useEffect(() => {
    fetchServerStats();
  }, [serverId]);

  const fetchServerStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await serverAPI.stats(Number(serverId));
      setStatsData(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load server stats');
      console.error('Error fetching server stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatHour = (hour: number) => {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
    return `${displayHour}${period}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (error || !statsData) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => router.push('/dashboard/servers')}
          className="flex items-center gap-2 text-gray-400 hover:text-white"
        >
          <ArrowLeftIcon className="w-5 h-5" />
          Back to Servers
        </button>
        <div className="bg-red-500/10 border border-red-500 text-red-500 rounded-lg p-6 text-center">
          <p>{error || 'Failed to load server stats'}</p>
        </div>
      </div>
    );
  }

  // Prepare data for 24-hour chart
  const last24hData = statsData.last_24h.map((log) => ({
    time: formatTimestamp(log.timestamp),
    staff: log.staff_count,
    players: log.player_count,
    fullTime: new Date(log.timestamp).toLocaleString(),
  }));

  // Prepare data for hourly averages chart
  const hourlyAveragesData = statsData.hourly_averages.map((avg) => ({
    hour: formatHour(avg.hour),
    hourValue: avg.hour,
    avgStaff: avg.avg_staff,
    avgPlayers: avg.avg_players,
    samples: avg.sample_count,
  }));

  // Find hours with lowest average staff
  const sortedByStaff = [...statsData.hourly_averages].sort(
    (a, b) => a.avg_staff - b.avg_staff
  );
  const lowestStaffHours = sortedByStaff.slice(0, 3).filter(h => h.sample_count > 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => router.push('/dashboard/servers')}
          className="flex items-center gap-2 text-gray-400 hover:text-white mb-4"
        >
          <ArrowLeftIcon className="w-5 h-5" />
          Back to Servers
        </button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              {statsData.server.name} - Statistics
            </h1>
            <p className="text-gray-400">{statsData.server.server_name}</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="bg-dark-card rounded-lg px-4 py-3 border border-dark-border">
              <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
                <UsersIcon className="w-4 h-4" />
                Current Staff
              </div>
              <div className="text-2xl font-bold text-primary-400">
                {statsData.current_staff}
              </div>
            </div>
            
            <div className="bg-dark-card rounded-lg px-4 py-3 border border-dark-border">
              <div className="text-sm text-gray-400 mb-1">Status</div>
              <span
                className={`px-3 py-1 text-sm font-medium rounded-full ${
                  statsData.server.is_online
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-red-500/20 text-red-400'
                }`}
              >
                {statsData.server.is_online ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 24-Hour Staff Tracking */}
      <div className="bg-dark-card rounded-lg p-6 border border-dark-border">
        <div className="flex items-center gap-2 mb-4">
          <ClockIcon className="w-6 h-6 text-primary-400" />
          <h2 className="text-xl font-semibold text-white">
            Staff Presence - Last 24 Hours
          </h2>
        </div>
        
        {last24hData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={last24hData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="time"
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF' }}
                interval="preserveStartEnd"
              />
              <YAxis stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '0.5rem',
                  color: '#fff',
                }}
                labelStyle={{ color: '#9CA3AF' }}
              />
              <Legend
                wrapperStyle={{ color: '#9CA3AF' }}
                iconType="line"
              />
              <Line
                type="monotone"
                dataKey="staff"
                stroke="#8B5CF6"
                strokeWidth={2}
                name="Staff Count"
                dot={{ fill: '#8B5CF6', r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="players"
                stroke="#3B82F6"
                strokeWidth={2}
                name="Total Players"
                dot={{ fill: '#3B82F6', r: 3 }}
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <p>No data available for the last 24 hours</p>
          </div>
        )}
      </div>

      {/* Average Daily Staff Distribution */}
      <div className="bg-dark-card rounded-lg p-6 border border-dark-border">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-white mb-2">
            Average Hourly Staff Distribution
          </h2>
          <p className="text-sm text-gray-400">
            Based on {statsData.stats_period.average_period_days} days of data
          </p>
        </div>
        
        {hourlyAveragesData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={hourlyAveragesData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="hour"
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF' }}
              />
              <YAxis stroke="#9CA3AF" tick={{ fill: '#9CA3AF' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '0.5rem',
                  color: '#fff',
                }}
                labelStyle={{ color: '#9CA3AF' }}
              />
              <Legend
                wrapperStyle={{ color: '#9CA3AF' }}
              />
              <Bar
                dataKey="avgStaff"
                fill="#8B5CF6"
                name="Avg Staff"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="avgPlayers"
                fill="#3B82F6"
                name="Avg Players"
                radius={[4, 4, 0, 0]}
                fillOpacity={0.5}
              />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12 text-gray-500">
            <p>No historical data available</p>
          </div>
        )}
      </div>

      {/* Insights Panel */}
      {lowestStaffHours.length > 0 && (
        <div className="bg-dark-card rounded-lg p-6 border border-dark-border">
          <h2 className="text-xl font-semibold text-white mb-4">
            Staffing Insights
          </h2>
          
          <div className="space-y-4">
            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
              <h3 className="text-yellow-400 font-semibold mb-2">
                Hours with Lowest Staff Coverage
              </h3>
              <div className="space-y-2">
                {lowestStaffHours.map((hour, idx) => (
                  <div
                    key={hour.hour}
                    className="flex items-center justify-between text-sm"
                  >
                    <span className="text-gray-300">
                      #{idx + 1}: {formatHour(hour.hour)}
                    </span>
                    <span className="text-yellow-400 font-medium">
                      {hour.avg_staff.toFixed(2)} avg staff
                    </span>
                  </div>
                ))}
              </div>
            </div>
            
            <p className="text-gray-400 text-sm">
              Consider scheduling more staff during these hours to improve coverage.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
