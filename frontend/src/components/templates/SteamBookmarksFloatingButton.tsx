'use client';

import { useState, useEffect } from 'react';
import { SteamProfileBookmark } from '@/types/templates';
import { templateAPI } from '@/lib/api';
import { 
  BookmarkIcon as BookmarkIconSolid,
  XMarkIcon,
  ArrowTopRightOnSquareIcon,
  TrashIcon,
  StarIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/solid';
import { BookmarkIcon as BookmarkIconOutline } from '@heroicons/react/24/outline';

interface SteamBookmarksFloatingButtonProps {
  onSelectBookmark?: (steamId64: string) => void;
}

export default function SteamBookmarksFloatingButton({ onSelectBookmark }: SteamBookmarksFloatingButtonProps) {
  const [bookmarks, setBookmarks] = useState<SteamProfileBookmark[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isPopout, setIsPopout] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadBookmarks();
    // Refresh bookmarks every 30 seconds
    const interval = setInterval(loadBookmarks, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadBookmarks = async () => {
    try {
      const res = await templateAPI.steamBookmarks();
      // Handle both array and paginated response formats
      const data = Array.isArray(res.data) ? res.data : (res.data.results || []);
      setBookmarks(data);
    } catch (err) {
      console.error('Failed to load bookmarks:', err);
      setBookmarks([]);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Remove this bookmark?')) return;

    try {
      await templateAPI.deleteSteamBookmark(id);
      await loadBookmarks();
    } catch (err: any) {
      alert('Failed to delete bookmark: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleTogglePin = async (bookmark: SteamProfileBookmark) => {
    try {
      await templateAPI.updateSteamBookmark(bookmark.id, { is_pinned: !bookmark.is_pinned });
      await loadBookmarks();
    } catch (err: any) {
      alert('Failed to update bookmark: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleSelectBookmark = (steamId64: string) => {
    if (onSelectBookmark) {
      onSelectBookmark(steamId64);
      if (!isPopout) {
        setIsOpen(false);
      }
    }
  };

  const handlePopout = () => {
    setIsPopout(true);
    setIsOpen(false);
  };

  if (bookmarks.length === 0) {
    return null; // Don't show button if no bookmarks
  }

  return (
    <>
      {/* Floating Button */}
      {!isPopout && (
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`fixed bottom-6 right-6 p-4 rounded-full shadow-lg transition-all z-40 ${
            isOpen
              ? 'bg-blue-700 text-white'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
          title="Steam Bookmarks"
        >
          <div className="relative">
            <BookmarkIconSolid className="w-6 h-6" />
            {bookmarks.length > 0 && (
              <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-semibold">
                {bookmarks.length}
              </span>
            )}
          </div>
        </button>
      )}

      {/* Slide-in Panel */}
      {isOpen && !isPopout && (
        <div className="fixed bottom-24 right-6 w-96 max-h-[600px] bg-white rounded-lg shadow-2xl border border-gray-200 z-40 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <BookmarkIconSolid className="w-5 h-5 text-blue-600" />
              Bookmarked Players
            </h3>
            <div className="flex gap-1">
              <button
                onClick={handlePopout}
                className="p-1 text-gray-500 hover:text-gray-700 rounded"
                title="Pop out to new window"
              >
                <ArrowTopRightOnSquareIcon className="w-5 h-5" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 text-gray-500 hover:text-gray-700 rounded"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Bookmarks List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {bookmarks.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <BookmarkIconOutline className="w-12 h-12 mx-auto mb-2 text-gray-400" />
                <p>No bookmarked players yet</p>
              </div>
            ) : (
              bookmarks.map((bookmark) => (
                <BookmarkCard
                  key={bookmark.id}
                  bookmark={bookmark}
                  onSelect={() => handleSelectBookmark(bookmark.steam_profile_data.steam_id_64)}
                  onDelete={() => handleDelete(bookmark.id)}
                  onTogglePin={() => handleTogglePin(bookmark)}
                />
              ))
            )}
          </div>
        </div>
      )}

      {/* Popout Window */}
      {isPopout && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <BookmarkIconSolid className="w-5 h-5 text-blue-600" />
                Bookmarked Players ({bookmarks.length})
              </h3>
              <button
                onClick={() => setIsPopout(false)}
                className="p-1 text-gray-500 hover:text-gray-700 rounded"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {/* Bookmarks Grid */}
            <div className="flex-1 overflow-y-auto p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {bookmarks.map((bookmark) => (
                  <BookmarkCard
                    key={bookmark.id}
                    bookmark={bookmark}
                    onSelect={() => handleSelectBookmark(bookmark.steam_profile_data.steam_id_64)}
                    onDelete={() => handleDelete(bookmark.id)}
                    onTogglePin={() => handleTogglePin(bookmark)}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

interface BookmarkCardProps {
  bookmark: SteamProfileBookmark;
  onSelect: () => void;
  onDelete: () => void;
  onTogglePin: () => void;
}

function BookmarkCard({ bookmark, onSelect, onDelete, onTogglePin }: BookmarkCardProps) {
  const { steam_profile_data } = bookmark;

  return (
    <div className="border border-gray-200 rounded-lg p-3 hover:border-blue-300 hover:shadow-md transition-all bg-white">
      {/* Avatar & Name */}
      <div className="flex items-start gap-3 mb-2">
        <img
          src={steam_profile_data.avatar_url || '/default-avatar.png'}
          alt={steam_profile_data.persona_name}
          className="w-12 h-12 rounded-lg"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <h4 className="font-medium text-gray-900 truncate">
              {steam_profile_data.persona_name || 'Unknown Player'}
            </h4>
            <div className="flex gap-1">
              <button
                onClick={onTogglePin}
                className={`p-1 rounded ${
                  bookmark.is_pinned
                    ? 'text-yellow-600 hover:bg-yellow-50'
                    : 'text-gray-400 hover:bg-gray-50'
                }`}
                title={bookmark.is_pinned ? 'Unpin' : 'Pin to top'}
              >
                <StarIcon className="w-4 h-4" />
              </button>
              <button
                onClick={onDelete}
                className="p-1 text-red-600 hover:bg-red-50 rounded"
                title="Remove bookmark"
              >
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
          <p className="text-xs text-gray-500 font-mono truncate">
            {steam_profile_data.steam_id_64}
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="flex gap-4 text-xs text-gray-600 mb-2">
        <div>
          <span className="font-medium">Lookups:</span> {steam_profile_data.search_count}
        </div>
        {steam_profile_data.vac_bans > 0 && (
          <div className="text-red-600 font-medium">
            VAC: {steam_profile_data.vac_bans}
          </div>
        )}
        {steam_profile_data.game_bans > 0 && (
          <div className="text-orange-600 font-medium">
            Game Bans: {steam_profile_data.game_bans}
          </div>
        )}
      </div>

      {/* Note */}
      {bookmark.note && (
        <p className="text-sm text-gray-700 mb-2 italic">
          "{bookmark.note}"
        </p>
      )}

      {/* Tags */}
      {bookmark.tags && bookmark.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {bookmark.tags.map((tag, idx) => (
            <span
              key={idx}
              className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={onSelect}
        className="w-full mt-2 px-3 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
      >
        <MagnifyingGlassIcon className="w-4 h-4" />
        View Profile
      </button>
    </div>
  );
}
