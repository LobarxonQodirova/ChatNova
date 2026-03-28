import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchContacts } from '../../store/slices/contactSlice';
import chatApi from '../../api/chatApi';
import { getInitials } from '../../utils/formatters';
import toast from 'react-hot-toast';
import {
  HiXMark,
  HiUserGroup,
  HiCheck,
  HiMagnifyingGlass,
} from 'react-icons/hi2';

/**
 * Modal/panel for creating a new group chat.
 */
export default function CreateGroup({ onClose, onCreated }) {
  const dispatch = useDispatch();
  const { contacts } = useSelector((state) => state.contacts);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    dispatch(fetchContacts({ status: 'accepted' }));
  }, [dispatch]);

  const filteredContacts = contacts.filter((contact) => {
    if (contact.status !== 'accepted') return false;
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const user = contact.contact_user;
    return (
      (user?.username || '').toLowerCase().includes(q) ||
      (user?.display_name || '').toLowerCase().includes(q)
    );
  });

  const toggleMember = (userId) => {
    setSelectedMembers((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleCreate = async () => {
    if (!name.trim()) {
      toast.error('Group name is required.');
      return;
    }

    setCreating(true);
    try {
      const response = await chatApi.createGroup({
        name: name.trim(),
        description: description.trim(),
        is_public: isPublic,
        member_ids: selectedMembers,
      });
      toast.success(`Group "${name}" created!`);
      onCreated?.(response.data);
      onClose?.();
    } catch (err) {
      toast.error(err.response?.data?.error?.message || 'Failed to create group.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-xl shadow-2xl w-full max-w-md mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <HiUserGroup className="w-5 h-5 text-blue-400" />
            <h3 className="text-lg font-semibold text-white">Create Group</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg"
          >
            <HiXMark className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <div className="p-4 space-y-4 overflow-y-auto flex-1">
          {/* Group name */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Group Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Project Team"
              maxLength={200}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What is this group about?"
              maxLength={1000}
              rows={2}
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none"
            />
          </div>

          {/* Public toggle */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-white">Public Group</p>
              <p className="text-xs text-slate-400">Anyone can find and join this group.</p>
            </div>
            <button
              onClick={() => setIsPublic(!isPublic)}
              className={`relative w-10 h-5 rounded-full transition-colors ${
                isPublic ? 'bg-blue-600' : 'bg-slate-600'
              }`}
            >
              <span
                className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                  isPublic ? 'translate-x-5' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>

          {/* Add members */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Add Members ({selectedMembers.length} selected)
            </label>

            {/* Search contacts */}
            <div className="relative mb-2">
              <HiMagnifyingGlass className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search contacts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Contact list */}
            <div className="max-h-48 overflow-y-auto rounded-lg border border-slate-700">
              {filteredContacts.map((contact) => {
                const user = contact.contact_user;
                const isSelected = selectedMembers.includes(user?.id);

                return (
                  <button
                    key={contact.id}
                    onClick={() => user?.id && toggleMember(user.id)}
                    className={`flex items-center gap-3 w-full px-3 py-2 transition-colors ${
                      isSelected ? 'bg-blue-600/20' : 'hover:bg-slate-700'
                    }`}
                  >
                    <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-xs font-medium text-white shrink-0">
                      {getInitials(user?.display_name || user?.username)}
                    </div>
                    <p className="text-sm text-white truncate flex-1 text-left">
                      {user?.display_name || user?.username}
                    </p>
                    {isSelected && (
                      <HiCheck className="w-5 h-5 text-blue-400 shrink-0" />
                    )}
                  </button>
                );
              })}
              {filteredContacts.length === 0 && (
                <p className="text-center text-xs text-slate-500 py-4">No contacts found.</p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-4 border-t border-slate-700">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={!name.trim() || creating}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center"
          >
            {creating ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              'Create Group'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
