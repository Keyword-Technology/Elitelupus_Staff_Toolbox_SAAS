'use client';

import { useState, useEffect } from 'react';
import { SteamProfileNote } from '@/types/templates';
import { templateAPI } from '@/lib/api';
import { useFormatDate } from '@/hooks/useFormatDate';
import { 
  ChatBubbleLeftIcon, 
  ExclamationTriangleIcon,
  UserGroupIcon,
  PlusIcon,
  TrashIcon,
  CheckIcon,
  XMarkIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';

interface SteamProfileNotesProps {
  steamId64: string;
  steamProfileId?: number;
  notes: SteamProfileNote[];
  onNotesUpdate: () => void;
}

const NOTE_TYPE_ICONS = {
  general: ChatBubbleLeftIcon,
  warning_verbal: ExclamationTriangleIcon,
  behavior: UserGroupIcon,
};

const NOTE_TYPE_COLORS = {
  general: 'bg-gray-100 text-gray-700',
  warning_verbal: 'bg-yellow-100 text-yellow-700',
  behavior: 'bg-blue-100 text-blue-700',
};

const SEVERITY_COLORS = {
  1: 'bg-green-100 text-green-800 border-green-200',
  2: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  3: 'bg-orange-100 text-orange-800 border-orange-200',
  4: 'bg-red-100 text-red-800 border-red-200',
};

export default function SteamProfileNotes({ steamId64, steamProfileId, notes, onNotesUpdate }: SteamProfileNotesProps) {
  const { formatDateTime, formatDate } = useFormatDate();
  const [isCreating, setIsCreating] = useState(false);
  const [editingNote, setEditingNote] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    note_type: 'general',
    title: '',
    content: '',
    severity: 1,
    server: '',
    expiry_hours: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [servers, setServers] = useState<any[]>([]);
  const [showInactive, setShowInactive] = useState(false);

  // Fetch servers on component mount
  useEffect(() => {
    const fetchServers = async () => {
      try {
        const response = await templateAPI.getServers();
        setServers(response.data || []);
        // Auto-select server if only one exists
        if (response.data.length === 1) {
          setFormData(prev => ({ ...prev, server: response.data[0].name }));
        }
      } catch (err) {
        console.error('Failed to fetch servers:', err);
      }
    };
    fetchServers();
  }, []);

  const resetForm = () => {
    setFormData({
      note_type: 'general',
      title: '',
      content: '',
      severity: 1,
      server: '',
      expiry_hours: '',
    });
    setIsCreating(false);
    setEditingNote(null);
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validate steamProfileId is available
      if (!steamProfileId) {
        setError('Steam profile ID not available. Please refresh the page and try again.');
        setLoading(false);
        return;
      }

      // Validate expiry_hours is set
      if (!formData.expiry_hours) {
        setError('Please select an expiry time for the note');
        setLoading(false);
        return;
      }

      // Calculate expires_at from expiry_hours
      const expiryDate = new Date();
      expiryDate.setHours(expiryDate.getHours() + parseInt(formData.expiry_hours));
      
      console.log('Creating note with steam_profile ID:', steamProfileId);
      
      const submitData: any = {
        note_type: formData.note_type,
        title: formData.title,
        content: formData.content,
        severity: formData.severity,
        server: formData.server,
        expires_at: expiryDate.toISOString(),
        steam_profile: steamProfileId,
      };
      
      if (editingNote) {
        await templateAPI.updateSteamNote(editingNote, submitData);
      } else {
        await templateAPI.createSteamNote(submitData);
      }
      resetForm();
      onNotesUpdate();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save note');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (noteId: number) => {
    if (!confirm('Are you sure you want to delete this note?')) return;

    try {
      await templateAPI.deleteSteamNote(noteId);
      onNotesUpdate();
    } catch (err: any) {
      alert('Failed to delete note: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleResolve = async (note: SteamProfileNote) => {
    try {
      await templateAPI.updateSteamNote(note.id, { is_active: false });
      onNotesUpdate();
    } catch (err: any) {
      alert('Failed to resolve note: ' + (err.response?.data?.error || err.message));
    }
  };

  // Ensure notes is always an array
  const notesList = Array.isArray(notes) ? notes : [];
  const activeWarnings = notesList.filter(
    n => n.is_active && n.note_type === 'warning_verbal'
  );
  const activeNotes = notesList.filter(n => n.is_active);
  const inactiveNotes = notesList.filter(n => !n.is_active);
  const criticalNotes = activeNotes.filter(n => n.severity >= 3);

  return (
    <div className="space-y-4">
      {/* Critical/High Severity Banners */}
      {criticalNotes.length > 0 && (
        <div className="space-y-2">
          {criticalNotes.map((note) => (
            <div
              key={`banner-${note.id}`}
              className={`rounded-lg p-4 border-l-4 ${
                note.severity === 4
                  ? 'bg-red-900 border-red-500 text-red-100'
                  : 'bg-orange-900 border-orange-500 text-orange-100'
              }`}
            >
              <div className="flex items-start gap-3">
                <ExclamationTriangleIcon className="w-6 h-6 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-sm uppercase">
                      {note.severity === 4 ? '⚠️ Critical' : '⚠️ High'} Severity Warning
                    </span>
                    <span className="text-xs opacity-75">{note.note_type_display}</span>
                  </div>
                  {note.title && (
                    <h4 className="font-semibold text-base mb-1">{note.title}</h4>
                  )}
                  <p className="text-sm mb-2">{note.content}</p>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs opacity-75">
                    <span>By {note.author_name}</span>
                    <span>{formatDate(note.created_at)}</span>
                    {note.expires_at && (
                      <span>Expires: {formatDate(note.expires_at)}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Admin Notes & Warnings</h3>
          {activeWarnings.length > 0 && (
            <p className="text-sm text-red-400 font-medium">
              {activeWarnings.length} Active Warning{activeWarnings.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>
        {!isCreating && !editingNote && (
          <button
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <PlusIcon className="w-5 h-5" />
            Add Note
          </button>
        )}
      </div>

      {/* Create/Edit Form */}
      {(isCreating || editingNote) && (
        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="space-y-4">
            {/* Note Type & Severity */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Note Type
                </label>
                <select
                  value={formData.note_type}
                  onChange={(e) => setFormData({ ...formData, note_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-dark-bg text-white"
                  required
                >
                  <option value="general">General Note</option>
                  <option value="warning_verbal">Verbal Warning</option>
                  <option value="behavior">Behavior Note</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Severity
                </label>
                <select
                  value={formData.severity}
                  onChange={(e) => setFormData({ ...formData, severity: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-dark-bg text-white"
                  required
                >
                  <option value="1">Low</option>
                  <option value="2">Medium</option>
                  <option value="3">High</option>
                  <option value="4">Critical</option>
                </select>
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Title (Optional)
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-dark-bg text-white"
                placeholder="Brief title for this note"
              />
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Note Content *
              </label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 min-h-[100px] bg-dark-bg text-white"
                placeholder="Detailed note about the player's behavior, warnings given, etc."
                required
              />
            </div>

            {/* Server & Incident Date */}
            <div className={`grid ${servers.length > 1 ? 'grid-cols-2' : 'grid-cols-1'} gap-4`}>
              {servers.length > 1 && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Server
                  </label>
                  <select
                    value={formData.server}
                    onChange={(e) => setFormData({ ...formData, server: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-dark-bg text-white"
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
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Note Expiry
                </label>
                <select
                  value={formData.expiry_hours}
                  onChange={(e) => setFormData({ ...formData, expiry_hours: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-dark-bg text-white"
                  required
                >
                  <option value="">Select expiry time...</option>
                  <option value="12">12 hours</option>
                  <option value="24">24 hours</option>
                  <option value="48">48 hours</option>
                  <option value="72">3 days</option>
                  <option value="168">7 days</option>
                  <option value="672">28 days</option>
                </select>
              </div>
            </div>

            {error && (
              <div className="bg-red-900 border border-red-700 text-red-200 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                disabled={loading}
              >
                {loading ? 'Saving...' : editingNote ? 'Update Note' : 'Create Note'}
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Active Notes List */}
      <div className="space-y-3">
        {activeNotes.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <ChatBubbleLeftIcon className="w-12 h-12 mx-auto mb-2 text-gray-500" />
            <p>No active notes or warnings recorded for this player</p>
          </div>
        ) : (
          activeNotes.map((note) => {
            const Icon = NOTE_TYPE_ICONS[note.note_type as keyof typeof NOTE_TYPE_ICONS] || ChatBubbleLeftIcon;
            const colorClass = NOTE_TYPE_COLORS[note.note_type as keyof typeof NOTE_TYPE_COLORS] || NOTE_TYPE_COLORS.general;
            const severityClass = SEVERITY_COLORS[note.severity as keyof typeof SEVERITY_COLORS];

            return (
              <div
                key={note.id}
                className="border border-gray-300 bg-gray-50 rounded-lg p-4"
              >
                <div className="flex items-start gap-3">
                  {/* Icon */}
                  <div className={`p-2 rounded-lg ${colorClass}`}>
                    <Icon className="w-5 h-5" />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${colorClass}`}>
                            {note.note_type_display}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${severityClass}`}>
                            {note.severity_display}
                          </span>
                        </div>
                        {note.title && (
                          <h4 className="font-medium text-gray-900 mt-1">{note.title}</h4>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex gap-1">
                          <button
                            onClick={() => handleResolve(note)}
                            className="p-1 text-green-600 hover:bg-green-50 rounded"
                            title="Mark as resolved"
                          >
                            <CheckIcon className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDelete(note.id)}
                            className="p-1 text-red-600 hover:bg-red-50 rounded"
                            title="Delete note"
                          >
                            <TrashIcon className="w-5 h-5" />
                          </button>
                        </div>
                      )
                    </div>

                    {/* Note Content */}
                    <p className="text-sm text-gray-700 whitespace-pre-wrap mb-2">
                      {note.content}
                    </p>

                    {/* Metadata */}
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
                      <span>
                        By <span className="font-medium text-gray-900">{note.author_name}</span>
                        {note.author_role && (
                          <span className="text-gray-600"> ({note.author_role})</span>
                        )}
                      </span>
                      <span>{formatDateTime(note.created_at)}</span>
                      {note.server && (
                        <span>Server: <span className="font-medium text-gray-900">{note.server}</span></span>
                      )}
                      {note.expires_at && (
                        <span>Expires: {formatDateTime(note.expires_at)}</span>
                      )}
                      {note.resolved_at && (
                        <span>
                          Resolved: {formatDateTime(note.resolved_at)}
                          {note.resolved_by_name && ` by ${note.resolved_by_name}`}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
      {/* Inactive/Expired Notes - Collapsible */}
      {inactiveNotes.length > 0 && (
        <div className="border-t border-gray-700 pt-3 mt-3">
          <button
            onClick={() => setShowInactive(!showInactive)}
            className="flex items-center justify-between w-full text-left text-gray-400 hover:text-gray-300 transition-colors"
          >
            <span className="text-sm font-medium">
              Inactive Notes ({inactiveNotes.length})
            </span>
            {showInactive ? (
              <ChevronUpIcon className="w-5 h-5" />
            ) : (
              <ChevronDownIcon className="w-5 h-5" />
            )}
          </button>
          
          {showInactive && (
            <div className="space-y-3 mt-3">
              {inactiveNotes.map((note) => {
                const Icon = NOTE_TYPE_ICONS[note.note_type as keyof typeof NOTE_TYPE_ICONS] || ChatBubbleLeftIcon;
                const colorClass = NOTE_TYPE_COLORS[note.note_type as keyof typeof NOTE_TYPE_COLORS] || NOTE_TYPE_COLORS.general;
                const severityClass = SEVERITY_COLORS[note.severity as keyof typeof SEVERITY_COLORS];

                return (
                  <div
                    key={note.id}
                    className="border border-gray-200 bg-gray-100 rounded-lg p-4 opacity-75"
                  >
                    <div className="flex items-start gap-3">
                      {/* Icon */}
                      <div className={`p-2 rounded-lg ${colorClass}`}>
                        <Icon className="w-5 h-5" />
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        {/* Header */}
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className={`text-xs px-2 py-0.5 rounded-full ${colorClass}`}>
                                {note.note_type_display}
                              </span>
                              <span className={`text-xs px-2 py-0.5 rounded-full border ${severityClass}`}>
                                {note.severity_display}
                              </span>
                              <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800">
                                Expired/Resolved
                              </span>
                            </div>
                            {note.title && (
                              <h4 className="font-medium text-gray-900 mt-1">{note.title}</h4>
                            )}
                          </div>
                        </div>

                        {/* Note Content */}
                        <p className="text-sm text-gray-700 whitespace-pre-wrap mb-2">
                          {note.content}
                        </p>

                        {/* Metadata */}
                        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
                          <span>
                            By <span className="font-medium text-gray-900">{note.author_name}</span>
                            {note.author_role && (
                              <span className="text-gray-600"> ({note.author_role})</span>
                            )}
                          </span>
                          <span>{formatDateTime(note.created_at)}</span>
                          {note.server && (
                            <span>Server: <span className="font-medium text-gray-900">{note.server}</span></span>
                          )}
                          {note.expires_at && (
                            <span>Expired: {formatDateTime(note.expires_at)}</span>
                          )}
                          {note.resolved_at && (
                            <span>
                              Resolved: {formatDateTime(note.resolved_at)}
                              {note.resolved_by_name && ` by ${note.resolved_by_name}`}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}    </div>
  );
}
