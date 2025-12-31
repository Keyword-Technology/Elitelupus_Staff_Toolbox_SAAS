'use client';

import { useState, useEffect } from 'react';
import { templateAPI, serverAPI } from '@/lib/api';
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
  const [showWizardModal, setShowWizardModal] = useState(false);
  const [wizardStep, setWizardStep] = useState(1);
  const [selectedTemplateType, setSelectedTemplateType] = useState('');
  const [templateSearchTerm, setTemplateSearchTerm] = useState('');
  const [templateFilter, setTemplateFilter] = useState('all');
  const [wizardData, setWizardData] = useState<any>({});
  const [servers, setServers] = useState<any[]>([]);
  const [pastIGNs, setPastIGNs] = useState<string[]>([]);

  useEffect(() => {
    fetchTemplates();
    fetchServers();
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

  const fetchServers = async () => {
    try {
      const response = await serverAPI.list();
      setServers(response.data || []);
    } catch (error) {
      console.error('Failed to fetch servers:', error);
    }
  };

  const handleSteamLookup = async () => {
    if (!steamInput.trim()) return;
    setLookingUp(true);
    try {
      const res = await templateAPI.steamLookup(steamInput);
      setSteamProfile(res.data);
      
      // Extract past IGNs from search history and changes
      const igns = new Set<string>();
      if (res.data.profile?.name) {
        igns.add(res.data.profile.name);
      }
      if (res.data.search_history) {
        res.data.search_history.forEach((h: any) => {
          if (h.persona_name) igns.add(h.persona_name);
        });
      }
      if (res.data.changes?.ign_history) {
        res.data.changes.ign_history.forEach((ign: string) => igns.add(ign));
      }
      setPastIGNs(Array.from(igns));
      
      toast.success('Steam profile found');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Steam profile not found');
      setSteamProfile(null);
      setPastIGNs([]);
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

  const handleStartWizard = () => {
    setWizardStep(1);
    setSelectedTemplateType('');
    setWizardData({});
    setShowWizardModal(true);
  };

  const handleWizardNext = () => {
    if (wizardStep === 1 && !selectedTemplateType) {
      toast.error('Please select a template type');
      return;
    }
    setWizardStep(wizardStep + 1);
  };

  const handleWizardSubmit = async () => {
    try {
      // Pre-fill with Steam profile data if available
      const data = {
        ...wizardData,
        steam_id: steamProfile?.steam_id || wizardData.steam_id,
        steam_id_64: steamProfile?.steam_id_64 || wizardData.steam_id_64,
        player_ign: wizardData.player_ign || steamProfile?.profile.name,
      };

      // If IGN was manually entered and differs from current profile name, track it
      if (wizardData.player_ign && 
          steamProfile?.profile?.name && 
          wizardData.player_ign !== steamProfile.profile.name &&
          !pastIGNs.includes(wizardData.player_ign)) {
        setPastIGNs([wizardData.player_ign, ...pastIGNs]);
        // TODO: Send to backend to persist IGN change
        // await templateAPI.updateSteamProfile(steamProfile.steam_id_64, { ign_history: [wizardData.player_ign, ...pastIGNs] });
      }

      // Auto-select server if only one exists
      if (servers.length === 1 && !data.server) {
        data.server = servers[0].name;
      }

      // Call appropriate API based on template type
      switch (selectedTemplateType) {
        case 'refund':
          await templateAPI.createRefund(data);
          break;
        // Add other template types when APIs are ready
        default:
          toast.error('Template type not yet implemented');
          return;
      }

      toast.success('Template submitted successfully');
      setShowWizardModal(false);
      setWizardData({});
      fetchTemplates();
    } catch (error) {
      toast.error('Failed to submit template');
    }
  };

  // Filter templates
  const filteredTemplates = templates.filter((template) => {
    const matchesSearch = template.name.toLowerCase().includes(templateSearchTerm.toLowerCase()) ||
                          template.content.toLowerCase().includes(templateSearchTerm.toLowerCase());
    const matchesFilter = templateFilter === 'all' || template.name.toLowerCase().includes(templateFilter);
    return matchesSearch && matchesFilter;
  });

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
        <h1 className="text-2xl font-bold text-white">Steam Lookup & Actions</h1>
        <p className="text-gray-400 mt-1">
          Look up Steam profiles, check bans, and manage templates
        </p>
      </div>

      {/* Steam Lookup Bar */}
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

      {/* 2-Column Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Lookup Details */}
        <div className="space-y-6">
          <div className="bg-dark-card rounded-lg border border-dark-border p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <DocumentTextIcon className="w-5 h-5 text-primary-400" />
              Lookup
            </h2>
            {steamProfile ? (
              <EnhancedSteamProfile profile={steamProfile} />
            ) : (
              <div className="text-center py-12 text-gray-500">
                <MagnifyingGlassIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Enter a Steam ID above to view profile details</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Column - Templates */}
        <div className="space-y-6">
          <div className="bg-dark-card rounded-lg border border-dark-border p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <DocumentTextIcon className="w-5 h-5 text-primary-400" />
                Templates
              </h2>
              <button
                onClick={handleStartWizard}
                className="btn-primary flex items-center gap-2 text-sm"
              >
                <PlusIcon className="w-4 h-4" />
                Create New
              </button>
            </div>

            {/* Search Bar */}
            <div className="relative mb-4">
              <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                value={templateSearchTerm}
                onChange={(e) => setTemplateSearchTerm(e.target.value)}
                placeholder="Search templates..."
                className="input pl-10 w-full"
              />
            </div>

            {/* Filter Buttons */}
            <div className="flex flex-wrap gap-2 mb-4">
              {['all', 'refund', 'ban', 'report', 'application'].map((filter) => (
                <button
                  key={filter}
                  onClick={() => setTemplateFilter(filter)}
                  className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                    templateFilter === filter
                      ? 'bg-primary-600 text-white'
                      : 'bg-dark-bg text-gray-400 hover:bg-gray-700'
                  }`}
                >
                  {filter.charAt(0).toUpperCase() + filter.slice(1)}
                  <span className="ml-1 text-xs opacity-75">
                    ({filteredTemplates.filter(t => 
                      filter === 'all' ? true : t.name.toLowerCase().includes(filter)
                    ).length})
                  </span>
                </button>
              ))}
            </div>
            
            {/* Template List */}
            <div className="space-y-3 mb-6">
              {filteredTemplates.length === 0 ? (
                <p className="text-gray-500 text-center py-8">
                  {templateSearchTerm || templateFilter !== 'all' 
                    ? 'No templates match your search criteria.'
                    : 'No templates yet'}
                </p>
              ) : (
                filteredTemplates.map((template) => (
                  <div
                    key={template.id}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      selectedTemplate?.id === template.id
                        ? 'bg-primary-500/20 border-primary-500'
                        : 'bg-dark-bg border-dark-border hover:border-gray-600'
                    }`}
                    onClick={() => setSelectedTemplate(template)}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-white font-medium">{template.name}</span>
                      <div className="flex gap-2">
                        {selectedTemplate?.id === template.id && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCopyTemplate(template.content);
                            }}
                            className="p-1 text-gray-400 hover:text-blue-400 transition-colors"
                          >
                            <ClipboardDocumentIcon className="w-4 h-4" />
                          </button>
                        )}
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
                    </div>
                    <p className="text-gray-500 text-sm mt-1 line-clamp-2">
                      {template.content.substring(0, 100)}...
                    </p>
                  </div>
                ))
              )}
            </div>

            {/* Template Preview */}
            {selectedTemplate && (
              <div className="border-t border-dark-border pt-4">
                <h3 className="text-white font-medium mb-3">Preview</h3>
                <div className="bg-dark-bg rounded-lg p-4">
                  <pre className="text-gray-300 whitespace-pre-wrap font-mono text-sm">
                    {selectedTemplate.content}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Wizard Modal */}
      {showWizardModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-card rounded-lg border border-dark-border p-6 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            {/* Step 1: Template Type Selection */}
            {wizardStep === 1 && (
              <>
                <h2 className="text-xl font-bold text-white mb-4">Select Template Type</h2>
                <p className="text-gray-400 mb-6">Choose the type of template you want to fill out</p>
                
                <div className="grid grid-cols-2 gap-4 mb-6">
                  {[
                    { type: 'refund', label: 'Refund Template', icon: '💰', desc: 'Process item refunds' },
                    { type: 'ban_extension', label: 'Ban Extension', icon: '🔨', desc: 'Extend player bans' },
                    { type: 'player_report', label: 'Player Report', icon: '📝', desc: 'Report rule violations' },
                    { type: 'staff_application', label: 'Staff Application', icon: '👮', desc: 'Review staff apps' },
                  ].map((option) => (
                    <button
                      key={option.type}
                      onClick={() => setSelectedTemplateType(option.type)}
                      className={`p-4 rounded-lg border-2 transition-all text-left ${
                        selectedTemplateType === option.type
                          ? 'bg-primary-500/20 border-primary-500'
                          : 'bg-dark-bg border-dark-border hover:border-gray-600'
                      }`}
                    >
                      <div className="text-3xl mb-2">{option.icon}</div>
                      <h3 className="text-white font-semibold mb-1">{option.label}</h3>
                      <p className="text-gray-400 text-sm">{option.desc}</p>
                    </button>
                  ))}
                </div>

                <div className="flex justify-end gap-3">
                  <button
                    onClick={() => setShowWizardModal(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleWizardNext}
                    disabled={!selectedTemplateType}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </>
            )}

            {/* Step 2: Form Fields */}
            {wizardStep === 2 && (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-bold text-white">
                    {selectedTemplateType === 'refund' && 'Refund Template'}
                    {selectedTemplateType === 'ban_extension' && 'Ban Extension Template'}
                    {selectedTemplateType === 'player_report' && 'Player Report Template'}
                    {selectedTemplateType === 'staff_application' && 'Staff Application Template'}
                  </h2>
                  <button
                    onClick={() => setWizardStep(1)}
                    className="text-gray-400 hover:text-white"
                  >
                    ← Back
                  </button>
                </div>

                {/* Refund Template Fields */}
                {selectedTemplateType === 'refund' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Player IGN {pastIGNs.length > 1 && <span className="text-xs text-gray-500">({pastIGNs.length} past names)</span>}
                      </label>
                      <input
                        type="text"
                        value={wizardData.player_ign || pastIGNs[0] || steamProfile?.profile.name || ''}
                        onChange={(e) => setWizardData({ ...wizardData, player_ign: e.target.value })}
                        className="input w-full"
                        placeholder="Enter player name"
                        list="past-igns"
                      />
                      {pastIGNs.length > 0 && (
                        <datalist id="past-igns">
                          {pastIGNs.map((ign, i) => <option key={i} value={ign} />)}
                        </datalist>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        SteamID64
                      </label>
                      <input
                        type="text"
                        value={wizardData.steam_id_64 || steamProfile?.steam_id_64 || ''}
                        onChange={(e) => setWizardData({ ...wizardData, steam_id_64: e.target.value })}
                        className="input w-full"
                        placeholder="76561199012665547"
                      />
                    </div>

                    {servers.length > 1 && (
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Server
                        </label>
                        <select
                          value={wizardData.server || ''}
                          onChange={(e) => setWizardData({ ...wizardData, server: e.target.value })}
                          className="input w-full"
                        >
                          <option value="">Select server...</option>
                          {servers.map((server) => (
                            <option key={server.id} value={server.name}>
                              {server.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Items Lost
                      </label>
                      <textarea
                        value={wizardData.items || ''}
                        onChange={(e) => setWizardData({ ...wizardData, items: e.target.value })}
                        className="input w-full h-24"
                        placeholder="List items to refund..."
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Reason
                      </label>
                      <textarea
                        value={wizardData.reason || ''}
                        onChange={(e) => setWizardData({ ...wizardData, reason: e.target.value })}
                        className="input w-full h-24"
                        placeholder="Why is this refund being issued?"
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Proof (URL)
                      </label>
                      <input
                        type="text"
                        value={wizardData.proof || ''}
                        onChange={(e) => setWizardData({ ...wizardData, proof: e.target.value })}
                        className="input w-full"
                        placeholder="Link to screenshot/video"
                      />
                    </div>
                  </div>
                )}

                {/* Ban Extension Template Fields */}
                {selectedTemplateType === 'ban_extension' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Player IGN
                      </label>
                      <input
                        type="text"
                        value={wizardData.player_ign || pastIGNs[0] || steamProfile?.profile.name || ''}
                        onChange={(e) => setWizardData({ ...wizardData, player_ign: e.target.value })}
                        className="input w-full"
                        list="past-igns"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        SteamID
                      </label>
                      <input
                        type="text"
                        value={wizardData.steam_id || steamProfile?.steam_id || ''}
                        onChange={(e) => setWizardData({ ...wizardData, steam_id: e.target.value })}
                        className="input w-full"
                      />
                    </div>

                    {servers.length > 1 && (
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Server
                        </label>
                        <select
                          value={wizardData.server || ''}
                          onChange={(e) => setWizardData({ ...wizardData, server: e.target.value })}
                          className="input w-full"
                        >
                          <option value="">Select server...</option>
                          {servers.map((server) => (
                            <option key={server.id} value={server.name}>
                              {server.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Ban Reason
                      </label>
                      <input
                        type="text"
                        value={wizardData.ban_reason || ''}
                        onChange={(e) => setWizardData({ ...wizardData, ban_reason: e.target.value })}
                        className="input w-full"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Current Ban Time
                      </label>
                      <input
                        type="text"
                        value={wizardData.current_time || ''}
                        onChange={(e) => setWizardData({ ...wizardData, current_time: e.target.value })}
                        className="input w-full"
                        placeholder="e.g., 1 week"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Required Ban Time
                      </label>
                      <input
                        type="text"
                        value={wizardData.required_time || ''}
                        onChange={(e) => setWizardData({ ...wizardData, required_time: e.target.value })}
                        className="input w-full"
                        placeholder="e.g., 2 weeks"
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Extension Reason
                      </label>
                      <textarea
                        value={wizardData.reason || ''}
                        onChange={(e) => setWizardData({ ...wizardData, reason: e.target.value })}
                        className="input w-full h-24"
                      />
                    </div>
                  </div>
                )}

                {/* Player Report Template Fields */}
                {selectedTemplateType === 'player_report' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Reported Player IGN
                      </label>
                      <input
                        type="text"
                        value={wizardData.player_ign || ''}
                        onChange={(e) => setWizardData({ ...wizardData, player_ign: e.target.value })}
                        className="input w-full"
                        list="past-igns"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        SteamID64
                      </label>
                      <input
                        type="text"
                        value={wizardData.steam_id_64 || ''}
                        onChange={(e) => setWizardData({ ...wizardData, steam_id_64: e.target.value })}
                        className="input w-full"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Violation Type
                      </label>
                      <select
                        value={wizardData.violation_type || ''}
                        onChange={(e) => setWizardData({ ...wizardData, violation_type: e.target.value })}
                        className="input w-full"
                      >
                        <option value="">Select violation...</option>
                        <option value="RDM">RDM</option>
                        <option value="LTAP">LTAP</option>
                        <option value="FailRP">FailRP</option>
                        <option value="Propblock">Propblock</option>
                        <option value="Harassment">Harassment</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>

                    {servers.length > 1 && (
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Server
                        </label>
                        <select
                          value={wizardData.server || ''}
                          onChange={(e) => setWizardData({ ...wizardData, server: e.target.value })}
                          className="input w-full"
                        >
                          <option value="">Select server...</option>
                          {servers.map((server) => (
                            <option key={server.id} value={server.name}>
                              {server.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Description
                      </label>
                      <textarea
                        value={wizardData.description || ''}
                        onChange={(e) => setWizardData({ ...wizardData, description: e.target.value })}
                        className="input w-full h-32"
                        placeholder="Describe what happened..."
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Evidence (URLs)
                      </label>
                      <textarea
                        value={wizardData.evidence || ''}
                        onChange={(e) => setWizardData({ ...wizardData, evidence: e.target.value })}
                        className="input w-full h-24"
                        placeholder="Links to screenshots/videos (one per line)"
                      />
                    </div>
                  </div>
                )}

                {/* Staff Application Template Fields */}
                {selectedTemplateType === 'staff_application' && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Applicant Name
                      </label>
                      <input
                        type="text"
                        value={wizardData.applicant_name || ''}
                        onChange={(e) => setWizardData({ ...wizardData, applicant_name: e.target.value })}
                        className="input w-full"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        SteamID64
                      </label>
                      <input
                        type="text"
                        value={wizardData.steam_id_64 || ''}
                        onChange={(e) => setWizardData({ ...wizardData, steam_id_64: e.target.value })}
                        className="input w-full"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Position Applied For
                      </label>
                      <select
                        value={wizardData.position || ''}
                        onChange={(e) => setWizardData({ ...wizardData, position: e.target.value })}
                        className="input w-full"
                      >
                        <option value="">Select position...</option>
                        <option value="T-Staff">T-Staff</option>
                        <option value="Operator">Operator</option>
                        <option value="Moderator">Moderator</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Review Status
                      </label>
                      <select
                        value={wizardData.status || ''}
                        onChange={(e) => setWizardData({ ...wizardData, status: e.target.value })}
                        className="input w-full"
                      >
                        <option value="">Select status...</option>
                        <option value="Pending">Pending Review</option>
                        <option value="Interview">Interview Scheduled</option>
                        <option value="Approved">Approved</option>
                        <option value="Denied">Denied</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Experience Level
                      </label>
                      <select
                        value={wizardData.experience || ''}
                        onChange={(e) => setWizardData({ ...wizardData, experience: e.target.value })}
                        className="input w-full"
                      >
                        <option value="">Select experience...</option>
                        <option value="None">No prior experience</option>
                        <option value="Some">Some experience</option>
                        <option value="Moderate">Moderate experience</option>
                        <option value="Experienced">Highly experienced</option>
                      </select>
                    </div>

                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Reviewer Notes
                      </label>
                      <textarea
                        value={wizardData.notes || ''}
                        onChange={(e) => setWizardData({ ...wizardData, notes: e.target.value })}
                        className="input w-full h-32"
                        placeholder="Add your review comments..."
                      />
                    </div>
                  </div>
                )}

                <div className="flex justify-end gap-3 mt-6">
                  <button
                    onClick={() => setShowWizardModal(false)}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleWizardSubmit}
                    className="btn-primary"
                  >
                    Submit Template
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
