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
  VideoCameraIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { sitAPI } from '@/lib/api';

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

interface UserSitPreferences {
  recording_enabled: boolean;
  ocr_enabled: boolean;
  auto_start_recording: boolean;
  auto_stop_recording: boolean;
  ocr_scan_interval_ms: number;
  ocr_popup_region_enabled: boolean;
  ocr_chat_region_enabled: boolean;
  video_quality: 'low' | 'medium' | 'high';
  max_recording_minutes: number;
  show_recording_preview: boolean;
  confirm_before_start: boolean;
}

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(true);
  const [socialStatus, setSocialStatus] = useState<SocialStatus | null>(null);
  const [timezones, setTimezones] = useState<Timezone[]>([]);
  const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'social' | 'sit-recording'>('profile');
  
  // Profile form
  const [profileForm, setProfileForm] = useState({
    display_name: '',
    email: '',
    timezone: '',
    use_24_hour_time: true,
  });
  const [savingProfile, setSavingProfile] = useState(false);

  // Password form
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    new_password_confirm: '',
  });
  const [savingPassword, setSavingPassword] = useState(false);

  // Sit recording preferences
  const [sitPreferences, setSitPreferences] = useState<UserSitPreferences | null>(null);
  const [savingSitPrefs, setSavingSitPrefs] = useState(false);
  const [sitRecordingSystemEnabled, setSitRecordingSystemEnabled] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (user) {
      setProfileForm({
        display_name: user.display_name || '',
        email: user.email || '',
        timezone: user.timezone || 'UTC',
        use_24_hour_time: user.use_24_hour_time ?? true,
      });
    }
  }, [user]);

  const fetchData = async () => {
    try {
      const [socialRes, tzRes, sitEnabledRes, sitPrefsRes] = await Promise.all([
        authAPI.socialStatus(),
        authAPI.timezones(),
        sitAPI.isEnabled().catch(() => ({ data: { system_enabled: false, ocr_system_enabled: false } })),
        sitAPI.getPreferences().catch(() => ({ data: null })),
      ]);
      setSocialStatus(socialRes.data);
      // Ensure we have an array, fallback to a safe default
      const tzData = Array.isArray(tzRes.data) ? tzRes.data : [];
      setTimezones(tzData);
      setSitRecordingSystemEnabled(sitEnabledRes.data?.system_enabled || false);
      setSitPreferences(sitPrefsRes.data);
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

  const handleSaveSitPreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sitPreferences) return;
    setSavingSitPrefs(true);
    try {
      await sitAPI.updatePreferences(sitPreferences);
      toast.success('Sit recording preferences updated');
    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Failed to update preferences');
    } finally {
      setSavingSitPrefs(false);
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
    <div className="space-y-6\">
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
        {/* Only show Sit Recording tab if feature is enabled system-wide */}
        {sitRecordingSystemEnabled && (
          <button
            onClick={() => setActiveTab('sit-recording')}
            className={`pb-3 px-1 font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'sit-recording'
                ? 'text-primary-400 border-b-2 border-primary-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <VideoCameraIcon className="w-5 h-5" />
            Sit Recording
          </button>
        )}
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
            <div>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profileForm.use_24_hour_time}
                  onChange={(e) =>
                    setProfileForm({ ...profileForm, use_24_hour_time: e.target.checked })
                  }
                  className="w-4 h-4 text-primary-600 bg-dark-bg border-gray-600 rounded focus:ring-primary-500 focus:ring-2"
                />
                <span className="text-sm font-medium text-gray-300">
                  Use 24-hour time format
                </span>
              </label>
              <p className="text-sm text-gray-500 mt-1 ml-7">
                Display times as {profileForm.use_24_hour_time ? '14:30' : '2:30 PM'}
              </p>
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
                  href={`${API_URL}/api/oauth/login/steam/`}
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
                  href={`${API_URL}/api/oauth/login/discord/`}
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

      {/* Sit Recording Tab */}
      {activeTab === 'sit-recording' && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-lg font-semibold text-white mb-6">
            Sit Recording Preferences
          </h2>

          {!sitRecordingSystemEnabled ? (
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
              <p className="text-yellow-400 text-sm">
                ⚠️ Sit recording is currently disabled system-wide. Contact an administrator to enable this feature.
              </p>
            </div>
          ) : !sitPreferences ? (
            <div className="animate-pulse space-y-4">
              <div className="h-12 bg-dark-bg rounded"></div>
              <div className="h-12 bg-dark-bg rounded"></div>
              <div className="h-12 bg-dark-bg rounded"></div>
            </div>
          ) : (
            <form onSubmit={handleSaveSitPreferences} className="space-y-6 max-w-2xl">
              {/* Master Toggle */}
              <div className="pb-4 border-b border-dark-border">
                <label className="flex items-center justify-between cursor-pointer">
                  <div>
                    <span className="text-base font-medium text-white">
                      Enable Sit Recording Feature
                    </span>
                    <p className="text-sm text-gray-400 mt-1">
                      Master toggle for the entire sit recording system
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={sitPreferences.recording_enabled}
                    onChange={(e) =>
                      setSitPreferences({ ...sitPreferences, recording_enabled: e.target.checked })
                    }
                    className="w-5 h-5 text-primary-600 bg-dark-bg border-gray-600 rounded focus:ring-primary-500 focus:ring-2"
                  />
                </label>
              </div>

              {/* OCR Detection Section */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                  Auto-Detection (OCR)
                </h3>
                
                <label className="flex items-center justify-between cursor-pointer">
                  <div>
                    <span className="text-sm font-medium text-gray-300">
                      Enable OCR Auto-Detection
                    </span>
                    <p className="text-sm text-gray-500 mt-1">
                      Automatically detect sit events by scanning your screen
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={sitPreferences.ocr_enabled}
                    onChange={(e) =>
                      setSitPreferences({ ...sitPreferences, ocr_enabled: e.target.checked })
                    }
                    disabled={!sitPreferences.recording_enabled}
                    className="w-4 h-4 text-primary-600 bg-dark-bg border-gray-600 rounded focus:ring-primary-500 focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </label>

                {sitPreferences.ocr_enabled && (
                  <div className="ml-6 space-y-3 pl-4 border-l-2 border-gray-700">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={sitPreferences.ocr_popup_region_enabled}
                        onChange={(e) =>
                          setSitPreferences({ ...sitPreferences, ocr_popup_region_enabled: e.target.checked })
                        }
                        disabled={!sitPreferences.recording_enabled}
                        className="w-4 h-4 text-primary-600 bg-dark-bg border-gray-600 rounded focus:ring-primary-500 focus:ring-2 disabled:opacity-50"
                      />
                      <span className="text-sm text-gray-300">Scan report popup area</span>
                    </label>

                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={sitPreferences.ocr_chat_region_enabled}
                        onChange={(e) =>
                          setSitPreferences({ ...sitPreferences, ocr_chat_region_enabled: e.target.checked })
                        }
                        disabled={!sitPreferences.recording_enabled}
                        className="w-4 h-4 text-primary-600 bg-dark-bg border-gray-600 rounded focus:ring-primary-500 focus:ring-2 disabled:opacity-50"
                      />
                      <span className="text-sm text-gray-300">Scan chat area</span>
                    </label>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        OCR Scan Interval: {sitPreferences.ocr_scan_interval_ms}ms
                      </label>
                      <input
                        type="range"
                        min="500"
                        max="5000"
                        step="500"
                        value={sitPreferences.ocr_scan_interval_ms}
                        onChange={(e) =>
                          setSitPreferences({ ...sitPreferences, ocr_scan_interval_ms: parseInt(e.target.value) })
                        }
                        disabled={!sitPreferences.recording_enabled}
                        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer disabled:opacity-50"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Lower = more frequent scans (higher CPU usage)
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Recording Section */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                  Screen Recording
                </h3>

                <label className="flex items-center justify-between cursor-pointer">
                  <div>
                    <span className="text-sm font-medium text-gray-300">
                      Auto-Start Recording
                    </span>
                    <p className="text-sm text-gray-500 mt-1">
                      Automatically start recording when a sit is detected
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={sitPreferences.auto_start_recording}
                    onChange={(e) =>
                      setSitPreferences({ ...sitPreferences, auto_start_recording: e.target.checked })
                    }
                    disabled={!sitPreferences.recording_enabled || !sitPreferences.ocr_enabled}
                    className="w-4 h-4 text-primary-600 bg-dark-bg border-gray-600 rounded focus:ring-primary-500 focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </label>

                <label className="flex items-center justify-between cursor-pointer">
                  <div>
                    <span className="text-sm font-medium text-gray-300">
                      Auto-Stop Recording
                    </span>
                    <p className="text-sm text-gray-500 mt-1">
                      Automatically stop recording when sit is closed
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={sitPreferences.auto_stop_recording}
                    onChange={(e) =>
                      setSitPreferences({ ...sitPreferences, auto_stop_recording: e.target.checked })
                    }
                    disabled={!sitPreferences.recording_enabled || !sitPreferences.ocr_enabled}
                    className="w-4 h-4 text-primary-600 bg-dark-bg border-gray-600 rounded focus:ring-primary-500 focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </label>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Video Quality
                  </label>
                  <select
                    value={sitPreferences.video_quality}
                    onChange={(e) =>
                      setSitPreferences({ ...sitPreferences, video_quality: e.target.value as 'low' | 'medium' | 'high' })
                    }
                    disabled={!sitPreferences.recording_enabled}
                    className="input w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <option value="low">Low (1 Mbps) - Smaller files</option>
                    <option value="medium">Medium (2.5 Mbps) - Balanced</option>
                    <option value="high">High (5 Mbps) - Best quality</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Higher quality = larger file sizes
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Max Recording Duration: {sitPreferences.max_recording_minutes} minutes
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="120"
                    step="5"
                    value={sitPreferences.max_recording_minutes}
                    onChange={(e) =>
                      setSitPreferences({ ...sitPreferences, max_recording_minutes: parseInt(e.target.value) })
                    }
                    disabled={!sitPreferences.recording_enabled}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer disabled:opacity-50"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Recording will automatically stop after this duration
                  </p>
                </div>
              </div>

              {/* UI Settings */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
                  Interface Options
                </h3>

                <label className="flex items-center justify-between cursor-pointer">
                  <div>
                    <span className="text-sm font-medium text-gray-300">
                      Show Recording Preview
                    </span>
                    <p className="text-sm text-gray-500 mt-1">
                      Display small preview of recording in the UI
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={sitPreferences.show_recording_preview}
                    onChange={(e) =>
                      setSitPreferences({ ...sitPreferences, show_recording_preview: e.target.checked })
                    }
                    disabled={!sitPreferences.recording_enabled}
                    className="w-4 h-4 text-primary-600 bg-dark-bg border-gray-600 rounded focus:ring-primary-500 focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </label>

                <label className="flex items-center justify-between cursor-pointer">
                  <div>
                    <span className="text-sm font-medium text-gray-300">
                      Confirm Before Auto-Start
                    </span>
                    <p className="text-sm text-gray-500 mt-1">
                      Show confirmation popup before automatically starting recording
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={sitPreferences.confirm_before_start}
                    onChange={(e) =>
                      setSitPreferences({ ...sitPreferences, confirm_before_start: e.target.checked })
                    }
                    disabled={!sitPreferences.recording_enabled}
                    className="w-4 h-4 text-primary-600 bg-dark-bg border-gray-600 rounded focus:ring-primary-500 focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </label>
              </div>

              {/* Info Box */}
              <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
                <p className="text-blue-400 text-sm mb-2">
                  💡 <strong>Use Case:</strong> Want auto-detection without recording?
                </p>
                <p className="text-blue-300 text-sm">
                  Enable <strong>OCR Auto-Detection</strong> but disable <strong>Auto-Start Recording</strong>. 
                  You'll get notifications when sits are detected, but won't start recording automatically. 
                  You can then manually start recording if needed.
                </p>
              </div>

              <div className="pt-4">
                <button
                  type="submit"
                  disabled={savingSitPrefs || !sitPreferences.recording_enabled}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {savingSitPrefs ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
