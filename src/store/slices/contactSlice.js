import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import contactApi from '../../api/contactApi';

/**
 * Fetch user's contacts.
 */
export const fetchContacts = createAsyncThunk(
  'contacts/fetchContacts',
  async (params = {}, { rejectWithValue }) => {
    try {
      const response = await contactApi.getContacts(params);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to load contacts.');
    }
  }
);

/**
 * Fetch pending contact requests.
 */
export const fetchContactRequests = createAsyncThunk(
  'contacts/fetchRequests',
  async (_, { rejectWithValue }) => {
    try {
      const response = await contactApi.getContactRequests();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to load requests.');
    }
  }
);

/**
 * Send a contact request.
 */
export const addContact = createAsyncThunk(
  'contacts/addContact',
  async ({ contactUserId, nickname }, { rejectWithValue }) => {
    try {
      const response = await contactApi.addContact(contactUserId, nickname);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to add contact.');
    }
  }
);

/**
 * Respond to a contact request (accept/decline).
 */
export const respondToRequest = createAsyncThunk(
  'contacts/respondToRequest',
  async ({ contactId, action }, { rejectWithValue }) => {
    try {
      const response = await contactApi.respondToRequest(contactId, action);
      return { contactId, action, data: response.data };
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to respond.');
    }
  }
);

/**
 * Remove a contact.
 */
export const removeContact = createAsyncThunk(
  'contacts/removeContact',
  async (contactId, { rejectWithValue }) => {
    try {
      await contactApi.removeContact(contactId);
      return contactId;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to remove contact.');
    }
  }
);

/**
 * Block a user.
 */
export const blockUser = createAsyncThunk(
  'contacts/blockUser',
  async ({ userId, reason }, { rejectWithValue }) => {
    try {
      const response = await contactApi.blockUser(userId, reason);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to block user.');
    }
  }
);

/**
 * Search for users.
 */
export const searchUsers = createAsyncThunk(
  'contacts/searchUsers',
  async (query, { rejectWithValue }) => {
    try {
      const response = await contactApi.searchUsers(query);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data?.error?.message || 'Search failed.');
    }
  }
);

const initialState = {
  contacts: [],
  requests: [],
  searchResults: [],
  blockedUsers: [],
  loading: false,
  error: null,
};

const contactSlice = createSlice({
  name: 'contacts',
  initialState,
  reducers: {
    clearContactSearch(state) {
      state.searchResults = [];
    },
    clearContactError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch contacts
      .addCase(fetchContacts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchContacts.fulfilled, (state, action) => {
        state.loading = false;
        state.contacts = action.payload.results || action.payload;
      })
      .addCase(fetchContacts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Fetch requests
      .addCase(fetchContactRequests.fulfilled, (state, action) => {
        state.requests = action.payload.results || action.payload;
      })

      // Add contact
      .addCase(addContact.fulfilled, (state, action) => {
        state.contacts.push(action.payload);
      })
      .addCase(addContact.rejected, (state, action) => {
        state.error = action.payload;
      })

      // Respond to request
      .addCase(respondToRequest.fulfilled, (state, action) => {
        const { contactId, action: responseAction } = action.payload;
        state.requests = state.requests.filter((r) => r.id !== contactId);
        if (responseAction === 'accept') {
          // Refresh contacts after accepting
        }
      })

      // Remove contact
      .addCase(removeContact.fulfilled, (state, action) => {
        state.contacts = state.contacts.filter((c) => c.id !== action.payload);
      })

      // Block user
      .addCase(blockUser.fulfilled, (state, action) => {
        state.blockedUsers.push(action.payload);
        // Remove from contacts if present
        const blockedId = action.payload.blocked_user?.id;
        if (blockedId) {
          state.contacts = state.contacts.filter(
            (c) => c.contact_user?.id !== blockedId
          );
        }
      })

      // Search users
      .addCase(searchUsers.fulfilled, (state, action) => {
        state.searchResults = action.payload.results || action.payload;
      });
  },
});

export const { clearContactSearch, clearContactError } = contactSlice.actions;
export default contactSlice.reducer;
