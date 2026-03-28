import React, { useState, useCallback, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { searchUsers, addContact, clearContactSearch } from '../../store/slices/contactSlice';
import { getInitials } from '../../utils/formatters';
import toast from 'react-hot-toast';
import {
  HiMagnifyingGlass,
  HiUserPlus,
  HiXMark,
  HiCheck,
} from 'react-icons/hi2';

/**
 * Search for users and send contact requests.
 */
export default function ContactSearch() {
  const dispatch = useDispatch();
  const { searchResults, contacts } = useSelector((state) => state.contacts);
  const [query, setQuery] = useState('');
  const [pendingIds, setPendingIds] = useState(new Set());

  // Debounced search
  useEffect(() => {
    if (query.trim().length >= 2) {
      const timer = setTimeout(() => {
        dispatch(searchUsers(query.trim()));
      }, 300);
      return () => clearTimeout(timer);
    } else {
      dispatch(clearContactSearch());
    }
  }, [query, dispatch]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      dispatch(clearContactSearch());
    };
  }, [dispatch]);

  const isAlreadyContact = useCallback(
    (userId) => {
      return contacts.some((c) => c.contact_user?.id === userId);
    },
    [contacts]
  );

  const handleAddContact = async (userId, username) => {
    try {
      await dispatch(addContact({ contactUserId: userId })).unwrap();
      setPendingIds((prev) => new Set([...prev, userId]));
      toast.success(`Contact request sent to ${username}.`);
    } catch (err) {
      toast.error(err || 'Failed to send request.');
    }
  };

  return (
    <div className="border-b border-slate-700 pb-4">
      {/* Search input */}
      <div className="px-4 pt-4">
        <div className="relative">
          <HiMagnifyingGlass className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search users by name or email..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-9 pr-10 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          {query && (
            <button
              onClick={() => {
                setQuery('');
                dispatch(clearContactSearch());
              }}
              className="absolute right-3 top-2.5 text-slate-500 hover:text-white"
            >
              <HiXMark className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Search results */}
      {searchResults.length > 0 && (
        <div className="mt-2 mx-4 bg-slate-700/50 rounded-lg overflow-hidden">
          {searchResults.map((user) => {
            const alreadyAdded = isAlreadyContact(user.id) || pendingIds.has(user.id);

            return (
              <div
                key={user.id}
                className="flex items-center gap-3 px-3 py-2.5 hover:bg-slate-700 transition-colors"
              >
                {user.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.username}
                    className="w-9 h-9 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-9 h-9 rounded-full bg-slate-600 flex items-center justify-center text-xs font-medium text-white">
                    {getInitials(user.display_name || user.username)}
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {user.display_name || user.username}
                  </p>
                  <p className="text-xs text-slate-400">@{user.username}</p>
                </div>

                {alreadyAdded ? (
                  <span className="flex items-center gap-1 text-xs text-green-400">
                    <HiCheck className="w-4 h-4" />
                    {pendingIds.has(user.id) ? 'Sent' : 'Added'}
                  </span>
                ) : (
                  <button
                    onClick={() => handleAddContact(user.id, user.username)}
                    className="flex items-center gap-1 px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors"
                  >
                    <HiUserPlus className="w-3.5 h-3.5" />
                    Add
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {query.length >= 2 && searchResults.length === 0 && (
        <p className="text-center text-xs text-slate-500 mt-3">No users found.</p>
      )}
    </div>
  );
}
