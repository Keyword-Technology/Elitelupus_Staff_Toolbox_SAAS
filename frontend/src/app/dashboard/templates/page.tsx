'use client';

import { useState, useEffect } from 'react';
import { templateAPI } from '@/lib/api';
import {
  DocumentTextIcon,
  MagnifyingGlassIcon,
  ClipboardDocumentIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import EnhancedSteamProfile from '@/components/templates/EnhancedSteamProfile';

interface RefundTemplate {
  id: number;
  name: string;
  content: string;
  fields: Record<string, string>;
  created_at: string;
  updated_at: string;
}

interface SteamProfileData {
  steam_id: string;
  steam_id_64: string;
  profile: {
    name: string;
    profile_url: string;
    avatar_url: string;
    profile_state: string;
    real_name?: string;
    location?: string;
    is_private: boolean;
    is_limited: boolean;
    level?: number;
    account_created?: string;
  };
  bans: {
    vac_bans: number;
    game_bans: number;
    days_since_last_ban?: number;
    community_banned: boolean;
    trade_ban: string;
  };
  search_stats: {
    total_searches: number;
    first_searched: string;
    last_searched: string;
    last_searched_by?: string;
  };
  changes: Record<string, { old: any; new: any }>;
  related_templates: any[];
  search_history: any[];
}

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<RefundTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<RefundTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [steamInput, setSteamInput] = useState('');
  const [steamProfile, setSteamProfile] = useState<SteamProfileData | null>(null);
  const [lookingUp, setLookingUp] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTemplate, setNewTemplate] = useState({ name: '', content: '' });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await templateAPI.refunds();
      setTemplates(res.data.results || res.data);
    } catch (error) {
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleSteamLookup = async () => {
    if (!steamInput.trim()) return;
    setLookingUp(true);
    try {
      const res = await templateAPI.steamLookup(steamInput);
      setSteamProfile(res.data);
      toast.success('Steam profile found');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Steam profile not found');
      setSteamProfile(null);
    } finally {
      setLookingUp(false);
    }
  };

  const handleCopyTemplate = (content: string) => {
    let finalContent = content;
    
    // Replace placeholders with Steam profile data if available
    if (steamProfile) {
      finalContent = finalContent
        .replace(/\{steam_id\}/g, steamProfile.steam_id)
        .replace(/\{steam_id64\}/g, steamProfile.steam_id_64)
        .replace(/\{steam_name\}/g, steamProfile.profile.name)
        .replace(/\{profile_url\}/g, steamProfile.profile.profile_url);
    }
    
    navigator.clipboard.writeText(finalContent);
    toast.success('Template copied to clipboard');
  };

  const handleCreateTemplate = async () => {
    if (!newTemplate.name || !newTemplate.content) {
      toast.error('Please fill in all fields');
      return;
    }
    try {
      await templateAPI.createRefund(newTemplate);
      toast.success('Template created');
      setShowCreateModal(false);
      setNewTemplate({ name: '', content: '' });
      fetchTemplates();
    } catch (error) {
      toast.error('Failed to create template');
    }
  };

  const handleDeleteTemplate = async (id: number) => {
    if (!confirm('Are you sure you want to delete this template?')) return;
    try {
      await templateAPI.deleteRefund(id);
      toast.success('Template deleted');
      if (selectedTemplate?.id === id) setSelectedTemplate(null);
      fetchTemplates();
    } catch (error) {
      toast.error('Failed to delete template');
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Steam Lookup & Actions</h1>
          <p className="text-gray-400 mt-1">
            Look up Steam profiles, check bans, and manage refund templates
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <PlusIcon className="w-4 h-4" />
          New Refund Template
        </button>
      </div>

      {/* Steam Lookup */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <MagnifyingGlassIcon className="w-5 h-5 text-primary-400" />
          Steam Profile Lookup
        </h2>
        <div className="flex gap-4">
          <input
            type="text"
            value={steamInput}
            onChange={(e) => setSteamInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSteamLookup()}
            placeholder="Enter Steam ID, Steam64, or Profile URL..."
            className="input flex-1"
          />
          <button
            onClick={handleSteamLookup}
            disabled={lookingUp}
            className="btn-primary"
          >
            {lookingUp ? 'Looking up...' : 'Lookup'}
          </button>
          {steamProfile && (
            <button
              onClick={() => setSteamProfile(null)}
              className="btn-secondary"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Enhanced Profile Display - Inline */}
      {steamProfile && (
        <EnhancedSteamProfile profile={steamProfile} />
      )}

      {/* Templates Section - Only show if no profile or collapsed */}
      {!steamProfile && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Template List */}
          <div className="lg:col-span-1 space-y-3">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <DocumentTextIcon className="w-5 h-5 text-primary-400" />
              Templates
            </h2>
            {templates.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No templates yet</p>
            ) : (
              templates.map((template) => (
                <div
                  key={template.id}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedTemplate?.id === template.id
                      ? 'bg-primary-500/20 border-primary-500'
                      : 'bg-dark-card border-dark-border hover:border-gray-600'
                  }`}
                  onClick={() => setSelectedTemplate(template)}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-white font-medium">{template.name}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteTemplate(template.id);
                      }}
                      className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                    >
                      <TrashIcon className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-gray-500 text-sm mt-1 line-clamp-2">
                    {template.content.substring(0, 100)}...
                  </p>
                </div>
              ))
            )}
          </div>

          {/* Template Preview */}
          <div className="lg:col-span-2">
            <div className="bg-dark-card rounded-lg border border-dark-border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">
                  {selectedTemplate ? selectedTemplate.name : 'Select a Template'}
                </h2>
                {selectedTemplate && (
                  <button
                    onClick={() => handleCopyTemplate(selectedTemplate.content)}
                    className="btn-secondary flex items-center gap-2"
                  >
                    <ClipboardDocumentIcon className="w-4 h-4" />
                    Copy
                  </button>
                )}
              </div>
              {selectedTemplate ? (
                <div className="bg-dark-bg rounded-lg p-4">
                  <pre className="text-gray-300 whitespace-pre-wrap font-mono text-sm">
                    {selectedTemplate.content}
                  </pre>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  Select a template from the list to preview
                </div>
              )}
            </div>
          </div>
        </div>
      )}
                    className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-gray-500 text-sm mt-1 line-clamp-2">
                  {template.content.substring(0, 100)}...
                </p>
              </div>
            ))
          )}
        </div>

        {/* Template Preview */}
        <div className="lg:col-span-2">
          <div className="bg-dark-card rounded-lg border border-dark-border p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">
                {selectedTemplate ? selectedTemplate.name : 'Select a Template'}
              </h2>
              {selectedTemplate && (
                <button
                  onClick={() => handleCopyTemplate(selectedTemplate.content)}
                  className="btn-secondary flex items-center gap-2"
                >
                  <ClipboardDocumentIcon className="w-4 h-4" />
                  Copy
                </button>
              )}
            </div>
            {selectedTemplate ? (
              <div className="bg-dark-bg rounded-lg p-4">
                <pre className="text-gray-300 whitespace-pre-wrap font-mono text-sm">
                  {selectedTemplate.content}
                </pre>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                Select a template from the list to preview
              </div>
            )}
            {steamProfile && selectedTemplate && (
              <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                <p className="text-blue-400 text-sm">
                  💡 Steam profile data will be automatically inserted when copying.
                  Use placeholders: {'{steam_id}'}, {'{steam_id64}'}, {'{steam_name}'}, {'{profile_url}'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-card rounded-lg border border-dark-border p-6 w-full max-w-lg mx-4">
            <h2 className="text-xl font-bold text-white mb-4">Create Template</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Template Name
                </label>
                <input
                  type="text"
                  value={newTemplate.name}
                  onChange={(e) =>
                    setNewTemplate({ ...newTemplate, name: e.target.value })
                  }
                  className="input w-full"
                  placeholder="e.g., Standard Refund"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Template Content
                </label>
                <textarea
                  value={newTemplate.content}
                  onChange={(e) =>
                    setNewTemplate({ ...newTemplate, content: e.target.value })
                  }
                  className="input w-full h-48"
                  placeholder="Enter template content... Use {steam_id}, {steam_name}, etc. for placeholders"
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button onClick={handleCreateTemplate} className="btn-primary">
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
