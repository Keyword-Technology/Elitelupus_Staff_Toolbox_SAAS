'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { staffAPI } from '@/lib/api';
import {
  ArrowLeftIcon,
  UsersIcon,
  MagnifyingGlassIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  EyeIcon,
  GlobeAltIcon,
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

export default function LegacyStaffPage() {
  const router = useRouter();
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState('rank_priority');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    fetchLegacyStaff();
  }, [sortBy, sortOrder]);

  const fetchLegacyStaff = async () => {
    try {
      const orderingParam = sortOrder === 'desc' ? `-${sortBy}` : sortBy;
      const response = await staffAPI.roster(`?show_inactive=true&ordering=${orderingParam}`);
      
      // Handle paginated response
      const staffData = Array.isArray(response.data) ? response.data : (response.data?.results || []);
      
      // Filter to only show inactive staff
      const inactiveStaff = staffData.filter((s: StaffMember) => !s.is_active);
      setStaff(inactiveStaff);
      
      if (inactiveStaff.length === 0) {
        console.log('No inactive staff members found');
      }
    } catch (error: any) {
      console.error('Error loading legacy staff:', error);
      toast.error(`Failed to load legacy staff: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const renderSortIcon = (field: string) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? (
      <ChevronUpIcon className="w-4 h-4" />
    ) : (
      <ChevronDownIcon className="w-4 h-4" />
    );
  };

  const filteredStaff = staff.filter((member) => {
    const matchesSearch =
      member.display_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      member.role.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesRole = roleFilter === 'all' || member.role === roleFilter;

    return matchesSearch && matchesRole;
  });

  const uniqueRoles = [...new Set(staff.map((s) => s.role))].sort(
    (a, b) => {
      const aPriority = staff.find((s) => s.role === a)?.role_priority || 100;
      const bPriority = staff.find((s) => s.role === b)?.role_priority || 100;
      return aPriority - bPriority;
    }
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <div>
        <button
          onClick={() => router.push('/dashboard/staff')}
          className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeftIcon className="w-5 h-5" />
          <span>Back to Staff Roster</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gray-500/20">
              <UsersIcon className="w-5 h-5 text-gray-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Total Legacy Staff</p>
              <p className="text-2xl font-bold text-white">{staff.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-dark-card rounded-lg border border-dark-border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <UsersIcon className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-400">Unique Roles</p>
              <p className="text-2xl font-bold text-white">{uniqueRoles.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by name or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-card border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="px-4 py-2 bg-dark-card border border-dark-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="all">All Roles</option>
          {uniqueRoles.map((role) => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </select>
      </div>

      {/* Staff Table */}
      <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-border bg-dark-bg">
                <th
                  onClick={() => handleSort('username')}
                  className="text-left p-4 text-gray-400 font-medium cursor-pointer hover:text-gray-300 transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    Name
                    {renderSortIcon('username')}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('rank_priority')}
                  className="text-left p-4 text-gray-400 font-medium cursor-pointer hover:text-gray-300 transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    Rank
                    {renderSortIcon('rank_priority')}
                  </div>
                </th>
                <th className="text-left p-4 text-gray-400 font-medium">
                  Steam ID
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
                    colSpan={6}
                    className="text-center py-8 text-gray-500"
                  >
                    No legacy staff members found
                  </td>
                </tr>
              ) : (
                filteredStaff.map((member) => (
                  <tr
                    key={member.id}
                    className="border-b border-dark-border hover:bg-dark-bg transition-colors opacity-75"
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
                      {member.discord_status ? (
                        <DiscordStatusBadge
                          status={member.discord_status}
                          customStatus={member.discord_custom_status}
                          activity={member.discord_activity}
                          showText={true}
                          size="sm"
                        />
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
                        className="flex items-center gap-2 px-3 py-1.5 rounded bg-gray-500/20 text-gray-400 hover:bg-gray-500/30 transition-colors"
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
      </div>
    </div>
  );
}
