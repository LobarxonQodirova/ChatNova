import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchContacts, removeContact } from '../../store/slices/contactSlice';
import { getInitials, formatRelativeTime } from '../../utils/formatters';
import {
  HiChatBubbleLeftRight,
  HiStar,
  HiEllipsisVertical,
  HiTrash,
  HiNoSymbol,
  HiFunnel,
} from 'react-icons/hi2';

export default function ContactList({ onStartChat }) {
  const dispatch = useDispatch();
  const { contacts, loading } = useSelector((state) => state.contacts);
  const onlineUsers = useSelector((state) => state.chat.onlineUsers);
  const [filter, setFilter] = useState('all');
  const [activeMenu, setActiveMenu] = useState(null);

  useEffect(() => {
    dispatch(fetchContacts({ status: 'accepted' }));
  }, [dispatch]);

  const filteredContacts = contacts.filter((contact) => {
    if (contact.status !== 'accepted') return false;
    if (filter === 'favorites') return contact.is_favorite;
    if (filter === 'online') {
      return onlineUsers[contact.contact_user?.id]?.status === 'online';
    }
    return true;
  });

  const handleRemove = (contactId) => {
    if (window.confirm('Remove this contact?')) {
      dispatch(removeContact(contactId));
    }
    setActiveMenu(null);
  };

  const statusColors = {
    online: 'bg-green-500',
    away: 'bg-yellow-500',
    dnd: 'bg-red-500',
    offline: 'bg-gray-500',
  };

  return (
    <div className="flex-1 overflow-y-auto">
      {/* Filters */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700">
        <HiFunnel className="w-4 h-4 text-slate-500" />
        {['all', 'online', 'favorites'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              filter === f
                ? 'bg-blue-600 text-white'
                : 'bg-slate-700 text-slate-400 hover:text-white'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <span className="ml-auto text-xs text-slate-500">
          {filteredContacts.length} contact{filteredContacts.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Contact list */}
      {loading ? (
        <div className="flex items-center justify-center h-32 text-slate-500 text-sm">
          Loading contacts...
        </div>
      ) : filteredContacts.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-32 text-slate-500 text-sm">
          <p>No contacts found.</p>
        </div>
      ) : (
        <div className="divide-y divide-slate-700/50">
          {filteredContacts.map((contact) => {
            const user = contact.contact_user;
            const userStatus = onlineUsers[user?.id]?.status || user?.status || 'offline';

            return (
              <div
                key={contact.id}
                className="flex items-center gap-3 px-4 py-3 hover:bg-slate-800/50 transition-colors group"
              >
                {/* Avatar */}
                <div className="relative shrink-0">
                  {user?.avatar ? (
                    <img
                      src={user.avatar}
                      alt={user.username}
                      className="w-10 h-10 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-slate-600 flex items-center justify-center text-sm font-medium text-white">
                      {getInitials(user?.display_name || user?.username)}
                    </div>
                  )}
                  <span
                    className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-slate-800 ${
                      statusColors[userStatus]
                    }`}
                  />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <p className="text-sm font-medium text-white truncate">
                      {contact.nickname || user?.display_name || user?.username}
                    </p>
                    {contact.is_favorite && (
                      <HiStar className="w-3.5 h-3.5 text-yellow-500 shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    {userStatus === 'online'
                      ? 'Online'
                      : user?.last_seen
                      ? `Last seen ${formatRelativeTime(user.last_seen)}`
                      : 'Offline'}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => onStartChat && onStartChat(user?.id)}
                    className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-700 rounded-lg"
                    title="Start chat"
                  >
                    <HiChatBubbleLeftRight className="w-4 h-4" />
                  </button>

                  <div className="relative">
                    <button
                      onClick={() => setActiveMenu(activeMenu === contact.id ? null : contact.id)}
                      className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg"
                    >
                      <HiEllipsisVertical className="w-4 h-4" />
                    </button>

                    {activeMenu === contact.id && (
                      <div className="absolute right-0 top-8 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-10 py-1 w-36">
                        <button
                          onClick={() => handleRemove(contact.id)}
                          className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-red-400 hover:bg-slate-700"
                        >
                          <HiTrash className="w-3.5 h-3.5" />
                          Remove
                        </button>
                        <button className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-red-400 hover:bg-slate-700">
                          <HiNoSymbol className="w-3.5 h-3.5" />
                          Block
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
