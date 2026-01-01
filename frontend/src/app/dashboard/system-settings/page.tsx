'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { systemAPI } from '@/lib/api';
import { useFormatDate } from '@/hooks/useFormatDate';
import {
  Cog6ToothIcon,
  ServerIcon,
  KeyIcon,
  ClockIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  ArrowPathIcon,
  CheckIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';

interface EnvironmentVariable {
  key: string;
  env_value: string | null;
  override_value: string | null;
  effective_value: string;
  is_overridden: boolean;
  is_sensitive: boolean;
  category: string;
  description: string;
}

interface ManagedServer {
  id: number;
  name: string;
  ip_address: string;
  port: number;
  description: string;
  is_active: boolean;
  display_order: number;
  query_port: number | null;
  address: string;
  created_at: string;
  updated_at: string;
  created_by_username: string;
}

interface AuditLog {
  id: number;
  setting_key: string;
  user_username: string;
  old_value: string;
  new_value: string;
  changed_at: string;
  ip_address: string;
}

interface SystemSetting {
  id: number;
  key: string;
  value: string;
  display_value: string;
  setting_type: 'string' | 'integer' | 'boolean' | 'json';
  category: string;
  description: string;
  is_sensitive: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

type TabType = 'settings' | 'environment' | 'servers' | 'audit';

export default function SystemSettingsPage() {
  const { user, hasMinRole } = useAuth();
  const router = useRouter();
  const { formatDateTime } = useFormatDate();
  const [activeTab, setActiveTab] = useState<TabType>('settings');
  const [loading, setLoading] = useState(true);
  const [accessDenied, setAccessDenied] = useState(false);
  
  // System Settings State
  const [systemSettings, setSystemSettings] = useState<SystemSetting[]>([]);
  const [editingSettingId, setEditingSettingId] = useState<number | null>(null);
  const [editingSettingValue, setEditingSettingValue] = useState('');
  
  // Environment Variables State
  const [envVars, setEnvVars] = useState<EnvironmentVariable[]>([]);
  const [editingEnvKey, setEditingEnvKey] = useState<string | null>(null);
  const [editingEnvValue, setEditingEnvValue] = useState('');
  
  // Managed Servers State
  const [servers, setServers] = useState<ManagedServer[]>([]);
  const [showServerModal, setShowServerModal] = useState(false);
  const [editingServer, setEditingServer] = useState<ManagedServer | null>(null);
  const [serverForm, setServerForm] = useState({
    name: '',
    ip_address: '',
    port: 27015 as number | null,
    description: '',
    is_active: true,
    display_order: 0 as number | null,
    query_port: null as number | null,
  });
  
  // Audit Logs State
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);

  // Helper to normalize paginated/non-paginated arrays
  const toArray = <T,>(payload: any): T[] => {
    if (Array.isArray(payload)) return payload as T[];
    if (Array.isArray(payload?.results)) return payload.results as T[];
    return [];
  };
  
  // Check if user has admin access
  useEffect(() => {
    if (user && !hasMinRole(70)) {
      setAccessDenied(true);
      toast.error('You do not have permission to access system settings');
      router.push('/dashboard');
      return;
    }
    if (user && hasMinRole(70)) {
      setAccessDenied(false);
    }
  }, [user, hasMinRole, router]);

  useEffect(() => {
    if (user && hasMinRole(70) && !accessDenied) {
      fetchData();
    }
  }, [activeTab, user, hasMinRole, accessDenied]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'settings') {
        const res = await systemAPI.settings();
        setSystemSettings(toArray<SystemSetting>(res.data));
      } else if (activeTab === 'environment') {
        const res = await systemAPI.envList();
        setEnvVars(toArray<EnvironmentVariable>(res.data));
      } else if (activeTab === 'servers') {
        const res = await systemAPI.servers();
        setServers(toArray<ManagedServer>(res.data));
      } else if (activeTab === 'audit') {
        const res = await systemAPI.auditLogs();
        setAuditLogs(toArray<AuditLog>(res.data));
      }
    } catch (error) {
      toast.error('Failed to load data');
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Environment Variable handlers
  const handleEditSetting = (setting: SystemSetting) => {
    setEditingSettingId(setting.id);
    setEditingSettingValue(setting.value);
  };

  const handleSaveSetting = async (id: number) => {
    try {
      await systemAPI.updateSetting(id, { value: editingSettingValue });
      toast.success('Setting updated');
      setEditingSettingId(null);
      setEditingSettingValue('');
      fetchData();
    } catch (error) {
      toast.error('Failed to update setting');
    }
  };

  const handleEditEnvVar = (envVar: EnvironmentVariable) => {
    setEditingEnvKey(envVar.key);
    setEditingEnvValue(envVar.is_overridden ? '' : envVar.effective_value);
  };

  const handleSaveEnvVar = async (key: string) => {
    try {
      await systemAPI.envUpdate(key, editingEnvValue);
      toast.success('Environment variable updated');
      setEditingEnvKey(null);
      setEditingEnvValue('');
      fetchData();
    } catch (error) {
      toast.error('Failed to update environment variable');
    }
  };

  const handleResetEnvVar = async (key: string) => {
    if (!confirm('Are you sure you want to remove the override and use the original environment value?')) {
      return;
    }
    try {
      await systemAPI.envUpdate(key, '');
      toast.success('Override removed');
      fetchData();
    } catch (error) {
      toast.error('Failed to reset environment variable');
    }
  };

  // Server handlers
  const handleOpenServerModal = (server?: ManagedServer) => {
    if (server) {
      setEditingServer(server);
      setServerForm({
        name: server.name,
        ip_address: server.ip_address,
        port: server.port,
        description: server.description,
        is_active: server.is_active,
        display_order: server.display_order,
        query_port: server.query_port,
      });
    } else {
      setEditingServer(null);
      setServerForm({
        name: '',
        ip_address: '',
        port: 27015,
        description: '',
        is_active: true,
        display_order: servers.length,
        query_port: null,
      });
    }
    setShowServerModal(true);
  };

  const safeInt = (value: string | number | null, fallback: number | null) => {
    if (value === null || value === undefined || value === '') return fallback;
    const num = Number(value);
    return Number.isFinite(num) ? num : fallback;
  };

  const handleSaveServer = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        ...serverForm,
        port: safeInt(serverForm.port, 27015) ?? 27015,
        display_order: safeInt(serverForm.display_order, 0) ?? 0,
        query_port: safeInt(serverForm.query_port, null),
      };

      if (editingServer) {
        await systemAPI.updateServer(editingServer.id, payload);
        toast.success('Server updated');
      } else {
        await systemAPI.createServer(payload);
        toast.success('Server created');
      }
      setShowServerModal(false);
      fetchData();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save server');
    }
  };

  const handleDeleteServer = async (server: ManagedServer) => {
    if (!confirm(`Are you sure you want to delete ${server.name}?`)) {
      return;
    }
    try {
      await systemAPI.deleteServer(server.id);
      toast.success('Server deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete server');
    }
  };

  const handleSyncServers = async () => {
    try {
      const res = await systemAPI.syncServers();
      toast.success(res.data.message);
    } catch (error) {
      toast.error('Failed to sync servers');
    }
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      general: 'General',
      counters: 'Counters & Quotas',
      sit_recording: 'Sit Recording',
      api_keys: 'API Keys',
      database: 'Database',
      cache: 'Cache',
      external: 'External Services',
      game_servers: 'Game Servers',
    };
    return labels[category] || category;
  };

  // Show loading while checking access
  if (!user || loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  // Access denied - user doesn't have permission
  if (accessDenied || !hasMinRole(70)) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white">Access Denied</h2>
          <p className="text-gray-400 mt-2">You do not have permission to access system settings.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Tabs */}
      <div className="flex gap-4 border-b border-dark-border">
        <button
          onClick={() => setActiveTab('settings')}
          className={`pb-3 px-1 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'settings'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Cog6ToothIcon className="w-5 h-5" />
          System Settings
        </button>
        <button
          onClick={() => setActiveTab('environment')}
          className={`pb-3 px-1 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'environment'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <KeyIcon className="w-5 h-5" />
          Environment Variables
        </button>
        <button
          onClick={() => setActiveTab('servers')}
          className={`pb-3 px-1 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'servers'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <ServerIcon className="w-5 h-5" />
          Server Manager
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`pb-3 px-1 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'audit'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <ClockIcon className="w-5 h-5" />
          Audit Logs
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      ) : (
        <>
          {/* System Settings Tab */}
          {activeTab === 'settings' && (
            <div className="space-y-4">
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mb-6">
                <p className="text-blue-400 text-sm">
                  💡 System settings control features and behavior across the application. 
                  Changes take effect immediately without requiring a server restart.
                </p>
              </div>

              {/* Group by category */}
              {['sit_recording', 'counters', 'general'].map((category) => {
                const categorySettings = systemSettings.filter((s) => s.category === category && s.is_active);
                if (categorySettings.length === 0) return null;

                return (
                  <div key={category} className="bg-dark-card rounded-lg border border-dark-border">
                    <div className="px-6 py-4 border-b border-dark-border">
                      <h3 className="text-lg font-semibold text-white">
                        {getCategoryLabel(category)}
                      </h3>
                    </div>
                    <div className="divide-y divide-dark-border">
                      {categorySettings.map((setting) => (
                        <div key={setting.id} className="px-6 py-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <code className="text-sm font-mono text-primary-400">
                                  {setting.key}
                                </code>
                                {setting.is_sensitive && (
                                  <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">
                                    Sensitive
                                  </span>
                                )}
                                <span className="px-2 py-0.5 text-xs bg-gray-500/20 text-gray-400 rounded">
                                  {setting.setting_type}
                                </span>
                              </div>
                              <p className="text-sm text-gray-400 mt-1">{setting.description}</p>
                              
                              {editingSettingId === setting.id ? (
                                <div className="mt-3 flex items-center gap-2">
                                  {setting.setting_type === 'boolean' ? (
                                    <select
                                      value={editingSettingValue}
                                      onChange={(e) => setEditingSettingValue(e.target.value)}
                                      className="input flex-1"
                                    >
                                      <option value="true">True</option>
                                      <option value="false">False</option>
                                    </select>
                                  ) : setting.setting_type === 'integer' ? (
                                    <input
                                      type="number"
                                      value={editingSettingValue}
                                      onChange={(e) => setEditingSettingValue(e.target.value)}
                                      className="input flex-1"
                                    />
                                  ) : setting.setting_type === 'json' ? (
                                    <textarea
                                      value={editingSettingValue}
                                      onChange={(e) => setEditingSettingValue(e.target.value)}
                                      className="input flex-1 font-mono text-sm"
                                      rows={4}
                                    />
                                  ) : (
                                    <input
                                      type={setting.is_sensitive ? 'password' : 'text'}
                                      value={editingSettingValue}
                                      onChange={(e) => setEditingSettingValue(e.target.value)}
                                      className="input flex-1"
                                    />
                                  )}
                                  <button
                                    onClick={() => handleSaveSetting(setting.id)}
                                    className="p-2 text-green-400 hover:bg-green-500/20 rounded transition-colors"
                                  >
                                    <CheckIcon className="w-5 h-5" />
                                  </button>
                                  <button
                                    onClick={() => {
                                      setEditingSettingId(null);
                                      setEditingSettingValue('');
                                    }}
                                    className="p-2 text-red-400 hover:bg-red-500/20 rounded transition-colors"
                                  >
                                    <XMarkIcon className="w-5 h-5" />
                                  </button>
                                </div>
                              ) : (
                                <div className="mt-2 flex items-center gap-2">
                                  <code className="text-sm bg-dark-hover px-3 py-1.5 rounded font-mono flex-1">
                                    {setting.display_value}
                                  </code>
                                  <button
                                    onClick={() => handleEditSetting(setting)}
                                    className="p-2 text-primary-400 hover:bg-primary-500/20 rounded transition-colors"
                                  >
                                    <PencilIcon className="w-5 h-5" />
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Environment Variables Tab */}
          {activeTab === 'environment' && (
            <div className="space-y-4">
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mb-6">
                <p className="text-blue-400 text-sm">
                  💡 Environment variables can be overridden here. Overrides take precedence over the 
                  original .env values and <strong>take effect immediately</strong> without requiring a server restart.
                  Remove an override to revert to the original value.
                </p>
              </div>

              {/* Group by category */}
              {['general', 'api_keys', 'external'].map((category) => {
                const categoryVars = envVars.filter((v) => v.category === category);
                if (categoryVars.length === 0) return null;

                return (
                  <div key={category} className="bg-dark-card rounded-lg border border-dark-border">
                    <div className="px-6 py-4 border-b border-dark-border">
                      <h3 className="text-lg font-semibold text-white">
                        {getCategoryLabel(category)}
                      </h3>
                    </div>
                    <div className="divide-y divide-dark-border">
                      {categoryVars.map((envVar) => (
                        <div key={envVar.key} className="px-6 py-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <code className="text-sm font-mono text-primary-400">
                                  {envVar.key}
                                </code>
                                {envVar.is_overridden && (
                                  <span className="px-2 py-0.5 text-xs bg-yellow-500/20 text-yellow-400 rounded">
                                    Overridden
                                  </span>
                                )}
                                {envVar.is_sensitive && (
                                  <span className="px-2 py-0.5 text-xs bg-red-500/20 text-red-400 rounded">
                                    Sensitive
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-400 mt-1">{envVar.description}</p>
                              
                              {editingEnvKey === envVar.key ? (
                                <div className="mt-3 flex items-center gap-2">
                                  <input
                                    type={envVar.is_sensitive ? 'password' : 'text'}
                                    value={editingEnvValue}
                                    onChange={(e) => setEditingEnvValue(e.target.value)}
                                    className="input flex-1"
                                    placeholder={`Enter new value for ${envVar.key}`}
                                  />
                                  <button
                                    onClick={() => handleSaveEnvVar(envVar.key)}
                                    className="p-2 text-green-400 hover:bg-green-500/20 rounded transition-colors"
                                  >
                                    <CheckIcon className="w-5 h-5" />
                                  </button>
                                  <button
                                    onClick={() => {
                                      setEditingEnvKey(null);
                                      setEditingEnvValue('');
                                    }}
                                    className="p-2 text-red-400 hover:bg-red-500/20 rounded transition-colors"
                                  >
                                    <XMarkIcon className="w-5 h-5" />
                                  </button>
                                </div>
                              ) : (
                                <div className="mt-2 flex items-center gap-2">
                                  <code className="text-sm text-gray-300 bg-dark-bg px-2 py-1 rounded">
                                    {envVar.effective_value || '(not set)'}
                                  </code>
                                </div>
                              )}
                            </div>
                            
                            {editingEnvKey !== envVar.key && (
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => handleEditEnvVar(envVar)}
                                  className="p-2 text-gray-400 hover:text-white hover:bg-dark-bg rounded transition-colors"
                                >
                                  <PencilIcon className="w-5 h-5" />
                                </button>
                                {envVar.is_overridden && (
                                  <button
                                    onClick={() => handleResetEnvVar(envVar.key)}
                                    className="p-2 text-yellow-400 hover:text-yellow-300 hover:bg-yellow-500/20 rounded transition-colors"
                                    title="Remove override"
                                  >
                                    <ArrowPathIcon className="w-5 h-5" />
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Server Manager Tab */}
          {activeTab === 'servers' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 flex-1 mr-4">
                  <p className="text-blue-400 text-sm">
                    💡 Add or remove game servers to monitor on the Server Status page. 
                    Changes are automatically synced to the server monitoring system.
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={handleSyncServers}
                    className="btn-secondary flex items-center gap-2"
                  >
                    <ArrowPathIcon className="w-5 h-5" />
                    Sync All
                  </button>
                  <button
                    onClick={() => handleOpenServerModal()}
                    className="btn-primary flex items-center gap-2"
                  >
                    <PlusIcon className="w-5 h-5" />
                    Add Server
                  </button>
                </div>
              </div>

              <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
                <table className="w-full">
                  <thead className="bg-dark-bg">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Server
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Address
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Order
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-dark-border">
                    {servers.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-12 text-center text-gray-400">
                          No servers configured. Click "Add Server" to get started.
                        </td>
                      </tr>
                    ) : (
                      servers.map((server) => (
                        <tr key={server.id} className="hover:bg-dark-bg/50 transition-colors">
                          <td className="px-6 py-4">
                            <div>
                              <p className="font-medium text-white">{server.name}</p>
                              {server.description && (
                                <p className="text-sm text-gray-400">{server.description}</p>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <code className="text-sm text-primary-400">{server.address}</code>
                          </td>
                          <td className="px-6 py-4">
                            <span
                              className={`px-2 py-1 text-xs rounded ${
                                server.is_active
                                  ? 'bg-green-500/20 text-green-400'
                                  : 'bg-red-500/20 text-red-400'
                              }`}
                            >
                              {server.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-gray-400">{server.display_order}</td>
                          <td className="px-6 py-4 text-right">
                            <button
                              onClick={() => handleOpenServerModal(server)}
                              className="p-2 text-gray-400 hover:text-white hover:bg-dark-bg rounded transition-colors"
                            >
                              <PencilIcon className="w-5 h-5" />
                            </button>
                            <button
                              onClick={() => handleDeleteServer(server)}
                              className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded transition-colors ml-2"
                            >
                              <TrashIcon className="w-5 h-5" />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Audit Logs Tab */}
          {activeTab === 'audit' && (
            <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
              <table className="w-full">
                <thead className="bg-dark-bg">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Setting
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      Old Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      New Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                      IP Address
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-border">
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-12 text-center text-gray-400">
                        No audit logs yet. Changes to settings will be recorded here.
                      </td>
                    </tr>
                  ) : (
                    auditLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-dark-bg/50 transition-colors">
                        <td className="px-6 py-4 text-sm text-gray-400">
                          {formatDateTime(log.changed_at)}
                        </td>
                        <td className="px-6 py-4">
                          <code className="text-sm text-primary-400">{log.setting_key}</code>
                        </td>
                        <td className="px-6 py-4 text-white">{log.user_username}</td>
                        <td className="px-6 py-4">
                          <code className="text-sm text-gray-400">{log.old_value || '(empty)'}</code>
                        </td>
                        <td className="px-6 py-4">
                          <code className="text-sm text-green-400">{log.new_value}</code>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-400">{log.ip_address}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Server Modal */}
      {showServerModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-card rounded-lg border border-dark-border w-full max-w-lg mx-4">
            <div className="px-6 py-4 border-b border-dark-border">
              <h2 className="text-lg font-semibold text-white">
                {editingServer ? 'Edit Server' : 'Add Server'}
              </h2>
            </div>
            <form onSubmit={handleSaveServer}>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Server Name
                  </label>
                  <input
                    type="text"
                    value={serverForm.name}
                    onChange={(e) => setServerForm({ ...serverForm, name: e.target.value })}
                    className="input w-full"
                    placeholder="e.g., Main Server"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      IP Address
                    </label>
                    <input
                      type="text"
                      value={serverForm.ip_address}
                      onChange={(e) => setServerForm({ ...serverForm, ip_address: e.target.value })}
                      className="input w-full"
                      placeholder="194.69.160.33"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Port
                    </label>
                    <input
                      type="number"
                      value={serverForm.port ?? ''}
                      onChange={(e) => setServerForm({ ...serverForm, port: safeInt(e.target.value, null) ?? null })}
                      className="input w-full"
                      placeholder="27015"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Description
                  </label>
                  <textarea
                    value={serverForm.description}
                    onChange={(e) => setServerForm({ ...serverForm, description: e.target.value })}
                    className="input w-full"
                    rows={2}
                    placeholder="Optional description"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Display Order
                    </label>
                    <input
                      type="number"
                      value={serverForm.display_order ?? ''}
                      onChange={(e) => setServerForm({ ...serverForm, display_order: safeInt(e.target.value, null) ?? null })}
                      className="input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Query Port (optional)
                    </label>
                    <input
                      type="number"
                      value={serverForm.query_port ?? ''}
                      onChange={(e) => setServerForm({ ...serverForm, query_port: safeInt(e.target.value, null) })}
                      className="input w-full"
                      placeholder="Same as port"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={serverForm.is_active}
                    onChange={(e) => setServerForm({ ...serverForm, is_active: e.target.checked })}
                    className="rounded border-dark-border bg-dark-bg text-primary-500 focus:ring-primary-500"
                  />
                  <label htmlFor="is_active" className="text-sm text-gray-300">
                    Active (server will be monitored)
                  </label>
                </div>
              </div>
              <div className="px-6 py-4 border-t border-dark-border flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowServerModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingServer ? 'Save Changes' : 'Add Server'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
