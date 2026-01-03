'use client';

import { useState, useEffect } from 'react';
import { staffAPI } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  UserPlusIcon,
  UserMinusIcon,
  ArrowPathIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  SparklesIcon,
  CalendarIcon,
  TrashIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

interface HistoryEvent {
  id: number;
  staff: string;
  staff_name: string;
  event_type: string;
  event_type_display: string;
  old_rank: string | null;
  new_rank: string | null;
  old_rank_priority: number | null;
  new_rank_priority: number | null;
  old_rank_color: string | null;
  new_rank_color: string | null;
  event_date: string;
  notes: string;
  auto_detected: boolean;
  event_description: string;
  is_promotion: boolean;
  is_demotion: boolean;
  created_at: string;
}

interface Summary {
  promotions: number;
  demotions: number;
  joins: number;
  removals: number;
  rejoined: number;
  role_changes: number;
}

interface CategorizedEvents {
  promotions: HistoryEvent[];
  demotions: HistoryEvent[];
  joins: HistoryEvent[];
  removals: HistoryEvent[];
  rejoined: HistoryEvent[];
  role_changes: HistoryEvent[];
}

interface PromotionsData {
  week_offset: number;
  week_start: string;
  week_end: string;
  week_label: string;
  total_events: number;
  summary: Summary;
  events: CategorizedEvents;
  all_events: HistoryEvent[];
}

export default function RecentPromotionsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [data, setData] = useState<PromotionsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [offset, setOffset] = useState(0);
  const [deletingEventId, setDeletingEventId] = useState<number | null>(null);

  // Check if user is SYSADMIN (role_priority 0)
  const isSysAdmin = user?.role_priority === 0;

  useEffect(() => {
    fetchData();
  }, [offset]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await staffAPI.recentPromotions(offset);
      setData(res.data);
    } catch (error) {
      toast.error('Failed to load recent promotions');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const getEventIcon = (eventType: string, isPromotion: boolean, isDemotion: boolean) => {
    if (eventType === 'joined') return <UserPlusIcon className="w-5 h-5 text-green-400" />;
    if (eventType === 'rejoined') return <ArrowPathIcon className="w-5 h-5 text-blue-400" />;
    if (eventType === 'removed' || eventType === 'left') return <UserMinusIcon className="w-5 h-5 text-red-400" />;
    if (eventType === 'promoted' || isPromotion) return <ArrowUpIcon className="w-5 h-5 text-green-400" />;
    if (eventType === 'demoted' || isDemotion) return <ArrowDownIcon className="w-5 h-5 text-red-400" />;
    return <SparklesIcon className="w-5 h-5 text-yellow-400" />;
  };

  const getEventBgClass = (eventType: string, isPromotion: boolean, isDemotion: boolean) => {
    if (eventType === 'joined') return 'border-green-500/30 bg-green-500/5';
    if (eventType === 'rejoined') return 'border-blue-500/30 bg-blue-500/5';
    if (eventType === 'removed' || eventType === 'left') return 'border-red-500/30 bg-red-500/5';
    if (eventType === 'promoted' || isPromotion) return 'border-green-500/30 bg-green-500/5';
    if (eventType === 'demoted' || isDemotion) return 'border-red-500/30 bg-red-500/5';
    return 'border-yellow-500/30 bg-yellow-500/5';
  };

  const handleDeleteEvent = async (eventId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this event? This action cannot be undone.')) {
      return;
    }
    
    setDeletingEventId(eventId);
    try {
      await staffAPI.deleteHistoryEvent(eventId);
      toast.success('Event deleted');
      // Refresh data
      fetchData();
    } catch (error: any) {
      if (error.response?.status === 403) {
        toast.error('Only SYSADMIN can delete events');
      } else {
        toast.error('Failed to delete event');
      }
    } finally {
      setDeletingEventId(null);
    }
  };

  const EventCard = ({ event }: { event: HistoryEvent }) => (
    <div
      className={`rounded-lg border p-4 ${getEventBgClass(event.event_type, event.is_promotion, event.is_demotion)} hover:bg-dark-bg/50 transition-colors cursor-pointer`}
      onClick={() => router.push(`/dashboard/staff/${event.staff}`)}
    >
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-dark-card">
          {getEventIcon(event.event_type, event.is_promotion, event.is_demotion)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-white">{event.staff_name}</span>
            <span className="text-gray-400 text-sm">{event.event_type_display}</span>
          </div>
          <div className="mt-1 text-sm">
            {event.old_rank && event.new_rank ? (
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className="px-2 py-0.5 rounded text-xs"
                  style={{
                    backgroundColor: `${event.old_rank_color}20`,
                    color: event.old_rank_color || '#808080',
                  }}
                >
                  {event.old_rank}
                </span>
                <span className="text-gray-500">→</span>
                <span
                  className="px-2 py-0.5 rounded text-xs"
                  style={{
                    backgroundColor: `${event.new_rank_color}20`,
                    color: event.new_rank_color || '#808080',
                  }}
                >
                  {event.new_rank}
                </span>
              </div>
            ) : event.new_rank ? (
              <span
                className="px-2 py-0.5 rounded text-xs"
                style={{
                  backgroundColor: `${event.new_rank_color}20`,
                  color: event.new_rank_color || '#808080',
                }}
              >
                {event.new_rank}
              </span>
            ) : event.old_rank ? (
              <span className="text-gray-400 text-xs">was {event.old_rank}</span>
            ) : null}
          </div>
          {event.notes && (
            <p className="text-gray-400 text-xs mt-1">{event.notes}</p>
          )}
        </div>
        <div className="flex items-start gap-2">
          <div className="text-right text-xs text-gray-500">
            {formatDate(event.event_date)}
          </div>
          
          {/* Delete button - SYSADMIN only */}
          {isSysAdmin && (
            <button
              onClick={(e) => handleDeleteEvent(event.id, e)}
              disabled={deletingEventId === event.id}
              className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-50"
              title="Delete event"
            >
              {deletingEventId === event.id ? (
                <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
              ) : (
                <TrashIcon className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );

  const CategorySection = ({
    title,
    events,
    icon,
    emptyMessage,
    color,
  }: {
    title: string;
    events: HistoryEvent[];
    icon: React.ReactNode;
    emptyMessage: string;
    color: string;
  }) => {
    if (events.length === 0) return null;

    return (
      <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
        <div className={`p-4 border-b border-dark-border bg-gradient-to-r ${color}`}>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            {icon}
            {title}
            <span className="ml-auto text-sm font-normal bg-dark-bg px-2 py-0.5 rounded">
              {events.length}
            </span>
          </h2>
        </div>
        <div className="p-4 space-y-3">
          {events.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <SparklesIcon className="w-8 h-8 text-primary-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">Recent Promotions</h1>
            <p className="text-gray-400 text-sm">Staff role changes and roster updates</p>
          </div>
        </div>
      </div>

      {/* Week Navigation */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-4">
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => setOffset(offset + 1)}
            className="p-2 rounded-lg bg-dark-bg hover:bg-dark-border transition-colors"
            title="Previous week"
          >
            <ChevronLeftIcon className="w-5 h-5 text-gray-400" />
          </button>
          
          <div className="text-center min-w-[200px]">
            <div className="flex items-center justify-center gap-2 text-white font-medium">
              <CalendarIcon className="w-5 h-5 text-primary-400" />
              {data?.week_label || 'Loading...'}
            </div>
            {offset > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                {offset} week{offset > 1 ? 's' : ''} ago
              </p>
            )}
          </div>
          
          <button
            onClick={() => setOffset(Math.max(0, offset - 1))}
            disabled={offset === 0}
            className={`p-2 rounded-lg transition-colors ${
              offset === 0 
                ? 'bg-dark-bg text-gray-600 cursor-not-allowed' 
                : 'bg-dark-bg hover:bg-dark-border text-gray-400'
            }`}
            title="Next week"
          >
            <ChevronRightIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      {data && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-dark-card rounded-lg border border-green-500/30 p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <ArrowUpIcon className="w-5 h-5 text-green-400" />
              <span className="text-2xl font-bold text-green-400">{data.summary.promotions}</span>
            </div>
            <p className="text-sm text-gray-400">Promotions</p>
          </div>
          <div className="bg-dark-card rounded-lg border border-red-500/30 p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <ArrowDownIcon className="w-5 h-5 text-red-400" />
              <span className="text-2xl font-bold text-red-400">{data.summary.demotions}</span>
            </div>
            <p className="text-sm text-gray-400">Demotions</p>
          </div>
          <div className="bg-dark-card rounded-lg border border-green-500/30 p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <UserPlusIcon className="w-5 h-5 text-green-400" />
              <span className="text-2xl font-bold text-green-400">{data.summary.joins}</span>
            </div>
            <p className="text-sm text-gray-400">New Joins</p>
          </div>
          <div className="bg-dark-card rounded-lg border border-red-500/30 p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <UserMinusIcon className="w-5 h-5 text-red-400" />
              <span className="text-2xl font-bold text-red-400">{data.summary.removals}</span>
            </div>
            <p className="text-sm text-gray-400">Removals</p>
          </div>
          <div className="bg-dark-card rounded-lg border border-blue-500/30 p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <ArrowPathIcon className="w-5 h-5 text-blue-400" />
              <span className="text-2xl font-bold text-blue-400">{data.summary.rejoined}</span>
            </div>
            <p className="text-sm text-gray-400">Rejoined</p>
          </div>
          <div className="bg-dark-card rounded-lg border border-yellow-500/30 p-4 text-center">
            <div className="flex items-center justify-center gap-2 mb-1">
              <SparklesIcon className="w-5 h-5 text-yellow-400" />
              <span className="text-2xl font-bold text-yellow-400">{data.summary.role_changes}</span>
            </div>
            <p className="text-sm text-gray-400">Other Changes</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      )}

      {/* No Events State */}
      {!loading && data && data.total_events === 0 && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-12 text-center">
          <SparklesIcon className="w-12 h-12 mx-auto mb-3 text-gray-600" />
          <p className="text-lg text-gray-400">No role changes this week</p>
          <p className="text-sm text-gray-500 mt-1">
            Staff promotions, demotions, and roster changes will appear here
          </p>
        </div>
      )}

      {/* Event Categories */}
      {!loading && data && data.total_events > 0 && (
        <div className="space-y-6">
          <CategorySection
            title="Promotions"
            events={data.events.promotions}
            icon={<ArrowUpIcon className="w-5 h-5 text-green-400" />}
            emptyMessage="No promotions this week"
            color="from-green-500/10 to-transparent"
          />
          
          <CategorySection
            title="New Staff"
            events={data.events.joins}
            icon={<UserPlusIcon className="w-5 h-5 text-green-400" />}
            emptyMessage="No new staff this week"
            color="from-green-500/10 to-transparent"
          />
          
          <CategorySection
            title="Rejoined Staff"
            events={data.events.rejoined}
            icon={<ArrowPathIcon className="w-5 h-5 text-blue-400" />}
            emptyMessage="No staff rejoined this week"
            color="from-blue-500/10 to-transparent"
          />
          
          <CategorySection
            title="Demotions"
            events={data.events.demotions}
            icon={<ArrowDownIcon className="w-5 h-5 text-red-400" />}
            emptyMessage="No demotions this week"
            color="from-red-500/10 to-transparent"
          />
          
          <CategorySection
            title="Staff Removed"
            events={data.events.removals}
            icon={<UserMinusIcon className="w-5 h-5 text-red-400" />}
            emptyMessage="No staff removed this week"
            color="from-red-500/10 to-transparent"
          />
          
          <CategorySection
            title="Other Role Changes"
            events={data.events.role_changes}
            icon={<SparklesIcon className="w-5 h-5 text-yellow-400" />}
            emptyMessage="No other role changes this week"
            color="from-yellow-500/10 to-transparent"
          />
        </div>
      )}
    </div>
  );
}
