'use client';

import { useState } from 'react';
import { SteamProfileNote } from '@/types/templates';
import { templateAPI } from '@/lib/api';
import { 
  ChatBubbleLeftIcon, 
  ExclamationTriangleIcon, 
  ShieldExclamationIcon,
  DocumentTextIcon,
  UserGroupIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  TrashIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

interface SteamProfileNotesProps {
  steamId64: string;
  notes: SteamProfileNote[];
  onNotesUpdate: () => void;
}

const NOTE_TYPE_ICONS = {
  general: ChatBubbleLeftIcon,
  warning_verbal: ExclamationTriangleIcon,
  warning_written: ShieldExclamationIcon,
  ban_history: DocumentTextIcon,
  behavior: UserGroupIcon,
  investigation: MagnifyingGlassIcon,
};

const NOTE_TYPE_COLORS = {
  general: 'bg-gray-100 text-gray-700',
  warning_verbal: 'bg-yellow-100 text-yellow-700',
  warning_written: 'bg-orange-100 text-orange-700',
  ban_history: 'bg-red-100 text-red-700',
  behavior: 'bg-blue-100 text-blue-700',
  investigation: 'bg-purple-100 text-purple-700',
};

const SEVERITY_COLORS = {
  1: 'bg-green-100 text-green-800 border-green-200',
  2: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  3: 'bg-orange-100 text-orange-800 border-orange-200',
  4: 'bg-red-100 text-red-800 border-red-200',
};

export default function SteamProfileNotes({ steamId64, notes, onNotesUpdate }: SteamProfileNotesProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [editingNote, setEditingNote] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    note_type: 'general',
    title: '',
    content: '',
    severity: 1,
    server: '',
    incident_date: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const resetForm = () => {
    setFormData({
      note_type: 'general',
      title: '',
      content: '',
      severity: 1,
      server: '',
      incident_date: '',
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
      if (editingNote) {
        await templateAPI.updateSteamNote(editingNote, formData);
      } else {
        await templateAPI.createSteamNote({
          ...formData,
          steam_profile: steamId64,
        });
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
    n => n.is_active && (n.note_type === 'warning_verbal' || n.note_type === 'warning_written')
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Admin Notes & Warnings</h3>
          {activeWarnings.length > 0 && (
            <p className="text-sm text-red-600 font-medium">
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
        <form onSubmit={handleSubmit} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <div className="space-y-4">
            {/* Note Type & Severity */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Note Type
                </label>
                <select
                  value={formData.note_type}
                  onChange={(e) => setFormData({ ...formData, note_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="general">General Note</option>
                  <option value="warning_verbal">Verbal Warning</option>
                  <option value="warning_written">Written Warning</option>
                  <option value="ban_history">Ban History</option>
                  <option value="behavior">Behavior Note</option>
                  <option value="investigation">Under Investigation</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Severity
                </label>
                <select
                  value={formData.severity}
                  onChange={(e) => setFormData({ ...formData, severity: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
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
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title (Optional)
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Brief title for this note"
              />
            </div>

            {/* Content */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Note Content *
              </label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 min-h-[100px]"
                placeholder="Detailed note about the player's behavior, warnings given, etc."
                required
              />
            </div>

            {/* Server & Incident Date */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Server
                </label>
                <input
                  type="text"
                  value={formData.server}
                  onChange={(e) => setFormData({ ...formData, server: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Server 1, Server 2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Incident Date
                </label>
                <input
                  type="datetime-local"
                  value={formData.incident_date}
                  onChange={(e) => setFormData({ ...formData, incident_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 justify-end">
              <button
                type="button"
                onClick={resetForm}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
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

      {/* Notes List */}
      <div className="space-y-3">
        {notesList.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <ChatBubbleLeftIcon className="w-12 h-12 mx-auto mb-2 text-gray-400" />
            <p>No notes or warnings recorded for this player</p>
          </div>
        ) : (
          notesList.map((note) => {
            const Icon = NOTE_TYPE_ICONS[note.note_type as keyof typeof NOTE_TYPE_ICONS] || ChatBubbleLeftIcon;
            const colorClass = NOTE_TYPE_COLORS[note.note_type as keyof typeof NOTE_TYPE_COLORS] || NOTE_TYPE_COLORS.general;
            const severityClass = SEVERITY_COLORS[note.severity as keyof typeof SEVERITY_COLORS];

            return (
              <div
                key={note.id}
                className={`border rounded-lg p-4 ${
                  note.is_active ? 'border-gray-300 bg-white' : 'border-gray-200 bg-gray-50 opacity-75'
                }`}
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
                          {!note.is_active && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800">
                              Resolved
                            </span>
                          )}
                        </div>
                        {note.title && (
                          <h4 className="font-medium text-gray-900 mt-1">{note.title}</h4>
                        )}
                      </div>
                      
                      {/* Actions */}
                      {note.is_active && (
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
                      )}
                    </div>

                    {/* Note Content */}
                    <p className="text-sm text-gray-700 whitespace-pre-wrap mb-2">
                      {note.content}
                    </p>

                    {/* Metadata */}
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                      <span>
                        By <span className="font-medium text-gray-700">{note.author_name}</span>
                        {note.author_role && (
                          <span className="text-gray-500"> ({note.author_role})</span>
                        )}
                      </span>
                      <span>{new Date(note.created_at).toLocaleString()}</span>
                      {note.server && (
                        <span>Server: <span className="font-medium text-gray-700">{note.server}</span></span>
                      )}
                      {note.incident_date && (
                        <span>Incident: {new Date(note.incident_date).toLocaleString()}</span>
                      )}
                      {note.resolved_at && (
                        <span>
                          Resolved: {new Date(note.resolved_at).toLocaleString()}
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
    </div>
  );
}
