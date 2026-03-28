import { format, formatDistanceToNow, isToday, isYesterday, isThisWeek } from 'date-fns';

/**
 * Format a timestamp for display in the message list.
 * Shows "Just now", "5m ago", time today, "Yesterday", or full date.
 *
 * @param {string|Date} dateString - ISO date string or Date object.
 * @returns {string} Human-readable formatted time.
 */
export function formatMessageTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMinutes = Math.floor(diffMs / 60000);

  if (diffMinutes < 1) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (isToday(date)) return format(date, 'h:mm a');
  if (isYesterday(date)) return `Yesterday ${format(date, 'h:mm a')}`;
  if (isThisWeek(date)) return format(date, 'EEEE h:mm a');
  return format(date, 'MMM d, yyyy h:mm a');
}

/**
 * Format a timestamp for the conversation sidebar.
 * Shorter format than message times.
 *
 * @param {string|Date} dateString - ISO date string or Date object.
 * @returns {string} Short formatted time.
 */
export function formatConversationTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);

  if (isToday(date)) return format(date, 'h:mm a');
  if (isYesterday(date)) return 'Yesterday';
  if (isThisWeek(date)) return format(date, 'EEE');
  return format(date, 'MM/dd/yy');
}

/**
 * Format a relative time string (e.g., "3 hours ago").
 *
 * @param {string|Date} dateString - ISO date string or Date object.
 * @returns {string} Relative time string.
 */
export function formatRelativeTime(dateString) {
  if (!dateString) return '';
  return formatDistanceToNow(new Date(dateString), { addSuffix: true });
}

/**
 * Format file size in human-readable format.
 *
 * @param {number} bytes - File size in bytes.
 * @returns {string} Formatted size string (e.g., "1.5 MB").
 */
export function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/**
 * Truncate a string to a maximum length with ellipsis.
 *
 * @param {string} str - Input string.
 * @param {number} maxLength - Maximum character length.
 * @returns {string} Truncated string.
 */
export function truncate(str, maxLength = 50) {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength) + '...';
}

/**
 * Get user initials from a display name or username.
 *
 * @param {string} name - User's display name or username.
 * @returns {string} Up to two initials (e.g., "JD").
 */
export function getInitials(name) {
  if (!name) return '?';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

/**
 * Format the typing indicator text.
 *
 * @param {string[]} usernames - List of usernames currently typing.
 * @returns {string} Typing indicator text.
 */
export function formatTypingIndicator(usernames) {
  if (!usernames || usernames.length === 0) return '';
  if (usernames.length === 1) return `${usernames[0]} is typing...`;
  if (usernames.length === 2) return `${usernames[0]} and ${usernames[1]} are typing...`;
  return `${usernames[0]} and ${usernames.length - 1} others are typing...`;
}

/**
 * Format member count with proper pluralization.
 *
 * @param {number} count - Number of members.
 * @returns {string} Formatted member count.
 */
export function formatMemberCount(count) {
  if (count === 1) return '1 member';
  return `${count} members`;
}
