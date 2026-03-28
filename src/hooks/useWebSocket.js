import { useEffect, useRef, useCallback, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  receiveMessage,
  updateMessage,
  removeMessage,
  setTypingUser,
  updatePresence,
  setOnlineUsers,
  updateReaction,
} from '../store/slices/chatSlice';

const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';

/**
 * Custom hook for managing WebSocket connections to the chat server.
 * Handles connection lifecycle, reconnection, and message dispatching.
 *
 * @param {string} conversationId - The conversation to connect to.
 * @returns {{ sendMessage, sendTypingStart, sendTypingStop, markRead, sendReaction, isConnected }}
 */
export function useChatWebSocket(conversationId) {
  const dispatch = useDispatch();
  const { token } = useSelector((state) => state.auth);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);

  const maxReconnectAttempts = 10;
  const baseDelay = 1000;

  const connect = useCallback(() => {
    if (!conversationId || !token) return;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    const url = `${WS_BASE_URL}/chat/${conversationId}/?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case 'chat_message':
            dispatch(receiveMessage({
              conversationId,
              message: data.message,
            }));
            break;

          case 'typing_indicator':
            dispatch(setTypingUser({
              conversationId,
              userId: data.user_id,
              username: data.display_name || data.username,
              isTyping: data.is_typing,
            }));
            break;

          case 'read_receipt':
            // Could update UI to show read status
            break;

          case 'message_reaction':
            dispatch(updateReaction({
              conversationId,
              messageId: data.message_id,
              emoji: data.emoji,
              userId: data.user_id,
              actionType: data.action,
            }));
            break;

          case 'message_edited':
            dispatch(updateMessage({
              conversationId,
              messageId: data.message_id,
              content: data.content,
              edited_at: data.edited_at,
            }));
            break;

          case 'message_deleted':
            dispatch(removeMessage({
              conversationId,
              messageId: data.message_id,
            }));
            break;

          case 'user_join':
          case 'user_leave':
            // Could show join/leave notification
            break;

          case 'error':
            console.error('WebSocket error:', data.message);
            break;

          default:
            break;
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onclose = (event) => {
      setIsConnected(false);

      // Reconnect unless intentionally closed
      if (event.code !== 1000 && event.code !== 4001 && event.code !== 4003) {
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(
            baseDelay * Math.pow(2, reconnectAttemptsRef.current),
            30000
          );
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect();
          }, delay);
        }
      }
    };

    ws.onerror = () => {
      // Will trigger onclose, which handles reconnection
    };
  }, [conversationId, token, dispatch]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000);
      }
    };
  }, [connect]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const sendChatMessage = useCallback((content, options = {}) => {
    send({
      type: 'chat_message',
      content,
      message_type: options.messageType || 'text',
      parent_message_id: options.parentMessageId || null,
    });
  }, [send]);

  const sendTypingStart = useCallback(() => {
    send({ type: 'typing_start' });
  }, [send]);

  const sendTypingStop = useCallback(() => {
    send({ type: 'typing_stop' });
  }, [send]);

  const markRead = useCallback((messageId) => {
    send({ type: 'mark_read', message_id: messageId });
  }, [send]);

  const sendReaction = useCallback((messageId, emoji) => {
    send({ type: 'reaction', message_id: messageId, emoji });
  }, [send]);

  return {
    sendMessage: sendChatMessage,
    sendTypingStart,
    sendTypingStop,
    markRead,
    sendReaction,
    isConnected,
  };
}

/**
 * Hook for connecting to the global presence WebSocket.
 */
export function usePresenceWebSocket() {
  const dispatch = useDispatch();
  const { token } = useSelector((state) => state.auth);
  const wsRef = useRef(null);
  const heartbeatRef = useRef(null);

  useEffect(() => {
    if (!token) return;

    const url = `${WS_BASE_URL}/presence/?token=${token}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      // Send heartbeat every 30 seconds
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'heartbeat' }));
        }
      }, 30000);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'presence_update') {
          dispatch(updatePresence({
            userId: data.user_id,
            status: data.status,
            customStatus: data.custom_status,
          }));
        } else if (data.type === 'online_users') {
          dispatch(setOnlineUsers(data.users));
        }
      } catch (err) {
        console.error('Presence WS parse error:', err);
      }
    };

    ws.onclose = () => {
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }
    };

    return () => {
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000);
      }
    };
  }, [token, dispatch]);

  const updateStatus = useCallback((status, customStatus = '') => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'status_update',
        status,
        custom_status: customStatus,
      }));
    }
  }, []);

  return { updateStatus };
}
