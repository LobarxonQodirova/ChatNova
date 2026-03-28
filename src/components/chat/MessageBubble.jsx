import React, { useState } from 'react';
import { formatMessageTime, getInitials } from '../../utils/formatters';
import {
  HiFaceSmile,
  HiArrowUturnLeft,
  HiEllipsisHorizontal,
  HiPencil,
  HiTrash,
  HiClipboard,
  HiCheckCircle,
} from 'react-icons/hi2';

/**
 * Individual message bubble component.
 * Displays message content, sender info, reactions, and action menu.
 */
export default function MessageBubble({ message, isOwn, showAvatar, onReaction }) {
  const [showActions, setShowActions] = useState(false);
  const [showReactionPicker, setShowReactionPicker] = useState(false);
  const [copied, setCopied] = useState(false);

  const quickReactions = ['👍', '❤️', '😂', '😮', '😢', '🎉'];

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    setShowActions(false);
  };

  const handleReaction = (emoji) => {
    onReaction(message.id, emoji);
    setShowReactionPicker(false);
  };

  // System messages
  if (message.type === 'system') {
    return (
      <div className="flex justify-center my-3">
        <span className="px-3 py-1 bg-slate-800 text-slate-500 text-xs rounded-full">
          {message.content}
        </span>
      </div>
    );
  }

  // Deleted messages
  if (message.is_deleted) {
    return (
      <div className={`flex ${isOwn ? 'justify-end' : 'justify-start'} mb-1`}>
        <div className="px-4 py-2 bg-slate-800 rounded-xl max-w-md">
          <p className="text-sm text-slate-600 italic">This message was deleted.</p>
        </div>
      </div>
    );
  }

  const reactions = message.reaction_summary || {};
  const hasReactions = Object.keys(reactions).length > 0;

  return (
    <div
      className={`group flex ${isOwn ? 'justify-end' : 'justify-start'} mb-1 ${
        showAvatar ? 'mt-3' : 'mt-0.5'
      }`}
      onMouseLeave={() => {
        setShowActions(false);
        setShowReactionPicker(false);
      }}
    >
      {/* Avatar (non-own messages) */}
      {!isOwn && (
        <div className="w-8 mr-2 shrink-0">
          {showAvatar ? (
            message.sender?.avatar ? (
              <img
                src={message.sender.avatar}
                alt={message.sender.username}
                className="w-8 h-8 rounded-full object-cover"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-xs font-medium text-white">
                {getInitials(message.sender?.display_name || message.sender?.username)}
              </div>
            )
          ) : null}
        </div>
      )}

      <div className={`max-w-lg ${isOwn ? 'items-end' : 'items-start'} flex flex-col`}>
        {/* Sender name (show for non-own, first in group) */}
        {!isOwn && showAvatar && (
          <p className="text-xs text-slate-400 mb-0.5 ml-1">
            {message.sender?.display_name || message.sender?.username}
          </p>
        )}

        <div className="relative flex items-center gap-1">
          {/* Action buttons (visible on hover) */}
          {isOwn && (
            <div className="hidden group-hover:flex items-center gap-0.5 mr-1">
              <button
                onClick={() => setShowReactionPicker(!showReactionPicker)}
                className="p-1 text-slate-500 hover:text-white hover:bg-slate-700 rounded"
              >
                <HiFaceSmile className="w-4 h-4" />
              </button>
              <button
                onClick={() => setShowActions(!showActions)}
                className="p-1 text-slate-500 hover:text-white hover:bg-slate-700 rounded"
              >
                <HiEllipsisHorizontal className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Message bubble */}
          <div
            className={`px-4 py-2 rounded-2xl ${
              isOwn
                ? 'bg-blue-600 text-white rounded-br-md'
                : 'bg-slate-700 text-slate-100 rounded-bl-md'
            }`}
          >
            {/* Reply reference */}
            {message.parent_message && (
              <div className={`mb-1 pb-1 border-b ${
                isOwn ? 'border-blue-500' : 'border-slate-600'
              }`}>
                <p className="text-xs opacity-70 truncate">
                  Replying to: {message.parent_message.content?.substring(0, 60)}
                </p>
              </div>
            )}

            {/* Attachments */}
            {message.attachments && message.attachments.length > 0 && (
              <div className="mb-1">
                {message.attachments.map((att) => (
                  <div key={att.id}>
                    {att.is_image ? (
                      <img
                        src={att.file_url}
                        alt={att.filename}
                        className="max-w-xs rounded-lg mb-1"
                        loading="lazy"
                      />
                    ) : (
                      <a
                        href={att.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-xs underline opacity-80 hover:opacity-100"
                      >
                        📎 {att.filename} ({att.human_readable_size})
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Message text */}
            <p className="text-sm whitespace-pre-wrap break-words">{message.content}</p>

            {/* Time + edited indicator */}
            <div className={`flex items-center gap-1 mt-1 ${
              isOwn ? 'justify-end' : 'justify-start'
            }`}>
              {message.is_edited && (
                <span className="text-[10px] opacity-50">edited</span>
              )}
              <span className="text-[10px] opacity-50">
                {formatMessageTime(message.created_at)}
              </span>
            </div>
          </div>

          {/* Action buttons (non-own) */}
          {!isOwn && (
            <div className="hidden group-hover:flex items-center gap-0.5 ml-1">
              <button
                onClick={() => setShowReactionPicker(!showReactionPicker)}
                className="p-1 text-slate-500 hover:text-white hover:bg-slate-700 rounded"
              >
                <HiFaceSmile className="w-4 h-4" />
              </button>
              <button
                onClick={() => setShowActions(!showActions)}
                className="p-1 text-slate-500 hover:text-white hover:bg-slate-700 rounded"
              >
                <HiEllipsisHorizontal className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Quick reaction picker */}
          {showReactionPicker && (
            <div className={`absolute ${isOwn ? 'right-0' : 'left-10'} bottom-10 flex gap-1 bg-slate-800 border border-slate-700 rounded-full px-2 py-1 shadow-xl z-20`}>
              {quickReactions.map((emoji) => (
                <button
                  key={emoji}
                  onClick={() => handleReaction(emoji)}
                  className="text-lg hover:scale-125 transition-transform p-0.5"
                >
                  {emoji}
                </button>
              ))}
            </div>
          )}

          {/* Context menu */}
          {showActions && (
            <div className={`absolute ${isOwn ? 'right-0' : 'left-10'} bottom-10 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-20 py-1 w-36`}>
              <button
                onClick={handleCopy}
                className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700"
              >
                {copied ? <HiCheckCircle className="w-3.5 h-3.5 text-green-500" /> : <HiClipboard className="w-3.5 h-3.5" />}
                {copied ? 'Copied!' : 'Copy text'}
              </button>
              <button className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700">
                <HiArrowUturnLeft className="w-3.5 h-3.5" />
                Reply
              </button>
              {isOwn && (
                <>
                  <button className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700">
                    <HiPencil className="w-3.5 h-3.5" />
                    Edit
                  </button>
                  <button className="flex items-center gap-2 w-full px-3 py-1.5 text-xs text-red-400 hover:bg-slate-700">
                    <HiTrash className="w-3.5 h-3.5" />
                    Delete
                  </button>
                </>
              )}
            </div>
          )}
        </div>

        {/* Reactions bar */}
        {hasReactions && (
          <div className="flex flex-wrap gap-1 mt-1 ml-1">
            {Object.entries(reactions).map(([emoji, count]) => (
              <button
                key={emoji}
                onClick={() => handleReaction(emoji)}
                className="flex items-center gap-0.5 px-1.5 py-0.5 bg-slate-800 border border-slate-700 rounded-full text-xs hover:border-blue-500 transition-colors"
              >
                <span>{emoji}</span>
                <span className="text-slate-400">{count}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
