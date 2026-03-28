import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import chatApi from '../../api/chatApi';

/**
 * Fetch all conversations for the current user.
 */
export const fetchConversations = createAsyncThunk(
  'chat/fetchConversations',
  async (params = {}, { rejectWithValue }) => {
    try {
      const response = await chatApi.getConversations(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to load conversations.');
    }
  }
);

/**
 * Fetch messages for a specific conversation.
 */
export const fetchMessages = createAsyncThunk(
  'chat/fetchMessages',
  async ({ conversationId, params = {} }, { rejectWithValue }) => {
    try {
      const response = await chatApi.getMessages(conversationId, params);
      return { conversationId, data: response.data };
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to load messages.');
    }
  }
);

/**
 * Send a message in a conversation.
 */
export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ conversationId, data }, { rejectWithValue }) => {
    try {
      const response = await chatApi.sendMessage(conversationId, data);
      return { conversationId, message: response.data };
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to send message.');
    }
  }
);

/**
 * Create a new conversation.
 */
export const createConversation = createAsyncThunk(
  'chat/createConversation',
  async (data, { rejectWithValue }) => {
    try {
      const response = await chatApi.createConversation(data);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to create conversation.');
    }
  }
);

/**
 * Search messages.
 */
export const searchMessages = createAsyncThunk(
  'chat/searchMessages',
  async (params, { rejectWithValue }) => {
    try {
      const response = await chatApi.searchMessages(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Search failed.');
    }
  }
);

const initialState = {
  conversations: [],
  activeConversationId: null,
  messages: {},          // { [conversationId]: Message[] }
  typingUsers: {},       // { [conversationId]: { userId: username }[] }
  onlineUsers: {},       // { [userId]: { status, customStatus } }
  searchResults: [],
  loading: false,
  messagesLoading: false,
  hasMoreMessages: {},   // { [conversationId]: boolean }
  error: null,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setActiveConversation(state, action) {
      state.activeConversationId = action.payload;
    },

    /**
     * Add a real-time message received via WebSocket.
     */
    receiveMessage(state, action) {
      const { conversationId, message } = action.payload;
      if (!state.messages[conversationId]) {
        state.messages[conversationId] = [];
      }
      // Prevent duplicates
      const exists = state.messages[conversationId].some((m) => m.id === message.id);
      if (!exists) {
        state.messages[conversationId].unshift(message);
      }

      // Update conversation's last_message in the list
      const convIndex = state.conversations.findIndex((c) => c.id === conversationId);
      if (convIndex !== -1) {
        state.conversations[convIndex].last_message = message;
        state.conversations[convIndex].last_activity = message.created_at;
        // Move to top
        const [conv] = state.conversations.splice(convIndex, 1);
        state.conversations.unshift(conv);
      }
    },

    /**
     * Update message after edit.
     */
    updateMessage(state, action) {
      const { conversationId, messageId, content, edited_at } = action.payload;
      const messages = state.messages[conversationId];
      if (messages) {
        const msg = messages.find((m) => m.id === messageId);
        if (msg) {
          msg.content = content;
          msg.is_edited = true;
          msg.edited_at = edited_at;
        }
      }
    },

    /**
     * Mark message as deleted.
     */
    removeMessage(state, action) {
      const { conversationId, messageId } = action.payload;
      const messages = state.messages[conversationId];
      if (messages) {
        const msg = messages.find((m) => m.id === messageId);
        if (msg) {
          msg.is_deleted = true;
          msg.content = 'This message was deleted.';
        }
      }
    },

    /**
     * Set typing indicator for a user.
     */
    setTypingUser(state, action) {
      const { conversationId, userId, username, isTyping } = action.payload;
      if (!state.typingUsers[conversationId]) {
        state.typingUsers[conversationId] = {};
      }
      if (isTyping) {
        state.typingUsers[conversationId][userId] = username;
      } else {
        delete state.typingUsers[conversationId][userId];
      }
    },

    /**
     * Update a user's online presence.
     */
    updatePresence(state, action) {
      const { userId, status, customStatus } = action.payload;
      state.onlineUsers[userId] = { status, customStatus };
    },

    /**
     * Batch set online users (on initial connect).
     */
    setOnlineUsers(state, action) {
      const users = action.payload;
      users.forEach((u) => {
        state.onlineUsers[u.user_id] = {
          status: u.status,
          customStatus: u.custom_status,
        };
      });
    },

    /**
     * Update reaction on a message.
     */
    updateReaction(state, action) {
      const { conversationId, messageId, emoji, userId, actionType } = action.payload;
      const messages = state.messages[conversationId];
      if (messages) {
        const msg = messages.find((m) => m.id === messageId);
        if (msg && msg.reaction_summary) {
          if (actionType === 'added') {
            msg.reaction_summary[emoji] = (msg.reaction_summary[emoji] || 0) + 1;
          } else if (actionType === 'removed') {
            if (msg.reaction_summary[emoji]) {
              msg.reaction_summary[emoji] -= 1;
              if (msg.reaction_summary[emoji] <= 0) {
                delete msg.reaction_summary[emoji];
              }
            }
          }
        }
      }
    },

    clearSearchResults(state) {
      state.searchResults = [];
    },

    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch conversations
      .addCase(fetchConversations.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchConversations.fulfilled, (state, action) => {
        state.loading = false;
        state.conversations = action.payload.results || action.payload;
      })
      .addCase(fetchConversations.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Fetch messages
      .addCase(fetchMessages.pending, (state) => {
        state.messagesLoading = true;
      })
      .addCase(fetchMessages.fulfilled, (state, action) => {
        state.messagesLoading = false;
        const { conversationId, data } = action.payload;
        const newMessages = data.results || data;
        const existing = state.messages[conversationId] || [];
        // Append older messages (pagination)
        const existingIds = new Set(existing.map((m) => m.id));
        const merged = [...existing, ...newMessages.filter((m) => !existingIds.has(m.id))];
        state.messages[conversationId] = merged;
        state.hasMoreMessages[conversationId] = !!data.next;
      })
      .addCase(fetchMessages.rejected, (state, action) => {
        state.messagesLoading = false;
        state.error = action.payload;
      })

      // Send message
      .addCase(sendMessage.fulfilled, (state, action) => {
        const { conversationId, message } = action.payload;
        if (!state.messages[conversationId]) {
          state.messages[conversationId] = [];
        }
        const exists = state.messages[conversationId].some((m) => m.id === message.id);
        if (!exists) {
          state.messages[conversationId].unshift(message);
        }
      })

      // Create conversation
      .addCase(createConversation.fulfilled, (state, action) => {
        state.conversations.unshift(action.payload);
        state.activeConversationId = action.payload.id;
      })

      // Search
      .addCase(searchMessages.fulfilled, (state, action) => {
        state.searchResults = action.payload.results || action.payload;
      });
  },
});

export const {
  setActiveConversation,
  receiveMessage,
  updateMessage,
  removeMessage,
  setTypingUser,
  updatePresence,
  setOnlineUsers,
  updateReaction,
  clearSearchResults,
  clearError,
} = chatSlice.actions;

export default chatSlice.reducer;
