'use client';

import { useState, useEffect } from 'react';
import { staffAPI } from '@/lib/api';
import {
  UsersIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  GlobeAltIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface StaffMember {
  id: number;
  username: string;
  display_name: string;
  role: string;
  role_color: string;
  role_priority: number;
  steam_id: string;
  discord_id: string;
  joined_date: string;
  timezone: string;
  is_active: boolean;
  is_on_loa: boolean;
  loa_end_date: string | null;
  last_activity: string;
}

interface SyncLog {
  id: number;
  synced_at: string;
  status: string;
  records_updated: number;
  error_message: string;
}

export default function StaffPage() {
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [syncLogs, setSyncLogs] = useState<SyncLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [rosterRes, logsRes] = await Promise.all([
        staffAPI.roster(),
        staffAPI.syncLogs(),
      ]);
      setStaff(rosterRes.data.results || rosterRes.data);
      setSyncLogs(logsRes.data.results || logsRes.data);
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

  const filteredStaff = staff.filter((member) => {
    const matchesSearch =
      member.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.display_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.steam_id?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole =
      roleFilter === 'all' || member.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const uniqueRoles = [...new Set(staff.map((s) => s.role))].sort(
    (a, b) => {
      const aPriority = staff.find((s) => s.role === a)?.role_priority || 100;
      const bPriority = staff.find((s) => s.role === b)?.role_priority || 100;
      return aPriority - bPriority;
    }
  );

  const activeStaff = staff.filter((s) => s.is_active && !s.is_on_loa).length;
  const onLoaStaff = staff.filter((s) => s.is_on_loa).length;

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
          <h1 className="text-2xl font-bold text-white">Staff Roster</h1>
          <p className="text-gray-400 mt-1">
            Synced from Google Sheets • {staff.length} staff members
          </p>
        </div>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="btn-primary flex items-center gap-2"
        >
          <ArrowPathIcon
            className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`}
          />
          {syncing ? 'Syncing...' : 'Sync Now'}
        </button>
      </div>

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
        </div>
      </div>

      {/* Staff Table */}
      <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-border bg-dark-bg">
                <th className="text-left p-4 text-gray-400 font-medium">
                  Staff Member
                </th>
                <th className="text-left p-4 text-gray-400 font-medium">Role</th>
                <th className="text-left p-4 text-gray-400 font-medium">
                  Steam ID
                </th>
                <th className="text-left p-4 text-gray-400 font-medium">
                  Timezone
                </th>
                <th className="text-left p-4 text-gray-400 font-medium">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredStaff.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
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
                        <p className="text-gray-500 text-sm">
                          @{member.username}
                        </p>
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
                      {member.is_on_loa ? (
                        <span className="px-2 py-1 rounded text-xs font-medium bg-yellow-500/20 text-yellow-400">
                          On LOA
                        </span>
                      ) : member.is_active ? (
                        <span className="px-2 py-1 rounded text-xs font-medium bg-green-500/20 text-green-400">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-1 rounded text-xs font-medium bg-red-500/20 text-red-400">
                          Inactive
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
                  {new Date(log.synced_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
