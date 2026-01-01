/**
 * Date formatting utilities with timezone support
 * 
 * These utilities format dates according to the user's timezone and time format preferences.
 */

export interface DateFormatOptions {
  timezone: string;
  use24Hour: boolean;
}

/**
 * Get Intl.DateTimeFormat options based on user preferences
 */
function getBaseOptions(options: DateFormatOptions): Intl.DateTimeFormatOptions {
  return {
    timeZone: options.timezone || 'UTC',
    hour12: !options.use24Hour,
  };
}

/**
 * Format a date string or Date object to a localized date and time string
 * Example: "Jan 1, 2026, 2:30 PM" or "Jan 1, 2026, 14:30"
 */
export function formatDateTime(
  date: string | Date | null | undefined,
  options: DateFormatOptions
): string {
  if (!date) return 'Never';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return 'Invalid date';
  
  const formatOptions: Intl.DateTimeFormatOptions = {
    ...getBaseOptions(options),
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };
  
  return dateObj.toLocaleString('en-US', formatOptions);
}

/**
 * Format a date string or Date object to a localized date string (no time)
 * Example: "Jan 1, 2026"
 */
export function formatDate(
  date: string | Date | null | undefined,
  options: DateFormatOptions
): string {
  if (!date) return 'Never';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return 'Invalid date';
  
  const formatOptions: Intl.DateTimeFormatOptions = {
    timeZone: options.timezone || 'UTC',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };
  
  return dateObj.toLocaleDateString('en-US', formatOptions);
}

/**
 * Format a date string or Date object to a localized time string
 * Example: "2:30 PM" or "14:30"
 */
export function formatTime(
  date: string | Date | null | undefined,
  options: DateFormatOptions
): string {
  if (!date) return 'Never';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return 'Invalid date';
  
  const formatOptions: Intl.DateTimeFormatOptions = {
    ...getBaseOptions(options),
    hour: '2-digit',
    minute: '2-digit',
  };
  
  return dateObj.toLocaleTimeString('en-US', formatOptions);
}

/**
 * Format a date string or Date object to a short time string for charts
 * Example: "14:30" or "2:30 PM"
 */
export function formatTimeShort(
  date: string | Date | null | undefined,
  options: DateFormatOptions
): string {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return '';
  
  const formatOptions: Intl.DateTimeFormatOptions = {
    ...getBaseOptions(options),
    hour: '2-digit',
    minute: '2-digit',
  };
  
  return dateObj.toLocaleTimeString('en-US', formatOptions);
}

/**
 * Format a date with full details (day of week, date, and time)
 * Example: "Wednesday, Jan 1, 2026, 2:30 PM"
 */
export function formatDateTimeFull(
  date: string | Date | null | undefined,
  options: DateFormatOptions
): string {
  if (!date) return 'Never';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return 'Invalid date';
  
  const formatOptions: Intl.DateTimeFormatOptions = {
    ...getBaseOptions(options),
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  };
  
  return dateObj.toLocaleString('en-US', formatOptions);
}

/**
 * Format hour number (0-23) to display format
 * Example: 14 -> "2 PM" or "14:00"
 */
export function formatHour(hour: number, options: DateFormatOptions): string {
  if (options.use24Hour) {
    return `${hour.toString().padStart(2, '0')}:00`;
  }
  
  const period = hour >= 12 ? 'PM' : 'AM';
  const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
  return `${displayHour} ${period}`;
}

/**
 * Format a relative time (e.g., "2 hours ago", "in 3 days")
 */
export function formatRelativeTime(
  date: string | Date | null | undefined
): string {
  if (!date) return 'Never';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(dateObj.getTime())) return 'Invalid date';
  
  const now = new Date();
  const diffMs = now.getTime() - dateObj.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSecs < 60) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} week${weeks !== 1 ? 's' : ''} ago`;
  }
  if (diffDays < 365) {
    const months = Math.floor(diffDays / 30);
    return `${months} month${months !== 1 ? 's' : ''} ago`;
  }
  
  const years = Math.floor(diffDays / 365);
  return `${years} year${years !== 1 ? 's' : ''} ago`;
}
