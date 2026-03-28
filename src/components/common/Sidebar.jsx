import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { fetchConversations, createConversation } from '../../store/slices/chatSlice';
import { formatConversationTime, truncate, getInitials } from '../../utils/formatters';
import {
  HiMagnifyingGlass,
  HiPlus,
  HiUserGroup,
  HiArchiveBox,
  HiXMark,
} from 'react-icons/hi2';

export default function Sidebar({ activeConversationId }) {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { conversations, loading } = useSelector((state) => state.chat);
  const { user } = useSelector((state) => state.auth);
  const onlineUsers = useSelector((state) => state.chat.onlineUsers);

  const [searchQuery, setSearchQuery] = useState('');
  const [showNewChat, setShowNewChat] = useState(false);
  const [filter, setFilter] = useState('all'); // all, direct, group, channel

  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch]);

  const filteredConversations = conversations.filter((conv) => {
    if (filter !== 'all' && conv.type !== filter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const name = (conv.name || '').toLowerCase();
      const lastMsg = (conv.last_message?.content || '').toLowerCase();
      return name.includes(q) || lastMsg.includes(q);
    }
    return true;
  });

  const getConversationName = (conv) => {
    if (conv.name) return conv.name;
    if (conv.type === 'direct' && conv.members_preview) {
      const other = conv.members_preview.find((m) => m.user?.id !== user?.id);
      return other?.user?.display_name || other?.user?.username || 'Direct Message';
    }
    return 'Conversation';
  };

  const getOtherUser = (conv) => {
    if (conv.type !== 'direct' || !conv.members_preview) return null;
    return conv.members_preview.find((m) => m.user?.id !== user?.id)?.user;
  };

  const isUserOnline = (userId) => {
    return onlineUsers[userId]?.status === 'online';
  };

  const handleConversationClick = (convId) => {
    navigate(`/chat/${convId}`);
  };

  return (
    <div className="w-80 bg-slate-800 border-r border-slate-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-white">Messages</h2>
          <button
            onClick={() => setShowNewChat(!showNewChat)}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            title="New conversation"
          >
            {showNewChat ? <HiXMark className="w-5 h-5" /> : <HiPlus className="w-5 h-5" />}
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <HiMagnifyingGlass className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1 mt-3">
          {[
            { key: 'all', label: 'All' },
            { key: 'direct', label: 'Direct' },
            { key: 'group', label: 'Groups' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilter(key)}
              className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                filter === key
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-400 hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {loading && conversations.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-slate-500 text-sm">
            Loading conversations...
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-slate-500 text-sm">
            <p>No conversations found.</p>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="mt-2 text-blue-400 hover:underline"
              >
                Clear search
              </button>
            )}
          </div>
        ) : (
          filteredConversations.map((conv) => {
            const isActive = conv.id === activeConversationId;
            const name = getConversationName(conv);
            const otherUser = getOtherUser(conv);
            const online = otherUser ? isUserOnline(otherUser.id) : false;

            return (
              <button
                key={conv.id}
                onClick={() => handleConversationClick(conv.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 transition-colors text-left ${
                  isActive
                    ? 'bg-slate-700 border-l-2 border-blue-500'
                    : 'hover:bg-slate-750 border-l-2 border-transparent'
                }`}
              >
                {/* Avatar */}
                <div className="relative shrink-0">
                  {conv.type === 'direct' && otherUser?.avatar ? (
                    <img
                      src={otherUser.avatar}
                      alt={name}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  ) : (
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium text-white ${
                      conv.type === 'group' ? 'bg-purple-600' : conv.type === 'channel' ? 'bg-green-600' : 'bg-blue-600'
                    }`}>
                      {conv.type === 'group' ? (
                        <HiUserGroup className="w-5 h-5" />
                      ) : (
                        getInitials(name)
                      )}
                    </div>
                  )}
                  {conv.type === 'direct' && online && (
                    <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-slate-800" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-white truncate">{name}</p>
                    <span className="text-xs text-slate-500 shrink-0 ml-2">
                      {formatConversationTime(conv.last_activity)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-0.5">
                    <p className="text-xs text-slate-400 truncate">
                      {conv.last_message
                        ? truncate(conv.last_message.content, 40)
                        : 'No messages yet'}
                    </p>
                    {conv.unread_count > 0 && (
                      <span className="ml-2 px-1.5 py-0.5 text-xs font-bold bg-blue-600 text-white rounded-full shrink-0">
                        {conv.unread_count > 99 ? '99+' : conv.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
