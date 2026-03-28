import React, { useState, useRef, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import chatApi from '../../api/chatApi';
import {
  HiPaperAirplane,
  HiPaperClip,
  HiFaceSmile,
  HiXMark,
  HiPhoto,
  HiDocument,
} from 'react-icons/hi2';

/**
 * Message input component with file upload, emoji picker, and multi-line support.
 */
export default function MessageInput({ onSend, onTyping, disabled }) {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState([]);
  const [showAttachMenu, setShowAttachMenu] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault();
      const trimmed = message.trim();
      if (!trimmed && attachments.length === 0) return;

      onSend(trimmed);
      setMessage('');
      setAttachments([]);
      inputRef.current?.focus();
    },
    [message, attachments, onSend]
  );

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    },
    [handleSubmit]
  );

  const handleChange = useCallback(
    (e) => {
      setMessage(e.target.value);
      onTyping();
    },
    [onTyping]
  );

  const handleFileSelect = useCallback(async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    setUploading(true);
    setShowAttachMenu(false);

    try {
      const uploaded = [];
      for (const file of files) {
        const response = await chatApi.uploadFile(file);
        uploaded.push({
          id: response.data.id,
          name: response.data.original_filename,
          type: response.data.content_type,
          size: response.data.file_size,
          url: response.data.file_url,
        });
      }
      setAttachments((prev) => [...prev, ...uploaded]);
    } catch (err) {
      console.error('File upload failed:', err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, []);

  const removeAttachment = useCallback((index) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  }, []);

  return (
    <div className="border-t border-slate-700 bg-slate-800 px-4 py-3 shrink-0">
      {/* Attachment previews */}
      {attachments.length > 0 && (
        <div className="flex gap-2 mb-2 overflow-x-auto pb-2">
          {attachments.map((file, index) => (
            <div
              key={file.id || index}
              className="relative flex items-center gap-2 bg-slate-700 rounded-lg px-3 py-2 shrink-0"
            >
              {file.type?.startsWith('image/') ? (
                <HiPhoto className="w-4 h-4 text-blue-400" />
              ) : (
                <HiDocument className="w-4 h-4 text-slate-400" />
              )}
              <span className="text-xs text-slate-300 max-w-[120px] truncate">
                {file.name}
              </span>
              <button
                onClick={() => removeAttachment(index)}
                className="ml-1 text-slate-500 hover:text-white"
              >
                <HiXMark className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        {/* Attachment button */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowAttachMenu(!showAttachMenu)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            disabled={disabled}
          >
            <HiPaperClip className="w-5 h-5" />
          </button>

          {showAttachMenu && (
            <div className="absolute bottom-12 left-0 bg-slate-700 border border-slate-600 rounded-lg shadow-xl py-1 w-40 z-10">
              <button
                type="button"
                onClick={() => {
                  fileInputRef.current?.click();
                  fileInputRef.current.accept = 'image/*';
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-300 hover:bg-slate-600"
              >
                <HiPhoto className="w-4 h-4 text-blue-400" />
                Photo / Image
              </button>
              <button
                type="button"
                onClick={() => {
                  fileInputRef.current?.click();
                  fileInputRef.current.accept = '*/*';
                }}
                className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-300 hover:bg-slate-600"
              >
                <HiDocument className="w-4 h-4 text-green-400" />
                Document / File
              </button>
            </div>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileSelect}
        />

        {/* Text input */}
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={message}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder={disabled ? 'Reconnecting...' : 'Type a message...'}
            disabled={disabled}
            rows={1}
            className="w-full px-4 py-2.5 bg-slate-700 border border-slate-600 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none max-h-32 disabled:opacity-50"
            style={{ minHeight: '40px' }}
          />
        </div>

        {/* Emoji button */}
        <button
          type="button"
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          disabled={disabled}
        >
          <HiFaceSmile className="w-5 h-5" />
        </button>

        {/* Send button */}
        <button
          type="submit"
          disabled={disabled || (!message.trim() && attachments.length === 0)}
          className="p-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-xl transition-colors"
        >
          {uploading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <HiPaperAirplane className="w-5 h-5" />
          )}
        </button>
      </form>

      {/* Click outside to close attachment menu */}
      {showAttachMenu && (
        <div className="fixed inset-0 z-0" onClick={() => setShowAttachMenu(false)} />
      )}
    </div>
  );
}
