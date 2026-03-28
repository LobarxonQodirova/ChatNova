import { useEffect, useCallback, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchConversations, fetchMessages, setActiveConversation } from '../store/slices/chatSlice';
import { useChatWebSocket } from './useWebSocket';

/**
 * Custom hook that orchestrates the full chat experience for a conversation.
 * Combines REST API data fetching with WebSocket real-time updates.
 *
 * @param {string|null} conversationId - Active conversation ID.
 * @returns {Object} Chat state and action methods.
 */
export function useChat(conversationId) {
  const dispatch = useDispatch();
  const { conversations, messages, typingUsers, messagesLoading, hasMoreMessages } =
    useSelector((state) => state.chat);
  const { user } = useSelector((state) => state.auth);

  const {
    sendMessage: wsSendMessage,
    sendTypingStart,
    sendTypingStop,
    markRead,
    sendReaction,
    isConnected,
  } = useChatWebSocket(conversationId);

  // Typing debounce
  const typingTimeoutRef = useRef(null);
  const isTypingRef = useRef(false);

  // Load conversations on mount
  useEffect(() => {
    dispatch(fetchConversations());
  }, [dispatch]);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversationId) {
      dispatch(setActiveConversation(conversationId));
      dispatch(fetchMessages({ conversationId }));
    }
  }, [conversationId, dispatch]);

  // Get current conversation data
  const activeConversation = conversations.find((c) => c.id === conversationId) || null;
  const conversationMessages = (messages[conversationId] || []).slice().sort(
    (a, b) => new Date(a.created_at) - new Date(b.created_at)
  );
  const currentTypingUsers = typingUsers[conversationId] || {};
  const typingUsersList = Object.values(currentTypingUsers).filter(
    (name) => name !== user?.username
  );

  /**
   * Send a text message.
   */
  const handleSendMessage = useCallback((content, options = {}) => {
    if (!content.trim()) return;

    // Stop typing indicator
    if (isTypingRef.current) {
      sendTypingStop();
      isTypingRef.current = false;
    }

    wsSendMessage(content, options);
  }, [wsSendMessage, sendTypingStop]);

  /**
   * Handle user typing input with debounced start/stop indicators.
   */
  const handleTyping = useCallback(() => {
    if (!isTypingRef.current) {
      sendTypingStart();
      isTypingRef.current = true;
    }

    // Reset the stop timer
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      sendTypingStop();
      isTypingRef.current = false;
    }, 2000);
  }, [sendTypingStart, sendTypingStop]);

  /**
   * Load older messages (pagination).
   */
  const loadMoreMessages = useCallback(() => {
    if (!conversationId || messagesLoading || !hasMoreMessages[conversationId]) return;

    const currentMessages = messages[conversationId] || [];
    const oldestMessage = currentMessages[currentMessages.length - 1];

    dispatch(fetchMessages({
      conversationId,
      params: oldestMessage ? { cursor: oldestMessage.id } : {},
    }));
  }, [conversationId, messagesLoading, hasMoreMessages, messages, dispatch]);

  /**
   * Mark the latest message as read.
   */
  const handleMarkRead = useCallback(() => {
    const msgs = messages[conversationId] || [];
    if (msgs.length > 0) {
      markRead(msgs[0].id);
    }
  }, [conversationId, messages, markRead]);

  // Cleanup typing timeout on unmount
  useEffect(() => {
    return () => {
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
    };
  }, []);

  return {
    // State
    conversations,
    activeConversation,
    messages: conversationMessages,
    typingUsers: typingUsersList,
    isConnected,
    messagesLoading,
    hasMore: hasMoreMessages[conversationId] || false,

    // Actions
    sendMessage: handleSendMessage,
    onTyping: handleTyping,
    loadMoreMessages,
    markRead: handleMarkRead,
    sendReaction,
  };
}
