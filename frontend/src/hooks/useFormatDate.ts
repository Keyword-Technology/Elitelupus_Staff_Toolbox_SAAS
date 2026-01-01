'use client';

import { useAuth } from '@/contexts/AuthContext';
import {
  formatDateTime,
  formatDate,
  formatTime,
  formatTimeShort,
  formatDateTimeFull,
  formatHour,
  formatRelativeTime,
  type DateFormatOptions,
} from '@/lib/dateUtils';

/**
 * Hook that provides date formatting functions using the user's timezone and time format preferences.
 * 
 * Usage:
 * ```tsx
 * const { formatDateTime, formatDate, formatTime } = useFormatDate();
 * 
 * return <span>{formatDateTime(someDate)}</span>;
 * ```
 */
export function useFormatDate() {
  const { user } = useAuth();
  
  // Default options when user is not logged in or hasn't set preferences
  const options: DateFormatOptions = {
    timezone: user?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    use24Hour: user?.use_24_hour_time ?? true,
  };
  
  return {
    /**
     * Format a date to include both date and time
     * Example: "Jan 1, 2026, 2:30 PM"
     */
    formatDateTime: (date: string | Date | null | undefined) => formatDateTime(date, options),
    
    /**
     * Format a date to show only the date (no time)
     * Example: "Jan 1, 2026"
     */
    formatDate: (date: string | Date | null | undefined) => formatDate(date, options),
    
    /**
     * Format a date to show only the time
     * Example: "2:30 PM" or "14:30"
     */
    formatTime: (date: string | Date | null | undefined) => formatTime(date, options),
    
    /**
     * Format a date to a short time string for charts
     * Example: "14:30" or "2:30 PM"
     */
    formatTimeShort: (date: string | Date | null | undefined) => formatTimeShort(date, options),
    
    /**
     * Format a date with full details including day of week
     * Example: "Wednesday, Jan 1, 2026, 2:30 PM"
     */
    formatDateTimeFull: (date: string | Date | null | undefined) => formatDateTimeFull(date, options),
    
    /**
     * Format an hour number (0-23) to display format
     * Example: 14 -> "2 PM" or "14:00"
     */
    formatHour: (hour: number) => formatHour(hour, options),
    
    /**
     * Format a relative time (e.g., "2 hours ago")
     */
    formatRelativeTime: (date: string | Date | null | undefined) => formatRelativeTime(date),
    
    /**
     * The user's configured timezone
     */
    timezone: options.timezone,
    
    /**
     * Whether the user prefers 24-hour time format
     */
    use24Hour: options.use24Hour,
    
    /**
     * The raw formatting options for custom use cases
     */
    options,
  };
}

export default useFormatDate;
