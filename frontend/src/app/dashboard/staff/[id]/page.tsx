'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { staffAPI } from '@/lib/api';
import {
  ArrowLeftIcon,
  ClockIcon,
  ServerIcon,
  ChartBarIcon,
  CalendarIcon,
  UserIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface HistoryEvent {
  id: number;
  event_type: string;
  event_type_display: string;
  old_rank: string | null;
  new_rank: string | null;
  old_rank_color: string | null;
  new_rank_color: string | null;
  event_date: string;
  event_description: string;
  is_promotion: boolean;
  is_demotion: boolean;
  notes: string;
}

interface StaffDetails {
  id: number;
  username: string;
  display_name: string;
  role: string;
  role_color: string;
  role_priority: number;
  steam_id: string;
  discord_id: string;
  discord_tag: string;
  timezone: string;
  is_active: boolean;
  total_server_time: number;
  total_sessions: number;
  avg_session_duration: number;
  last_server_join: string | null;
  server_time_breakdown: ServerTimeBreakdown[];
  sit_count: number;
  ticket_count: number;
  recent_sessions: ServerSession[];
  history_events: HistoryEvent[];
}

interface ServerTimeBreakdown {
  server_id: number;
  server_name: string;
  total_time: number;
  session_count: number;
  avg_duration: number;
}

interface ServerSession {
  id: number;
  staff_name: string;
  server_name: string;
  join_time: string;
  leave_time: string | null;
  duration: number;
  duration_formatted: string;
  is_active: boolean;
}

export default function StaffDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const staffId = params?.id as string;
  
  const [loading, setLoading] = useState(true);
  const [details, setDetails] = useState<StaffDetails | null>(null);
  const [sessionsFilter, setSessionsFilter] = useState<'all' | 'active'>('all');

  useEffect(() => {
    if (staffId) {
      fetchDetails();
    }
  }, [staffId]);

  const fetchDetails = async () => {
    try {
      const response = await staffAPI.details(Number(staffId));
      setDetails(response.data);
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('You do not have permission to view staff details');
        router.push('/dashboard/staff');
      } else {
        toast.error('Failed to load staff details');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-400">Staff member not found</p>
      </div>
    );
  }

  const filteredSessions = sessionsFilter === 'active'
    ? details.recent_sessions.filter(s => s.is_active)
    : details.recent_sessions;

  // Find active session if exists
  const activeSession = details.recent_sessions.find(s => s.is_active);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push('/dashboard/staff')}
            className="p-2 rounded-lg hover:bg-dark-bg transition-colors"
          >
            <ArrowLeftIcon className="w-5 h-5 text-gray-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white">
              {details.display_name || details.username}
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span
                className="px-2 py-1 rounded text-sm font-medium"
                style={{
                  backgroundColor: `${details.role_color}20`,
                  color: details.role_color,
                }}
              >
                {details.role}
              </span>
              {details.is_active ? (
                <span className="px-2 py-1 rounded text-xs font-medium bg-green-500/20 text-green-400">
                  Active
                </span>
              ) : (
                <span className="px-2 py-1 rounded text-xs font-medium bg-red-500/20 text-red-400">
                  Inactive
                </span>
              )}
              {activeSession && (
                <span className="px-2 py-1 rounded text-xs font-medium bg-blue-500/20 text-blue-400 flex items-center gap-1">
                  <ServerIcon className="w-3 h-3" />
                  Online: {activeSession.server_name}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Active Session Alert */}
      {activeSession && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <ServerIcon className="w-5 h-5 text-blue-400 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-blue-400 font-semibold mb-1">Currently Online</h3>
              <div className="text-sm text-gray-300 space-y-1">
                <p><span className="text-gray-400">Server:</span> {activeSession.server_name}</p>
                <p><span className="text-gray-400">Session Duration:</span> {activeSession.duration_formatted}</p>
                <p><span className="text-gray-400">Joined:</span> {formatDate(activeSession.join_time)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <ClockIcon className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total Server Time</p>
              <p className="text-xl font-bold text-white">
                {formatDuration(details.total_server_time)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/20">
              <ServerIcon className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total Sessions</p>
              <p className="text-xl font-bold text-white">{details.total_sessions}</p>
            </div>
          </div>
        </div>

        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/20">
              <ChartBarIcon className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Sits Tracked</p>
              <p className="text-xl font-bold text-white">{details.sit_count}</p>
            </div>
          </div>
        </div>

        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-yellow-500/20">
              <ChartBarIcon className="w-5 h-5 text-yellow-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Tickets Tracked</p>
              <p className="text-xl font-bold text-white">{details.ticket_count}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Session Habits */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Session Habits</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Average Session Time</span>
              <span className="text-white font-medium">
                {formatDuration(details.avg_session_duration)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Last Server Join</span>
              <span className="text-white font-medium">
                {formatDate(details.last_server_join)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Timezone</span>
              <span className="text-white font-medium">{details.timezone || 'Not set'}</span>
            </div>
          </div>
        </div>

        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Account Info</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Steam ID</span>
              <span className="text-white font-mono text-sm">
                {details.steam_id || 'Not linked'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Discord</span>
              <span className="text-white text-sm">
                {details.discord_tag || 'Not linked'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Time per Server */}
      {details.server_time_breakdown.length > 0 && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Time per Server</h2>
          <div className="space-y-4">
            {details.server_time_breakdown.map((server) => (
              <div key={server.server_id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-white font-medium">{server.server_name}</span>
                  <span className="text-gray-400">
                    {formatDuration(server.total_time)} • {server.session_count} sessions
                  </span>
                </div>
                <div className="w-full bg-dark-bg rounded-full h-2">
                  <div
                    className="bg-primary-500 h-2 rounded-full"
                    style={{
                      width: `${(server.total_time / details.total_server_time) * 100}%`,
                    }}
                  />
                </div>
                <div className="text-sm text-gray-500">
                  Avg: {formatDuration(server.avg_duration)} per session
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Sessions */}
      <div className="bg-dark-card rounded-lg border border-dark-border">
        <div className="p-6 border-b border-dark-border flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Recent Sessions</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setSessionsFilter('all')}
              className={`px-3 py-1 rounded text-sm ${
                sessionsFilter === 'all'
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              } transition-colors`}
            >
              All
            </button>
            <button
              onClick={() => setSessionsFilter('active')}
              className={`px-3 py-1 rounded text-sm ${
                sessionsFilter === 'active'
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-bg text-gray-400 hover:text-white'
              } transition-colors`}
            >
              Active
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-border bg-dark-bg">
                <th className="text-left p-4 text-gray-400 font-medium">Server</th>
                <th className="text-left p-4 text-gray-400 font-medium">Join Time</th>
                <th className="text-left p-4 text-gray-400 font-medium">Leave Time</th>
                <th className="text-left p-4 text-gray-400 font-medium">Duration</th>
                <th className="text-left p-4 text-gray-400 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredSessions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-500">
                    No sessions found
                  </td>
                </tr>
              ) : (
                filteredSessions.map((session) => (
                  <tr
                    key={session.id}
                    className="border-b border-dark-border hover:bg-dark-bg transition-colors"
                  >
                    <td className="p-4">
                      <span className="text-white font-medium">{session.server_name}</span>
                    </td>
                    <td className="p-4">
                      <span className="text-gray-400 text-sm">
                        {formatDate(session.join_time)}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="text-gray-400 text-sm">
                        {formatDate(session.leave_time)}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="text-white">{session.duration_formatted}</span>
                    </td>
                    <td className="p-4">
                      {session.is_active ? (
                        <span className="px-2 py-1 rounded text-xs font-medium bg-green-500/20 text-green-400">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-1 rounded text-xs font-medium bg-gray-500/20 text-gray-400">
                          Ended
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Staff Timeline */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
          <CalendarIcon className="w-5 h-5" />
          Staff Timeline
        </h2>
        
        {details.history_events && details.history_events.length > 0 ? (
          <div className="space-y-6">
            {details.history_events.map((event, index) => (
              <div key={event.id} className="relative pl-8">
                {/* Timeline line */}
                {index < details.history_events.length - 1 && (
                  <div className="absolute left-2 top-8 bottom-0 w-0.5 bg-dark-border" />
                )}
                
                {/* Timeline dot */}
                <div
                  className={`absolute left-0 top-1 w-4 h-4 rounded-full border-2 ${
                    event.event_type === 'joined' || event.event_type === 'rejoined'
                      ? 'bg-green-500 border-green-400'
                      : event.event_type === 'promoted' || event.is_promotion
                      ? 'bg-blue-500 border-blue-400'
                      : event.event_type === 'demoted' || event.is_demotion
                      ? 'bg-orange-500 border-orange-400'
                      : event.event_type === 'removed' || event.event_type === 'left'
                      ? 'bg-red-500 border-red-400'
                      : event.event_type === 'loa_start'
                      ? 'bg-yellow-500 border-yellow-400'
                      : event.event_type === 'loa_end'
                      ? 'bg-green-500 border-green-400'
                      : 'bg-gray-500 border-gray-400'
                  }`}
                />
                
                {/* Event content */}
                <div className="flex items-start gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      {/* Event icon */}
                      {(event.event_type === 'joined' || event.event_type === 'rejoined') && (
                        <UserIcon className="w-4 h-4 text-green-400" />
                      )}
                      {(event.event_type === 'promoted' || event.is_promotion) && (
                        <ArrowTrendingUpIcon className="w-4 h-4 text-blue-400" />
                      )}
                      {(event.event_type === 'demoted' || event.is_demotion) && (
                        <ArrowTrendingDownIcon className="w-4 h-4 text-orange-400" />
                      )}
                      {event.event_type === 'role_change' && !event.is_promotion && !event.is_demotion && (
                        <ArrowRightIcon className="w-4 h-4 text-gray-400" />
                      )}
                      {event.event_type === 'loa_start' && (
                        <ClockIcon className="w-4 h-4 text-yellow-400" />
                      )}
                      {event.event_type === 'loa_end' && (
                        <ClockIcon className="w-4 h-4 text-green-400" />
                      )}
                      
                      {/* Event type */}
                      <span
                        className={`text-sm font-semibold ${
                          event.event_type === 'joined' || event.event_type === 'rejoined'
                            ? 'text-green-400'
                            : event.event_type === 'promoted' || event.is_promotion
                            ? 'text-blue-400'
                            : event.event_type === 'demoted' || event.is_demotion
                            ? 'text-orange-400'
                            : event.event_type === 'removed' || event.event_type === 'left'
                            ? 'text-red-400'
                            : event.event_type === 'loa_start'
                            ? 'text-yellow-400'
                            : event.event_type === 'loa_end'
                            ? 'text-green-400'
                            : 'text-gray-400'
                        }`}
                      >
                        {event.event_type_display}
                      </span>
                    </div>
                    
                    {/* Event description with rank badges */}
                    <div className="flex items-center gap-2 flex-wrap">
                      {event.old_rank && (
                        <span
                          className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{
                            backgroundColor: `${event.old_rank_color}20`,
                            color: event.old_rank_color || '#808080',
                          }}
                        >
                          {event.old_rank}
                        </span>
                      )}
                      
                      {event.old_rank && event.new_rank && (
                        <ArrowRightIcon className="w-3 h-3 text-gray-500" />
                      )}
                      
                      {event.new_rank && (
                        <span
                          className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{
                            backgroundColor: `${event.new_rank_color}20`,
                            color: event.new_rank_color || '#808080',
                          }}
                        >
                          {event.new_rank}
                        </span>
                      )}
                    </div>
                    
                    {/* Notes if any */}
                    {event.notes && (
                      <p className="text-sm text-gray-400 mt-2">{event.notes}</p>
                    )}
                  </div>
                  
                  {/* Date */}
                  <div className="text-right">
                    <div className="text-sm text-gray-400">
                      {new Date(event.event_date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(event.event_date).toLocaleTimeString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <CalendarIcon className="w-12 h-12 mx-auto mb-3 text-gray-600" />
            <p className="text-lg mb-1">No timeline events recorded</p>
            <p className="text-sm">
              Staff history events (joins, promotions, demotions, LOA) will appear here once tracked.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
