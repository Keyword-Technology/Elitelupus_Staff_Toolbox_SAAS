'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { authAPI } from '@/lib/api';
import {
  UserCircleIcon,
  KeyIcon,
  LinkIcon,
  GlobeAltIcon,
  BellIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const API_URL = typeof window !== 'undefined' 
  ? (process.env.NEXT_PUBLIC_API_URL || '')
  : '';

interface SocialStatus {
  steam_connected: boolean;
  steam_id: string | null;
  steam_name: string | null;
  discord_connected: boolean;
  discord_id: string | null;
  discord_username: string | null;
}

interface Timezone {
  value: string;
  label: string;
}

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [socialStatus, setSocialStatus] = useState<SocialStatus | null>(null);
  const [timezones, setTimezones] = useState<Timezone[]>([]);
  const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'social'>('profile');
  
  // Profile form
  const [profileForm, setProfileForm] = useState({
    display_name: '',
    email: '',
    timezone: '',
  });
  const [savingProfile, setSavingProfile] = useState(false);

  // Password form
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  });
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (user) {
      setProfileForm({
        display_name: user.display_name || '',
        email: user.email || '',
        timezone: user.timezone || 'UTC',
      });
    }
  }, [user]);

  const fetchData = async () => {
    try {
      const [socialRes, tzRes] = await Promise.all([
        authAPI.socialStatus(),
        authAPI.timezones(),
      ]);
      setSocialStatus(socialRes.data);
      // Ensure we have an array, fallback to a safe default
      const tzData = Array.isArray(tzRes.data) ? tzRes.data : [];
      setTimezones(tzData);
    } catch (error) {
      toast.error('Failed to load settings');
      console.error('Settings fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await authAPI.updateProfile(profileForm);
      await refreshUser();
      toast.success('Profile updated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update profile');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (passwordForm.new_password !== passwordForm.new_password_confirm) {
      toast.error('Passwords do not match');
      return;
    }
    setSavingPassword(true);
    try {
      await authAPI.changePassword(passwordForm);
      toast.success('Password changed successfully');
      setPasswordForm({
        old_password: '',
        new_password: '',
        new_password_confirm: '',
      });
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to change password');
    } finally {
      setSavingPassword(false);
    }
  };

  const handleUnlinkSocial = async (provider: 'steam' | 'discord') => {
    if (!confirm(`Are you sure you want to unlink your ${provider} account?`)) {
      return;
    }
    try {
      await authAPI.unlinkSocial(provider);
      toast.success(`${provider} account unlinked`);
      fetchData();
    } catch (error) {
      toast.error(`Failed to unlink ${provider}`);
    }
  };

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
      <div>
        <h1 className="text-2xl font-bold text-white">Profile Settings</h1>
        <p className="text-gray-400 mt-1">
          Manage your account preferences and connected services
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-dark-border">
        <button
          onClick={() => setActiveTab('profile')}
          className={`pb-3 px-1 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'profile'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <UserCircleIcon className="w-5 h-5" />
          Profile
        </button>
        <button
          onClick={() => setActiveTab('password')}
          className={`pb-3 px-1 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'password'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <KeyIcon className="w-5 h-5" />
          Password
        </button>
        <button
          onClick={() => setActiveTab('social')}
          className={`pb-3 px-1 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'social'
              ? 'text-primary-400 border-b-2 border-primary-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <LinkIcon className="w-5 h-5" />
          Connected Accounts
        </button>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-6">
            Profile Information
          </h2>
          <form onSubmit={handleSaveProfile} className="space-y-4 max-w-lg">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <input
                type="text"
                value={user?.username || ''}
                disabled
                className="input w-full bg-dark-bg cursor-not-allowed"
              />
              <p className="text-sm text-gray-500 mt-1">
                Username cannot be changed
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Display Name
              </label>
              <input
                type="text"
                value={profileForm.display_name}
                onChange={(e) =>
                  setProfileForm({ ...profileForm, display_name: e.target.value })
                }
                className="input w-full"
                placeholder="Enter display name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Email
              </label>
              <input
                type="email"
                value={profileForm.email}
                onChange={(e) =>
                  setProfileForm({ ...profileForm, email: e.target.value })
                }
                className="input w-full"
                placeholder="Enter email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                <GlobeAltIcon className="w-4 h-4 inline mr-1" />
                Timezone
              </label>
              <select
                value={profileForm.timezone}
                onChange={(e) =>
                  setProfileForm({ ...profileForm, timezone: e.target.value })
                }
                className="input w-full"
              >
                {timezones.map((tz) => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="pt-4">
              <button
                type="submit"
                disabled={savingProfile}
                className="btn-primary"
              >
                {savingProfile ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Password Tab */}
      {activeTab === 'password' && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-6">
            Change Password
          </h2>
          <form onSubmit={handleChangePassword} className="space-y-4 max-w-lg">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Current Password
              </label>
              <input
                type="password"
                value={passwordForm.old_password}
                onChange={(e) =>
                  setPasswordForm({ ...passwordForm, old_password: e.target.value })
                }
                className="input w-full"
                placeholder="Enter current password"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                New Password
              </label>
              <input
                type="password"
                value={passwordForm.new_password}
                onChange={(e) =>
                  setPasswordForm({ ...passwordForm, new_password: e.target.value })
                }
                className="input w-full"
                placeholder="Enter new password"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Confirm New Password
              </label>
              <input
                type="password"
                value={passwordForm.new_password_confirm}
                onChange={(e) =>
                  setPasswordForm({
                    ...passwordForm,
                    new_password_confirm: e.target.value,
                  })
                }
                className="input w-full"
                placeholder="Confirm new password"
              />
            </div>
            <div className="pt-4">
              <button
                type="submit"
                disabled={savingPassword}
                className="btn-primary"
              >
                {savingPassword ? 'Changing...' : 'Change Password'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Social Tab */}
      {activeTab === 'social' && (
        <div className="space-y-4">
          {/* Steam */}
          <div className="bg-dark-card rounded-lg border border-dark-border p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#171a21] rounded-lg flex items-center justify-center">
                  <svg
                    className="w-8 h-8"
                    viewBox="0 0 24 24"
                    fill="#66c0f4"
                  >
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.08 3.16 9.42 7.62 11.18l3.98-5.72c-1.35-.08-2.56-.7-3.4-1.62l-2.42 1.62c-.23.15-.52.09-.67-.14-.15-.23-.09-.52.14-.67l2.42-1.62c-.35-.82-.55-1.72-.55-2.67 0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-.93 0-1.82-.18-2.63-.51l-4.02 5.78C8.23 23.89 10.05 24 12 24c6.63 0 12-5.37 12-12S18.63 0 12 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Steam</h3>
                  {socialStatus?.steam_connected ? (
                    <p className="text-gray-400 text-sm">
                      Connected as {socialStatus.steam_name}
                    </p>
                  ) : (
                    <p className="text-gray-500 text-sm">Not connected</p>
                  )}
                </div>
              </div>
              {socialStatus?.steam_connected ? (
                <button
                  onClick={() => handleUnlinkSocial('steam')}
                  className="btn-secondary text-red-400 hover:text-red-300"
                >
                  Unlink
                </button>
              ) : (
                <a
                  href={`${API_URL}/api/auth/login/steam/`}
                  className="btn-primary"
                >
                  Connect Steam
                </a>
              )}
            </div>
          </div>

          {/* Discord */}
          <div className="bg-dark-card rounded-lg border border-dark-border p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#5865F2] rounded-lg flex items-center justify-center">
                  <svg
                    className="w-8 h-8"
                    viewBox="0 0 24 24"
                    fill="white"
                  >
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-semibold">Discord</h3>
                  {socialStatus?.discord_connected ? (
                    <p className="text-gray-400 text-sm">
                      Connected as {socialStatus.discord_username}
                    </p>
                  ) : (
                    <p className="text-gray-500 text-sm">Not connected</p>
                  )}
                </div>
              </div>
              {socialStatus?.discord_connected ? (
                <button
                  onClick={() => handleUnlinkSocial('discord')}
                  className="btn-secondary text-red-400 hover:text-red-300"
                >
                  Unlink
                </button>
              ) : (
                <a
                  href={`${API_URL}/api/auth/login/discord/`}
                  className="btn-primary"
                >
                  Connect Discord
                </a>
              )}
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
            <p className="text-blue-400 text-sm">
              💡 Connecting your Steam account allows automatic verification of
              your staff status on the game servers. Connecting Discord enables
              notifications and role sync.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
