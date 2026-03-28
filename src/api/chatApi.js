import api from './axiosConfig';

/**
 * Chat & Conversation API client.
 * Provides methods for all conversation and message CRUD operations.
 */
const chatApi = {
  // --- Conversations ---

  getConversations(params = {}) {
    return api.get('/conversations/', { params });
  },

  getConversation(id) {
    return api.get(`/conversations/${id}/`);
  },

  createConversation(data) {
    return api.post('/conversations/', data);
  },

  updateConversation(id, data) {
    return api.patch(`/conversations/${id}/`, data);
  },

  archiveConversation(id) {
    return api.delete(`/conversations/${id}/`);
  },

  // --- Conversation Members ---

  getMembers(conversationId) {
    return api.get(`/conversations/${conversationId}/members/`);
  },

  addMember(conversationId, userId) {
    return api.post(`/conversations/${conversationId}/members/`, { user_id: userId });
  },

  removeMember(conversationId, userId) {
    return api.delete(`/conversations/${conversationId}/members/`, { data: { user_id: userId } });
  },

  // --- Messages ---

  getMessages(conversationId, params = {}) {
    return api.get(`/conversations/${conversationId}/messages/`, { params });
  },

  sendMessage(conversationId, data) {
    const isFormData = data instanceof FormData;
    return api.post(`/conversations/${conversationId}/messages/`, data, {
      headers: isFormData ? { 'Content-Type': 'multipart/form-data' } : {},
    });
  },

  editMessage(messageId, content) {
    return api.patch(`/messages/${messageId}/`, { content });
  },

  deleteMessage(messageId) {
    return api.delete(`/messages/${messageId}/`);
  },

  // --- Reactions ---

  toggleReaction(messageId, emoji) {
    return api.post(`/messages/${messageId}/reactions/`, { emoji });
  },

  // --- Pin ---

  togglePin(messageId) {
    return api.post(`/messages/${messageId}/pin/`);
  },

  // --- Thread ---

  getThreadReplies(messageId, params = {}) {
    return api.get(`/messages/${messageId}/thread/`, { params });
  },

  // --- Read Receipts ---

  markAsRead(conversationId, messageId = null) {
    return api.post(`/conversations/${conversationId}/read/`, {
      message_id: messageId,
    });
  },

  // --- Search ---

  searchMessages(params) {
    return api.get('/search/', { params });
  },

  // --- File Upload ---

  uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/files/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // --- Groups ---

  getGroups(params = {}) {
    return api.get('/groups/', { params });
  },

  createGroup(data) {
    return api.post('/groups/', data);
  },

  getGroup(id) {
    return api.get(`/groups/${id}/`);
  },

  updateGroup(id, data) {
    return api.patch(`/groups/${id}/`, data);
  },

  getGroupMessages(groupId, params = {}) {
    return api.get(`/groups/${groupId}/messages/`, { params });
  },

  sendGroupMessage(groupId, data) {
    return api.post(`/groups/${groupId}/messages/`, data);
  },

  getGroupMembers(groupId) {
    return api.get(`/groups/${groupId}/members/`);
  },

  addGroupMember(groupId, userId) {
    return api.post(`/groups/${groupId}/members/`, { user_id: userId });
  },

  updateGroupSettings(groupId, data) {
    return api.patch(`/groups/${groupId}/settings/`, data);
  },

  joinGroup(inviteLink) {
    return api.post('/groups/join/', { invite_link: inviteLink });
  },
};

export default chatApi;
