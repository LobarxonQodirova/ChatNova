import api from './axiosConfig';

/**
 * Contact management API client.
 */
const contactApi = {
  // --- Contacts ---

  getContacts(params = {}) {
    return api.get('/contacts/', { params });
  },

  addContact(contactUserId, nickname = '') {
    return api.post('/contacts/', {
      contact_user_id: contactUserId,
      nickname,
    });
  },

  updateContact(contactId, data) {
    return api.patch(`/contacts/${contactId}/`, data);
  },

  removeContact(contactId) {
    return api.delete(`/contacts/${contactId}/`);
  },

  // --- Contact Requests ---

  getContactRequests() {
    return api.get('/contacts/requests/');
  },

  respondToRequest(contactId, action) {
    return api.post(`/contacts/requests/${contactId}/respond/`, { action });
  },

  // --- Contact Groups ---

  getContactGroups() {
    return api.get('/contacts/groups/');
  },

  createContactGroup(data) {
    return api.post('/contacts/groups/', data);
  },

  updateContactGroup(groupId, data) {
    return api.patch(`/contacts/groups/${groupId}/`, data);
  },

  deleteContactGroup(groupId) {
    return api.delete(`/contacts/groups/${groupId}/`);
  },

  // --- Blocking ---

  getBlockedUsers() {
    return api.get('/contacts/blocked/');
  },

  blockUser(userId, reason = '') {
    return api.post('/contacts/blocked/', { user_id: userId, reason });
  },

  unblockUser(userId) {
    return api.delete(`/contacts/blocked/${userId}/`);
  },

  // --- User Search ---

  searchUsers(query) {
    return api.get('/auth/users/search/', { params: { q: query } });
  },
};

export default contactApi;
