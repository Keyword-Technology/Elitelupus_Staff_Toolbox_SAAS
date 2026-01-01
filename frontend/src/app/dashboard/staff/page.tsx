'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { staffAPI } from '@/lib/api';
import { usePageActions } from '@/contexts/PageActionsContext';
import { useAuth } from '@/contexts/AuthContext';
import { useWebSocket } from '@/contexts/WebSocketContext';
import { useFormatDate } from '@/hooks/useFormatDate';
import {
  UsersIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  GlobeAltIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  EyeIcon,
  WifiIcon,
  SignalIcon,
  CloudArrowDownIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import DiscordStatusBadge from '@/components/staff/DiscordStatusBadge';

interface StaffMember {
  id: number;
  username: string;
  display_name: string;
  role: string;
  role_color: string;
  role_priority: number;
  steam_id: string;
  discord_id: string;
  discord_tag: string;
  discord_status?: 'online' | 'idle' | 'dnd' | 'offline' | null;
  discord_custom_status?: string | null;
  discord_activity?: string | null;
  discord_status_updated?: string | null;
  last_seen?: string | null;
  is_active_in_app?: boolean;
  last_seen_display?: string | null;
  is_active_display?: boolean;
  last_seen_ago?: string | null;
  joined_date: string;
  timezone: string;
  is_active: boolean;
  is_on_loa: boolean;
  loa_end_date: string | null;
  last_activity: string;
  is_online: boolean;
  server_name: string | null;
  server_id: number | null;
}

interface SyncLog {
  id: number;
  synced_at: string;
  status: string;
  records_updated: number;
  error_message: string;
}

export default function StaffPage() {
  const router = useRouter();
  const { setActions } = usePageActions();
  const { hasMinRole, user: currentUser } = useAuth();
  const { onStaffOnlineChange, onStaffDiscordStatus, onRosterSync, connectionStatus } = useWebSocket();
  const { formatDateTime } = useFormatDate();
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [syncLogs, setSyncLogs] = useState<SyncLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncingSteamNames, setSyncingSteamNames] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [sortBy, setSortBy] = useState('rank_priority');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every minute for local time display
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  // Helper function to get current time in a specific timezone
  const getTimeInTimezone = (timezone: string | null): string => {
    if (!timezone) return '-';
    
    const use24Hour = currentUser?.use_24_hour_time ?? true;
    
    // Try to parse GMT offset format (e.g., "GMT", "GMT-5", "GMT+3")
    const gmtMatch = timezone.match(/^GMT([+-]?\d+)?$/i);
    if (gmtMatch) {
      const offset = gmtMatch[1] ? parseInt(gmtMatch[1]) : 0;
      const utcTime = currentTime.getTime() + (currentTime.getTimezoneOffset() * 60000);
      const targetTime = new Date(utcTime + (offset * 3600000));
      
      return targetTime.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: !use24Hour,
      });
    }
    
    // Try as IANA timezone (e.g., "America/New_York")
    try {
      return currentTime.toLocaleTimeString('en-US', {
        timeZone: timezone,
        hour: '2-digit',
        minute: '2-digit',
        hour12: !use24Hour,
      });
    } catch (e) {
      // Invalid timezone
      return '-';
    }
  };

  // Check if user has manager permissions (priority <= 10)
  const isManager = hasMinRole(10);
  
  // Check if user is sysadmin (priority = 0)
  const isSysAdmin = currentUser?.role === 'SYSADMIN' || hasMinRole(0);

  // Handle real-time staff online status changes
  useEffect(() => {
    const unsubscribe = onStaffOnlineChange((data) => {
      setStaff((prev) =>
        prev.map((s) =>
          s.id === data.staff_id
            ? {
                ...s,
                is_online: data.is_online,
                server_name: data.server_name || null,
                server_id: data.server_id || null,
              }
            : s
        )
      );
    });
    return unsubscribe;
  }, [onStaffOnlineChange]);

  // Handle real-time Discord status changes
  useEffect(() => {
    const unsubscribe = onStaffDiscordStatus((data) => {
      setStaff((prev) =>
        prev.map((s) =>
          s.id === data.staff_id
            ? {
                ...s,
                discord_status: data.discord_status as any,
                discord_custom_status: data.discord_custom_status || null,
                discord_activity: data.discord_activity || null,
              }
            : s
        )
      );
    });
    return unsubscribe;
  }, [onStaffDiscordStatus]);

  // Handle roster sync events - refresh data when sync completes
  useEffect(() => {
    const unsubscribe = onRosterSync((data) => {
      if (data.status === 'success') {
        toast.success(`Staff roster synced: ${data.records_updated} records updated`);
        fetchData();
      } else {
        toast.error('Staff roster sync failed');
      }
    });
    return unsubscribe;
  }, [onRosterSync]);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      // Reset to page 1 when search changes
      if (searchQuery !== debouncedSearch) {
        setCurrentPage(1);
      }
    }, 500); // 500ms delay

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Reset to page 1 when role filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [roleFilter]);

  useEffect(() => {
    fetchData();
  }, [currentPage, pageSize, sortBy, sortOrder, debouncedSearch, roleFilter, isManager]);

  useEffect(() => {
    setActions(
      <div className="flex items-center gap-2">
        <button
          onClick={() => router.push('/dashboard/staff/legacy')}
          className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
        >
          <ClockIcon className="w-4 h-4" />
          Legacy Staff
        </button>
        {isSysAdmin && (
          <button
            onClick={handleSyncSteamNames}
            disabled={syncingSteamNames}
            className="flex items-center gap-2 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white rounded-lg transition-colors text-sm"
            title="Fetch Steam display names for all staff members"
          >
            <CloudArrowDownIcon className={`w-4 h-4 ${syncingSteamNames ? 'animate-pulse' : ''}`} />
            {syncingSteamNames ? 'Syncing...' : 'Sync Steam Names'}
          </button>
        )}
        {isManager && (
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 text-white rounded-lg transition-colors text-sm"
          >
            <ArrowPathIcon className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync Now'}
          </button>
        )}
      </div>
    );
    return () => setActions(null);
  }, [setActions, syncing, syncingSteamNames, router, isManager, isSysAdmin]);

  const fetchData = async () => {
    try {
      const orderingParam = sortOrder === 'desc' ? `-${sortBy}` : sortBy;
      
      // Build query params
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
        ordering: orderingParam,
      });
      
      // Add search param if present
      if (debouncedSearch.trim()) {
        params.append('search', debouncedSearch.trim());
      }
      
      // Add role filter if not 'all'
      if (roleFilter !== 'all') {
        params.append('role', roleFilter);
      }
      
      // Fetch roster data (all users can view)
      const rosterRes = await staffAPI.roster(`?${params.toString()}`);
      
      // Handle paginated response
      if (rosterRes.data.results) {
        setStaff(rosterRes.data.results);
        setTotalCount(rosterRes.data.count || 0);
      } else {
        setStaff(rosterRes.data);
        setTotalCount(rosterRes.data.length);
      }
      
      // Only fetch sync logs if user is a manager
      if (isManager) {
        try {
          const logsRes = await staffAPI.syncLogs();
          setSyncLogs(logsRes.data.results || logsRes.data);
        } catch (error) {
          // Silently fail if sync logs can't be fetched
          console.warn('Could not fetch sync logs:', error);
        }
      }
    } catch (error) {
      toast.error('Failed to load staff roster');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await staffAPI.sync();
      toast.success('Staff roster synced successfully');
      fetchData();
    } catch (error) {
      toast.error('Failed to sync staff roster');
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncSteamNames = async () => {
    setSyncingSteamNames(true);
    try {
      const response = await staffAPI.syncSteamNames();
      const { updated, total, success, errors } = response.data;
      
      if (success) {
        toast.success(`Steam names synced: ${updated}/${total} updated`);
      } else if (errors && errors.length > 0) {
        toast.error(`Steam name sync completed with errors: ${errors[0]}`);
      } else {
        toast.error('Steam name sync failed');
      }
    } catch (error: any) {
      const message = error?.response?.data?.error || 'Failed to sync Steam names';
      toast.error(message);
    } finally {
      setSyncingSteamNames(false);
    }
  };

  const handleSort = (column: string) => {
    if (sortBy === column) {
      // Toggle sort order if clicking the same column
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new column and default to ascending
      setSortBy(column);
      setSortOrder('asc');
    }
    setCurrentPage(1); // Reset to first page when sorting
  };

  const renderSortIcon = (column: string) => {
    if (sortBy !== column) {
      return <ChevronUpIcon className="w-4 h-4 text-gray-600 opacity-0 group-hover:opacity-50 transition-opacity" />;
    }
    return sortOrder === 'asc' ? (
      <ChevronUpIcon className="w-4 h-4 text-primary-500" />
    ) : (
      <ChevronDownIcon className="w-4 h-4 text-primary-500" />
    );
  };

  // Note: Filtering and sorting now done server-side via API
  // Client-side filtering would only filter the current page, not all results
  const filteredStaff = staff;

  const uniqueRoles = [...new Set(staff.map((s) => s.role))].sort(
    (a, b) => {
      const aPriority = staff.find((s) => s.role === a)?.role_priority || 100;
      const bPriority = staff.find((s) => s.role === b)?.role_priority || 100;
      return aPriority - bPriority;
    }
  );

  const activeStaff = staff.filter((s) => s.is_active && !s.is_on_loa).length;
  const onLoaStaff = staff.filter((s) => s.is_on_loa).length;
  const onlineStaff = staff.filter((s) => s.is_online).length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <UsersIcon className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total Staff</p>
              <p className="text-2xl font-bold text-white">{staff.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/20">
              <UsersIcon className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Active Staff</p>
              <p className="text-2xl font-bold text-white">{activeStaff}</p>
              <p className="text-xs text-green-400 mt-1">{onlineStaff} online</p>
            </div>
          </div>
        </div>
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-yellow-500/20">
              <ClockIcon className="w-5 h-5 text-yellow-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">On LOA</p>
              <p className="text-2xl font-bold text-white">{onLoaStaff}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by name or Steam ID..."
              className="input w-full pl-10"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="input md:w-48"
          >
            <option value="all">All Roles</option>
            {uniqueRoles.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="input md:w-32"
          >
            <option value="10">10 per page</option>
            <option value="25">25 per page</option>
            <option value="50">50 per page</option>
            <option value="100">100 per page</option>
          </select>
        </div>
      </div>

      {/* Staff Table */}
      <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-border bg-dark-bg">
                <th 
                  onClick={() => handleSort('name')}
                  className="text-left p-4 text-gray-400 font-medium cursor-pointer hover:text-gray-300 transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    Staff Member
                    {renderSortIcon('name')}
                  </div>
                </th>
                <th 
                  onClick={() => handleSort('rank_priority')}
                  className="text-left p-4 text-gray-400 font-medium cursor-pointer hover:text-gray-300 transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    Role
                    {renderSortIcon('rank_priority')}
                  </div>
                </th>
                <th 
                  onClick={() => handleSort('steam_id')}
                  className="text-left p-4 text-gray-400 font-medium cursor-pointer hover:text-gray-300 transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    Steam ID
                    {renderSortIcon('steam_id')}
                  </div>
                </th>
                <th 
                  onClick={() => handleSort('timezone')}
                  className="text-left p-4 text-gray-400 font-medium cursor-pointer hover:text-gray-300 transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    Timezone
                    {renderSortIcon('timezone')}
                  </div>
                </th>
                <th className="text-left p-4 text-gray-400 font-medium">
                  <div className="flex items-center gap-2">
                    <ClockIcon className="w-4 h-4" />
                    Local Time
                  </div>
                </th>
                <th className="text-left p-4 text-gray-400 font-medium">
                  <div className="flex items-center gap-2">
                    <WifiIcon className="w-4 h-4" />
                    Last Seen
                  </div>
                </th>
                <th className="text-left p-4 text-gray-400 font-medium">
                  Discord Status
                </th>
                <th className="text-left p-4 text-gray-400 font-medium">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredStaff.length === 0 ? (
                <tr>
                  <td
                    colSpan={8}
                    className="text-center py-8 text-gray-500"
                  >
                    No staff members found
                  </td>
                </tr>
              ) : (
                filteredStaff.map((member) => (
                  <tr
                    key={member.id}
                    className="border-b border-dark-border hover:bg-dark-bg transition-colors"
                  >
                    <td className="p-4">
                      <div>
                        <p className="text-white font-medium">
                          {member.display_name || member.username}
                        </p>
                        {member.role && (
                          <p className="text-gray-500 text-sm">
                            {member.role}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      <span
                        className="px-2 py-1 rounded text-sm font-medium"
                        style={{
                          backgroundColor: `${member.role_color}20`,
                          color: member.role_color,
                        }}
                      >
                        {member.role}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="text-gray-400 font-mono text-sm">
                        {member.steam_id || 'N/A'}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2 text-gray-400 text-sm">
                        <GlobeAltIcon className="w-4 h-4" />
                        {member.timezone || 'Not set'}
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="text-gray-300 text-sm font-mono">
                        {getTimeInTimezone(member.timezone)}
                      </span>
                    </td>
                    <td className="p-4">
                      {member.is_online ? (
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                          <div className="flex flex-col">
                            <span className="text-green-400 text-sm font-medium">
                              Online
                            </span>
                            <span className="text-xs text-gray-400">
                              {member.server_name}
                            </span>
                          </div>
                        </div>
                      ) : member.last_seen_ago ? (
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-gray-600" />
                          <span className="text-gray-400 text-sm">
                            {member.last_seen_ago}
                          </span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-gray-700" />
                          <span className="text-gray-500 text-sm">
                            Never
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="p-4">
                      {member.discord_status ? (
                        <DiscordStatusBadge
                          status={member.discord_status}
                          customStatus={member.discord_custom_status}
                          activity={member.discord_activity}
                          showText={true}
                          size="sm"
                        />
                      ) : member.is_active_display ? (
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-green-400">
                              Active in App
                            </span>
                            <span className="text-xs text-gray-500">
                              {member.last_seen_display || 'Just now'}
                            </span>
                          </div>
                        </div>
                      ) : member.last_seen ? (
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-gray-600" />
                          <span className="text-gray-500 text-sm">
                            {member.last_seen_display || 'Inactive'}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-500 text-sm">Not linked</span>
                      )}
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => router.push(`/dashboard/staff/${member.id}`)}
                        className="flex items-center gap-2 px-3 py-1.5 rounded bg-primary-500/20 text-primary-400 hover:bg-primary-500/30 transition-colors"
                        title="View Details"
                      >
                        <EyeIcon className="w-4 h-4" />
                        <span className="text-sm font-medium">Details</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        {totalCount > pageSize && (
          <div className="px-4 py-3 border-t border-dark-border flex items-center justify-between">
            <div className="text-sm text-gray-400">
              Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalCount)} of {totalCount} staff members
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 rounded border border-dark-border text-gray-400 hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <div className="flex gap-1">
                {Array.from({ length: Math.ceil(totalCount / pageSize) }, (_, i) => i + 1)
                  .filter((page) => {
                    // Show first, last, current, and adjacent pages
                    return (
                      page === 1 ||
                      page === Math.ceil(totalCount / pageSize) ||
                      Math.abs(page - currentPage) <= 1
                    );
                  })
                  .map((page, idx, arr) => (
                    <div key={page} className="flex gap-1">
                      {idx > 0 && arr[idx - 1] !== page - 1 && (
                        <span className="px-2 py-1 text-gray-500">...</span>
                      )}
                      <button
                        onClick={() => setCurrentPage(page)}
                        className={`px-3 py-1 rounded border ${
                          currentPage === page
                            ? 'bg-primary-500 border-primary-500 text-white'
                            : 'border-dark-border text-gray-400 hover:bg-dark-bg'
                        } transition-colors`}
                      >
                        {page}
                      </button>
                    </div>
                  ))}
              </div>
              <button
                onClick={() => setCurrentPage((p) => Math.min(Math.ceil(totalCount / pageSize), p + 1))}
                disabled={currentPage >= Math.ceil(totalCount / pageSize)}
                className="px-3 py-1 rounded border border-dark-border text-gray-400 hover:bg-dark-bg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Recent Sync Logs */}
      {syncLogs.length > 0 && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            Recent Sync History
          </h2>
          <div className="space-y-3">
            {syncLogs.slice(0, 5).map((log) => (
              <div
                key={log.id}
                className="flex items-center justify-between py-2 border-b border-dark-border last:border-0"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      log.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                    }`}
                  />
                  <span className="text-white">
                    {log.records_updated} records updated
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {formatDateTime(log.synced_at)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
