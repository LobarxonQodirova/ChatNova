import React, { useEffect, useRef } from 'react';
import { useSelector } from 'react-redux';
import { useChat } from '../../hooks/useChat';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { formatMemberCount, formatTypingIndicator, getInitials } from '../../utils/formatters';
import {
  HiPhone,
  HiVideoCamera,
  HiEllipsisVertical,
  HiSignal,
  HiSignalSlash,
  HiUserGroup,
} from 'react-icons/hi2';

export default function ChatWindow({ conversationId }) {
  const { user } = useSelector((state) => state.auth);

  const {
    activeConversation,
    messages,
    typingUsers,
    isConnected,
    messagesLoading,
    hasMore,
    sendMessage,
    onTyping,
    loadMoreMessages,
    markRead,
    sendReaction,
  } = useChat(conversationId);

  // Mark as read when entering conversation
  useEffect(() => {
    if (conversationId && messages.length > 0) {
      markRead();
    }
  }, [conversationId, messages.length, markRead]);

  if (!conversationId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <div className="w-20 h-20 mx-auto mb-4 bg-slate-800 rounded-full flex items-center justify-center">
            <HiUserGroup className="w-10 h-10 text-slate-600" />
          </div>
          <h3 className="text-xl font-semibold text-slate-300 mb-2">Welcome to ChatNova</h3>
          <p className="text-slate-500 max-w-md">
            Select a conversation from the sidebar to start chatting, or create a new one.
          </p>
        </div>
      </div>
    );
  }

  // Determine conversation display name
  const getConversationTitle = () => {
    if (activeConversation?.name) return activeConversation.name;
    if (activeConversation?.type === 'direct' && activeConversation?.members_preview) {
      const other = activeConversation.members_preview.find(
        (m) => m.user?.id !== user?.id
      );
      return other?.user?.display_name || other?.user?.username || 'Chat';
    }
    return 'Conversation';
  };

  const title = getConversationTitle();
  const typingText = formatTypingIndicator(typingUsers);

  return (
    <div className="flex-1 flex flex-col bg-slate-900 h-full">
      {/* Chat Header */}
      <div className="px-4 py-3 bg-slate-800 border-b border-slate-700 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-sm font-medium text-white">
            {activeConversation?.type === 'group' ? (
              <HiUserGroup className="w-5 h-5" />
            ) : (
              getInitials(title)
            )}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">{title}</h3>
            <div className="flex items-center gap-2">
              {typingText ? (
                <p className="text-xs text-blue-400 animate-pulse">{typingText}</p>
              ) : (
                <p className="text-xs text-slate-400">
                  {activeConversation?.member_count
                    ? formatMemberCount(activeConversation.member_count)
                    : ''}
                </p>
              )}
              {/* Connection indicator */}
              <span className="flex items-center gap-1">
                {isConnected ? (
                  <HiSignal className="w-3 h-3 text-green-500" title="Connected" />
                ) : (
                  <HiSignalSlash className="w-3 h-3 text-red-500" title="Disconnected" />
                )}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
            <HiPhone className="w-5 h-5" />
          </button>
          <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
            <HiVideoCamera className="w-5 h-5" />
          </button>
          <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
            <HiEllipsisVertical className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <MessageList
        messages={messages}
        currentUserId={user?.id}
        loading={messagesLoading}
        hasMore={hasMore}
        onLoadMore={loadMoreMessages}
        onReaction={sendReaction}
      />

      {/* Input */}
      <MessageInput
        onSend={sendMessage}
        onTyping={onTyping}
        disabled={!isConnected}
      />
    </div>
  );
}
