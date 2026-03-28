import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import chatApi from '../../api/chatApi';
import { formatMessageTime, getInitials, formatMemberCount } from '../../utils/formatters';
import {
  HiUserGroup,
  HiCog6Tooth,
  HiArrowRightOnRectangle,
  HiPaperAirplane,
  HiUsers,
} from 'react-icons/hi2';

/**
 * Group chat component with message list, member sidebar, and send functionality.
 */
export default function GroupChat({ groupId }) {
  const { user } = useSelector((state) => state.auth);
  const [group, setGroup] = useState(null);
  const [messages, setMessages] = useState([]);
  const [members, setMembers] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [showMembers, setShowMembers] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!groupId) return;

    const loadGroup = async () => {
      setLoading(true);
      try {
        const [groupRes, messagesRes, membersRes] = await Promise.all([
          chatApi.getGroup(groupId),
          chatApi.getGroupMessages(groupId),
          chatApi.getGroupMembers(groupId),
        ]);
        setGroup(groupRes.data);
        setMessages((messagesRes.data.results || messagesRes.data).reverse());
        setMembers(membersRes.data.results || membersRes.data);
      } catch (err) {
        console.error('Failed to load group:', err);
      } finally {
        setLoading(false);
      }
    };

    loadGroup();
  }, [groupId]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    try {
      const response = await chatApi.sendGroupMessage(groupId, {
        content: newMessage,
        type: 'text',
      });
      setMessages((prev) => [...prev, response.data]);
      setNewMessage('');
    } catch (err) {
      console.error('Failed to send group message:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        Loading group...
      </div>
    );
  }

  if (!group) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        Group not found.
      </div>
    );
  }

  const roleColors = {
    owner: 'text-yellow-400',
    admin: 'text-blue-400',
    moderator: 'text-green-400',
    member: 'text-slate-400',
  };

  return (
    <div className="flex h-full">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Group header */}
        <div className="px-4 py-3 bg-slate-800 border-b border-slate-700 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            {group.avatar ? (
              <img src={group.avatar} alt={group.name} className="w-10 h-10 rounded-full object-cover" />
            ) : (
              <div className="w-10 h-10 rounded-full bg-purple-600 flex items-center justify-center">
                <HiUserGroup className="w-5 h-5 text-white" />
              </div>
            )}
            <div>
              <h3 className="text-sm font-semibold text-white">{group.name}</h3>
              <p className="text-xs text-slate-400">
                {formatMemberCount(group.member_count)}
                {group.description && ` - ${group.description.substring(0, 50)}`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowMembers(!showMembers)}
              className={`p-2 rounded-lg transition-colors ${
                showMembers ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
            >
              <HiUsers className="w-5 h-5" />
            </button>
            <button className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
              <HiCog6Tooth className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.map((msg) => {
            const isOwn = msg.sender?.id === user?.id;
            const isSystem = msg.type === 'system';

            if (isSystem) {
              return (
                <div key={msg.id} className="flex justify-center">
                  <span className="px-3 py-1 bg-slate-800 text-slate-500 text-xs rounded-full">
                    {msg.content}
                  </span>
                </div>
              );
            }

            return (
              <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                {!isOwn && (
                  <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-xs font-medium text-white mr-2 shrink-0 mt-5">
                    {getInitials(msg.sender?.display_name || msg.sender?.username)}
                  </div>
                )}
                <div className="max-w-md">
                  {!isOwn && (
                    <p className="text-xs text-slate-400 mb-0.5 ml-1">
                      {msg.sender?.display_name || msg.sender?.username}
                    </p>
                  )}
                  <div className={`px-4 py-2 rounded-2xl ${
                    isOwn ? 'bg-blue-600 text-white rounded-br-md' : 'bg-slate-700 text-slate-100 rounded-bl-md'
                  }`}>
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    <p className="text-[10px] opacity-50 mt-1">
                      {formatMessageTime(msg.created_at)}
                      {msg.is_edited && ' (edited)'}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Input */}
        <form onSubmit={handleSend} className="border-t border-slate-700 bg-slate-800 px-4 py-3 flex gap-2 shrink-0">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2.5 bg-slate-700 border border-slate-600 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={!newMessage.trim()}
            className="p-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white rounded-xl transition-colors"
          >
            <HiPaperAirplane className="w-5 h-5" />
          </button>
        </form>
      </div>

      {/* Members sidebar */}
      {showMembers && (
        <div className="w-64 bg-slate-800 border-l border-slate-700 overflow-y-auto">
          <div className="p-4 border-b border-slate-700">
            <h4 className="text-sm font-semibold text-white">
              Members ({members.length})
            </h4>
          </div>
          <div className="divide-y divide-slate-700/50">
            {members.map((member) => (
              <div key={member.id} className="flex items-center gap-2 px-4 py-2.5">
                <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-xs font-medium text-white">
                  {getInitials(member.user?.display_name || member.user?.username)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">
                    {member.nickname || member.user?.display_name || member.user?.username}
                  </p>
                  <p className={`text-xs ${roleColors[member.role]}`}>
                    {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
