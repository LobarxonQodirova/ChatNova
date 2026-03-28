import React, { useEffect, useRef, useCallback } from 'react';
import MessageBubble from './MessageBubble';

/**
 * Scrollable message list with infinite scroll for loading older messages.
 */
export default function MessageList({
  messages,
  currentUserId,
  loading,
  hasMore,
  onLoadMore,
  onReaction,
}) {
  const containerRef = useRef(null);
  const bottomRef = useRef(null);
  const prevMessageCountRef = useRef(0);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messages.length > prevMessageCountRef.current) {
      const isNewMessage = messages.length - prevMessageCountRef.current <= 2;
      if (isNewMessage) {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
    }
    prevMessageCountRef.current = messages.length;
  }, [messages.length]);

  // Initial scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView();
  }, []);

  // Infinite scroll: load more when scrolled to top
  const handleScroll = useCallback(() => {
    const container = containerRef.current;
    if (!container || loading || !hasMore) return;

    if (container.scrollTop < 100) {
      onLoadMore();
    }
  }, [loading, hasMore, onLoadMore]);

  // Group messages by date
  const groupedMessages = groupMessagesByDate(messages);

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto px-4 py-4"
    >
      {/* Loading indicator at top */}
      {loading && (
        <div className="flex justify-center py-4">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {hasMore && !loading && (
        <button
          onClick={onLoadMore}
          className="w-full py-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
        >
          Load older messages
        </button>
      )}

      {/* Messages grouped by date */}
      {groupedMessages.map(({ date, messages: dayMessages }) => (
        <div key={date}>
          {/* Date divider */}
          <div className="flex items-center gap-4 my-4">
            <div className="flex-1 h-px bg-slate-700" />
            <span className="text-xs text-slate-500 font-medium px-2">{date}</span>
            <div className="flex-1 h-px bg-slate-700" />
          </div>

          {/* Messages for this date */}
          {dayMessages.map((message, index) => {
            const prevMessage = index > 0 ? dayMessages[index - 1] : null;
            const showAvatar = !prevMessage || prevMessage.sender?.id !== message.sender?.id;
            const isOwn = message.sender?.id === currentUserId;

            return (
              <MessageBubble
                key={message.id}
                message={message}
                isOwn={isOwn}
                showAvatar={showAvatar}
                onReaction={onReaction}
              />
            );
          })}
        </div>
      ))}

      {/* Empty state */}
      {!loading && messages.length === 0 && (
        <div className="flex items-center justify-center h-full text-slate-500 text-sm">
          No messages yet. Start the conversation!
        </div>
      )}

      {/* Bottom anchor for auto-scroll */}
      <div ref={bottomRef} />
    </div>
  );
}

/**
 * Group messages by date for rendering date dividers.
 */
function groupMessagesByDate(messages) {
  const groups = {};

  messages.forEach((msg) => {
    const date = new Date(msg.created_at);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    let dateKey;
    if (date.toDateString() === today.toDateString()) {
      dateKey = 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      dateKey = 'Yesterday';
    } else {
      dateKey = date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined,
      });
    }

    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(msg);
  });

  return Object.entries(groups).map(([date, msgs]) => ({
    date,
    messages: msgs,
  }));
}
