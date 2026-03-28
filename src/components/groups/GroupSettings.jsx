import React, { useState, useEffect } from 'react';
import chatApi from '../../api/chatApi';
import toast from 'react-hot-toast';
import {
  HiCog6Tooth,
  HiShieldCheck,
  HiClock,
  HiLink,
  HiClipboard,
  HiCheckCircle,
} from 'react-icons/hi2';

/**
 * Group settings panel for admins to configure group behavior.
 */
export default function GroupSettings({ groupId, userRole }) {
  const [settings, setSettings] = useState(null);
  const [inviteLink, setInviteLink] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);

  const isAdmin = userRole === 'owner' || userRole === 'admin';

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const [settingsRes, inviteRes] = await Promise.all([
          chatApi.updateGroupSettings(groupId, {}),
          chatApi.getGroup(groupId),
        ]);
        setSettings(settingsRes.data);
        setInviteLink(inviteRes.data.invite_link || '');
      } catch (err) {
        // Load existing settings via GET
        try {
          const res = await chatApi.getGroup(groupId);
          setSettings(res.data.settings || {});
          setInviteLink(res.data.invite_link || '');
        } catch (innerErr) {
          console.error('Failed to load settings:', innerErr);
        }
      } finally {
        setLoading(false);
      }
    };
    loadSettings();
  }, [groupId]);

  const handleToggle = async (field) => {
    if (!isAdmin) return;

    const updated = { ...settings, [field]: !settings[field] };
    setSettings(updated);

    try {
      setSaving(true);
      await chatApi.updateGroupSettings(groupId, { [field]: updated[field] });
      toast.success('Settings updated.');
    } catch (err) {
      setSettings({ ...settings }); // Revert
      toast.error('Failed to update settings.');
    } finally {
      setSaving(false);
    }
  };

  const handleSlowModeChange = async (value) => {
    if (!isAdmin) return;

    const seconds = parseInt(value, 10);
    setSettings({ ...settings, slow_mode_seconds: seconds });

    try {
      await chatApi.updateGroupSettings(groupId, { slow_mode_seconds: seconds });
      toast.success('Slow mode updated.');
    } catch (err) {
      toast.error('Failed to update slow mode.');
    }
  };

  const copyInviteLink = () => {
    navigator.clipboard.writeText(inviteLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="p-6 text-slate-500 text-sm">Loading settings...</div>
    );
  }

  const toggleSettings = [
    {
      key: 'only_admins_can_post',
      label: 'Only admins can post',
      description: 'Restrict messaging to admins and moderators only.',
      icon: HiShieldCheck,
    },
    {
      key: 'only_admins_can_edit_info',
      label: 'Only admins can edit info',
      description: 'Only admins can change group name, description, and avatar.',
      icon: HiCog6Tooth,
    },
    {
      key: 'member_can_invite',
      label: 'Members can invite',
      description: 'Allow non-admin members to share the invite link.',
      icon: HiLink,
    },
    {
      key: 'approve_new_members',
      label: 'Approve new members',
      description: 'Require admin approval for new join requests.',
      icon: HiShieldCheck,
    },
  ];

  return (
    <div className="p-6 max-w-lg">
      <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
        <HiCog6Tooth className="w-5 h-5" />
        Group Settings
      </h3>

      {/* Invite link */}
      {inviteLink && (
        <div className="mb-6 p-4 bg-slate-700/50 rounded-lg">
          <label className="text-sm font-medium text-white mb-2 block">Invite Link</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={inviteLink}
              readOnly
              className="flex-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-slate-300 focus:outline-none"
            />
            <button
              onClick={copyInviteLink}
              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors flex items-center gap-1"
            >
              {copied ? <HiCheckCircle className="w-4 h-4" /> : <HiClipboard className="w-4 h-4" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
        </div>
      )}

      {/* Toggle settings */}
      <div className="space-y-4">
        {toggleSettings.map(({ key, label, description, icon: Icon }) => (
          <div
            key={key}
            className="flex items-start justify-between p-3 bg-slate-700/30 rounded-lg"
          >
            <div className="flex items-start gap-3">
              <Icon className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-white">{label}</p>
                <p className="text-xs text-slate-400 mt-0.5">{description}</p>
              </div>
            </div>
            <button
              onClick={() => handleToggle(key)}
              disabled={!isAdmin || saving}
              className={`relative w-10 h-5 rounded-full transition-colors shrink-0 ml-3 mt-0.5 ${
                settings?.[key] ? 'bg-blue-600' : 'bg-slate-600'
              } ${!isAdmin ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <span
                className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                  settings?.[key] ? 'translate-x-5' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>
        ))}

        {/* Slow mode */}
        <div className="p-3 bg-slate-700/30 rounded-lg">
          <div className="flex items-start gap-3">
            <HiClock className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-white">Slow mode</p>
              <p className="text-xs text-slate-400 mt-0.5">
                Minimum seconds between messages per user.
              </p>
              <select
                value={settings?.slow_mode_seconds || 0}
                onChange={(e) => handleSlowModeChange(e.target.value)}
                disabled={!isAdmin}
                className="mt-2 px-3 py-1.5 bg-slate-700 border border-slate-600 rounded-lg text-sm text-white focus:outline-none disabled:opacity-50"
              >
                <option value={0}>Off</option>
                <option value={5}>5 seconds</option>
                <option value={10}>10 seconds</option>
                <option value={30}>30 seconds</option>
                <option value={60}>1 minute</option>
                <option value={300}>5 minutes</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {!isAdmin && (
        <p className="mt-4 text-xs text-slate-500 text-center">
          Only group admins can modify these settings.
        </p>
      )}
    </div>
  );
}
