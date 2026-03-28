import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { logout } from '../../store/slices/authSlice';
import { usePresenceWebSocket } from '../../hooks/useWebSocket';
import {
  HiChatBubbleLeftRight,
  HiUserGroup,
  HiCog6Tooth,
  HiArrowRightOnRectangle,
  HiBell,
  HiMagnifyingGlass,
} from 'react-icons/hi2';

export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { updateStatus } = usePresenceWebSocket();

  const handleLogout = () => {
    updateStatus('offline');
    dispatch(logout());
    navigate('/login');
  };

  const handleStatusChange = (status) => {
    updateStatus(status);
    setShowUserMenu(false);
  };

  const navItems = [
    { path: '/chat', icon: HiChatBubbleLeftRight, label: 'Chat' },
    { path: '/contacts', icon: HiUserGroup, label: 'Contacts' },
    { path: '/settings', icon: HiCog6Tooth, label: 'Settings' },
  ];

  const statusColors = {
    online: 'bg-green-500',
    away: 'bg-yellow-500',
    dnd: 'bg-red-500',
    offline: 'bg-gray-500',
  };

  return (
    <nav className="bg-slate-800 border-b border-slate-700 px-4 py-2 flex items-center justify-between shrink-0">
      {/* Logo */}
      <Link to="/chat" className="flex items-center gap-2">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <HiChatBubbleLeftRight className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-bold text-white hidden sm:block">ChatNova</span>
      </Link>

      {/* Navigation Links */}
      <div className="flex items-center gap-1">
        {navItems.map(({ path, icon: Icon, label }) => {
          const isActive = location.pathname.startsWith(path);
          return (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-700'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="hidden md:inline text-sm">{label}</span>
            </Link>
          );
        })}
      </div>

      {/* Right side: notifications + user */}
      <div className="flex items-center gap-3">
        <button className="relative p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
          <HiBell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* User avatar + dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1 rounded-lg hover:bg-slate-700 transition-colors"
          >
            <div className="relative">
              {user?.avatar ? (
                <img
                  src={user.avatar}
                  alt={user.username}
                  className="w-8 h-8 rounded-full object-cover"
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-medium text-white">
                  {(user?.display_name || user?.username || '?').charAt(0).toUpperCase()}
                </div>
              )}
              <span
                className={`absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-slate-800 ${
                  statusColors[user?.status || 'offline']
                }`}
              />
            </div>
            <span className="text-sm text-slate-300 hidden lg:block">
              {user?.display_name || user?.username}
            </span>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 top-12 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 py-1">
              <div className="px-3 py-2 border-b border-slate-700">
                <p className="text-sm font-medium text-white">{user?.display_name || user?.username}</p>
                <p className="text-xs text-slate-400">{user?.email}</p>
              </div>

              <div className="py-1 border-b border-slate-700">
                <p className="px-3 py-1 text-xs text-slate-500 uppercase">Status</p>
                {['online', 'away', 'dnd'].map((s) => (
                  <button
                    key={s}
                    onClick={() => handleStatusChange(s)}
                    className="flex items-center gap-2 w-full px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-700"
                  >
                    <span className={`w-2.5 h-2.5 rounded-full ${statusColors[s]}`} />
                    {s === 'dnd' ? 'Do Not Disturb' : s.charAt(0).toUpperCase() + s.slice(1)}
                  </button>
                ))}
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-400 hover:bg-slate-700"
              >
                <HiArrowRightOnRectangle className="w-4 h-4" />
                Log Out
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Click outside to close menu */}
      {showUserMenu && (
        <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
      )}
    </nav>
  );
}
