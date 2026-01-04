'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { featuresAPI } from '@/lib/api';
import toast from 'react-hot-toast';
import {
  PlusIcon,
  ChatBubbleLeftRightIcon,
  PencilIcon,
  TrashIcon,
  XMarkIcon,
  CheckIcon,
  ClockIcon,
  RocketLaunchIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface Feature {
  id: number;
  title: string;
  description: string;
  status: string;
  status_display: string;
  priority: string;
  priority_display: string;
  created_by: number;
  created_by_username: string;
  created_at: string;
  updated_at: string;
  target_date: string | null;
  order: number;
  comment_count: number;
}

interface Comment {
  id: number;
  feature: number;
  author: number;
  author_username: string;
  author_display_name: string;
  author_avatar: string | null;
  author_role: string;
  author_role_color: string;
  content: string;
  created_at: string;
  updated_at: string;
  is_own_comment: boolean;
}

interface FeatureDetail extends Feature {
  comments: Comment[];
}

const statusColors: Record<string, string> = {
  planned: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  in_progress: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  completed: 'bg-green-500/20 text-green-400 border-green-500/30',
  cancelled: 'bg-red-500/20 text-red-400 border-red-500/30',
};

const priorityColors: Record<string, string> = {
  low: 'bg-gray-500/20 text-gray-400',
  medium: 'bg-blue-500/20 text-blue-400',
  high: 'bg-orange-500/20 text-orange-400',
  critical: 'bg-red-500/20 text-red-400',
};

const statusIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  planned: ClockIcon,
  in_progress: RocketLaunchIcon,
  completed: CheckIcon,
  cancelled: XMarkIcon,
};

export default function FutureFeatures() {
  const { user } = useAuth();
  const [features, setFeatures] = useState<Feature[]>([]);
  const [selectedFeature, setSelectedFeature] = useState<FeatureDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [editingComment, setEditingComment] = useState<number | null>(null);
  const [editCommentText, setEditCommentText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const isSysAdmin = user?.role === 'SYSADMIN';

  // Form state for create/edit
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'planned',
    priority: 'medium',
    target_date: '',
    order: 0,
  });

  useEffect(() => {
    loadFeatures();
  }, [statusFilter]);

  const loadFeatures = async () => {
    try {
      setLoading(true);
      const response = await featuresAPI.list(statusFilter || undefined);
      setFeatures(response.data);
    } catch (error) {
      toast.error('Failed to load features');
    } finally {
      setLoading(false);
    }
  };

  const loadFeatureDetail = async (id: number) => {
    try {
      const response = await featuresAPI.get(id);
      setSelectedFeature(response.data);
    } catch (error) {
      toast.error('Failed to load feature details');
    }
  };

  const handleCreateFeature = async () => {
    try {
      await featuresAPI.create({
        ...formData,
        target_date: formData.target_date || null,
      });
      toast.success('Feature created successfully');
      setShowCreateModal(false);
      resetForm();
      loadFeatures();
    } catch (error) {
      toast.error('Failed to create feature');
    }
  };

  const handleUpdateFeature = async () => {
    if (!selectedFeature) return;
    try {
      await featuresAPI.update(selectedFeature.id, {
        ...formData,
        target_date: formData.target_date || null,
      });
      toast.success('Feature updated successfully');
      setShowEditModal(false);
      loadFeatures();
      loadFeatureDetail(selectedFeature.id);
    } catch (error) {
      toast.error('Failed to update feature');
    }
  };

  const handleDeleteFeature = async (id: number) => {
    if (!confirm('Are you sure you want to delete this feature?')) return;
    try {
      await featuresAPI.delete(id);
      toast.success('Feature deleted successfully');
      setSelectedFeature(null);
      loadFeatures();
    } catch (error) {
      toast.error('Failed to delete feature');
    }
  };

  const handleAddComment = async () => {
    if (!selectedFeature || !newComment.trim()) return;
    try {
      await featuresAPI.createComment(selectedFeature.id, newComment);
      toast.success('Comment added');
      setNewComment('');
      loadFeatureDetail(selectedFeature.id);
      loadFeatures(); // Update comment count
    } catch (error) {
      toast.error('Failed to add comment');
    }
  };

  const handleUpdateComment = async (commentId: number) => {
    if (!editCommentText.trim()) return;
    try {
      await featuresAPI.updateComment(commentId, editCommentText);
      toast.success('Comment updated');
      setEditingComment(null);
      setEditCommentText('');
      if (selectedFeature) {
        loadFeatureDetail(selectedFeature.id);
      }
    } catch (error) {
      toast.error('Failed to update comment');
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!confirm('Are you sure you want to delete this comment?')) return;
    try {
      await featuresAPI.deleteComment(commentId);
      toast.success('Comment deleted');
      if (selectedFeature) {
        loadFeatureDetail(selectedFeature.id);
        loadFeatures(); // Update comment count
      }
    } catch (error) {
      toast.error('Failed to delete comment');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      status: 'planned',
      priority: 'medium',
      target_date: '',
      order: 0,
    });
  };

  const openEditModal = () => {
    if (!selectedFeature) return;
    setFormData({
      title: selectedFeature.title,
      description: selectedFeature.description,
      status: selectedFeature.status,
      priority: selectedFeature.priority,
      target_date: selectedFeature.target_date || '',
      order: selectedFeature.order,
    });
    setShowEditModal(true);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <SparklesIcon className="w-7 h-7 text-primary-500" />
            Future Features
          </h1>
          <p className="text-gray-400 mt-1">
            Track upcoming features and share your feedback
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-dark-card border border-dark-border rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="">All Status</option>
            <option value="planned">Planned</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          
          {/* Create Button (SYSADMIN only) */}
          {isSysAdmin && (
            <button
              onClick={() => {
                resetForm();
                setShowCreateModal(true);
              }}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              <PlusIcon className="w-5 h-5" />
              Add Feature
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Feature List */}
        <div className="lg:col-span-1 space-y-3">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
            </div>
          ) : features.length === 0 ? (
            <div className="bg-dark-card border border-dark-border rounded-lg p-6 text-center">
              <SparklesIcon className="w-12 h-12 mx-auto text-gray-500 mb-3" />
              <p className="text-gray-400">No features found</p>
            </div>
          ) : (
            features.map((feature) => {
              const StatusIcon = statusIcons[feature.status] || ClockIcon;
              return (
                <button
                  key={feature.id}
                  onClick={() => loadFeatureDetail(feature.id)}
                  className={`w-full text-left bg-dark-card border rounded-lg p-4 transition-all hover:border-primary-500/50 ${
                    selectedFeature?.id === feature.id
                      ? 'border-primary-500 ring-1 ring-primary-500/30'
                      : 'border-dark-border'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-white truncate">
                        {feature.title}
                      </h3>
                      <p className="text-sm text-gray-400 line-clamp-2 mt-1">
                        {feature.description}
                      </p>
                    </div>
                    <StatusIcon className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  </div>
                  <div className="flex items-center gap-2 mt-3 flex-wrap">
                    <span className={`text-xs px-2 py-1 rounded border ${statusColors[feature.status]}`}>
                      {feature.status_display}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded ${priorityColors[feature.priority]}`}>
                      {feature.priority_display}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1 ml-auto">
                      <ChatBubbleLeftRightIcon className="w-4 h-4" />
                      {feature.comment_count}
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Feature Detail */}
        <div className="lg:col-span-2">
          {selectedFeature ? (
            <div className="bg-dark-card border border-dark-border rounded-lg">
              {/* Detail Header */}
              <div className="p-6 border-b border-dark-border">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <h2 className="text-xl font-semibold text-white">
                      {selectedFeature.title}
                    </h2>
                    <div className="flex items-center gap-3 mt-2 flex-wrap">
                      <span className={`text-sm px-2 py-1 rounded border ${statusColors[selectedFeature.status]}`}>
                        {selectedFeature.status_display}
                      </span>
                      <span className={`text-sm px-2 py-1 rounded ${priorityColors[selectedFeature.priority]}`}>
                        {selectedFeature.priority_display}
                      </span>
                      {selectedFeature.target_date && (
                        <span className="text-sm text-gray-400">
                          Target: {new Date(selectedFeature.target_date).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  {isSysAdmin && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={openEditModal}
                        className="p-2 text-gray-400 hover:text-white hover:bg-dark-bg rounded-lg transition-colors"
                      >
                        <PencilIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDeleteFeature(selectedFeature.id)}
                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-dark-bg rounded-lg transition-colors"
                      >
                        <TrashIcon className="w-5 h-5" />
                      </button>
                    </div>
                  )}
                </div>
                <p className="text-gray-300 mt-4 whitespace-pre-wrap">
                  {selectedFeature.description}
                </p>
                <p className="text-xs text-gray-500 mt-4">
                  Created by {selectedFeature.created_by_username} • {formatDate(selectedFeature.created_at)}
                </p>
              </div>

              {/* Comments Section */}
              <div className="p-6">
                <h3 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                  <ChatBubbleLeftRightIcon className="w-5 h-5" />
                  Comments ({selectedFeature.comments.length})
                </h3>

                {/* Comment List */}
                <div className="space-y-4 mb-6 max-h-96 overflow-y-auto">
                  {selectedFeature.comments.length === 0 ? (
                    <p className="text-gray-400 text-center py-4">
                      No comments yet. Be the first to share your thoughts!
                    </p>
                  ) : (
                    selectedFeature.comments.map((comment) => (
                      <div
                        key={comment.id}
                        className="bg-dark-bg rounded-lg p-4"
                      >
                        <div className="flex items-start gap-3">
                          {comment.author_avatar ? (
                            <img
                              src={comment.author_avatar}
                              alt={comment.author_display_name || comment.author_username}
                              className="w-8 h-8 rounded-full"
                            />
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
                              <span className="text-sm font-medium text-white">
                                {(comment.author_display_name || comment.author_username)[0].toUpperCase()}
                              </span>
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-white">
                                {comment.author_display_name || comment.author_username}
                              </span>
                              <span
                                className="text-xs px-2 py-0.5 rounded"
                                style={{ 
                                  backgroundColor: `${comment.author_role_color}20`,
                                  color: comment.author_role_color 
                                }}
                              >
                                {comment.author_role}
                              </span>
                              <span className="text-xs text-gray-500">
                                {formatDate(comment.created_at)}
                              </span>
                            </div>
                            {editingComment === comment.id ? (
                              <div className="mt-2">
                                <textarea
                                  value={editCommentText}
                                  onChange={(e) => setEditCommentText(e.target.value)}
                                  className="w-full bg-dark-card border border-dark-border rounded-lg px-3 py-2 text-white text-sm resize-none"
                                  rows={3}
                                />
                                <div className="flex gap-2 mt-2">
                                  <button
                                    onClick={() => handleUpdateComment(comment.id)}
                                    className="px-3 py-1 text-sm bg-primary-600 hover:bg-primary-700 text-white rounded transition-colors"
                                  >
                                    Save
                                  </button>
                                  <button
                                    onClick={() => {
                                      setEditingComment(null);
                                      setEditCommentText('');
                                    }}
                                    className="px-3 py-1 text-sm bg-dark-card hover:bg-dark-border text-gray-300 rounded transition-colors"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              </div>
                            ) : (
                              <p className="text-gray-300 mt-1 whitespace-pre-wrap">
                                {comment.content}
                              </p>
                            )}
                          </div>
                          {(comment.is_own_comment || isSysAdmin) && editingComment !== comment.id && (
                            <div className="flex items-center gap-1">
                              {comment.is_own_comment && (
                                <button
                                  onClick={() => {
                                    setEditingComment(comment.id);
                                    setEditCommentText(comment.content);
                                  }}
                                  className="p-1 text-gray-500 hover:text-white rounded transition-colors"
                                >
                                  <PencilIcon className="w-4 h-4" />
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteComment(comment.id)}
                                className="p-1 text-gray-500 hover:text-red-400 rounded transition-colors"
                              >
                                <TrashIcon className="w-4 h-4" />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {/* Add Comment */}
                <div className="border-t border-dark-border pt-4">
                  <textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add your comment..."
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-3 text-white placeholder-gray-500 resize-none focus:outline-none focus:border-primary-500"
                    rows={3}
                  />
                  <div className="flex justify-end mt-2">
                    <button
                      onClick={handleAddComment}
                      disabled={!newComment.trim()}
                      className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                    >
                      Add Comment
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-dark-card border border-dark-border rounded-lg p-12 text-center">
              <SparklesIcon className="w-16 h-16 mx-auto text-gray-500 mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">
                Select a feature to view details
              </h3>
              <p className="text-gray-400">
                Click on a feature from the list to see its details and comments
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-card border border-dark-border rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-dark-border flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Add New Feature</h2>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 text-gray-400 hover:text-white rounded-lg transition-colors"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                  placeholder="Feature title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500 resize-none"
                  rows={4}
                  placeholder="Describe the feature..."
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Status
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                  >
                    <option value="planned">Planned</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Priority
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Target Date (Optional)
                </label>
                <input
                  type="date"
                  value={formData.target_date}
                  onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
                  className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
            <div className="p-6 border-t border-dark-border flex justify-end gap-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 bg-dark-bg hover:bg-dark-border text-gray-300 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateFeature}
                disabled={!formData.title.trim() || !formData.description.trim()}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                Create Feature
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedFeature && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-dark-card border border-dark-border rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-dark-border flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Edit Feature</h2>
              <button
                onClick={() => setShowEditModal(false)}
                className="p-2 text-gray-400 hover:text-white rounded-lg transition-colors"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Title
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                  placeholder="Feature title"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500 resize-none"
                  rows={4}
                  placeholder="Describe the feature..."
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Status
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                  >
                    <option value="planned">Planned</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Priority
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Target Date (Optional)
                </label>
                <input
                  type="date"
                  value={formData.target_date}
                  onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
                  className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-primary-500"
                />
              </div>
            </div>
            <div className="p-6 border-t border-dark-border flex justify-end gap-3">
              <button
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 bg-dark-bg hover:bg-dark-border text-gray-300 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateFeature}
                disabled={!formData.title.trim() || !formData.description.trim()}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
