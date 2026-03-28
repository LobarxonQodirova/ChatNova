import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../api/axiosConfig';

/**
 * Async thunk: Register a new user.
 */
export const registerUser = createAsyncThunk(
  'auth/register',
  async (userData, { rejectWithValue }) => {
    try {
      const response = await api.post('/auth/register/', userData);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.error?.message || 'Registration failed.'
      );
    }
  }
);

/**
 * Async thunk: Login with email and password.
 */
export const loginUser = createAsyncThunk(
  'auth/login',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const response = await api.post('/auth/login/', { email, password });
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.error?.message || 'Invalid credentials.'
      );
    }
  }
);

/**
 * Async thunk: Fetch current authenticated user.
 */
export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/auth/me/');
      return response.data;
    } catch (error) {
      return rejectWithValue('Session expired. Please login again.');
    }
  }
);

/**
 * Async thunk: Update user profile.
 */
export const updateProfile = createAsyncThunk(
  'auth/updateProfile',
  async (profileData, { rejectWithValue }) => {
    try {
      const isFormData = profileData instanceof FormData;
      const response = await api.patch('/auth/me/', profileData, {
        headers: isFormData ? { 'Content-Type': 'multipart/form-data' } : {},
      });
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.error?.message || 'Profile update failed.'
      );
    }
  }
);

/**
 * Async thunk: Change password.
 */
export const changePassword = createAsyncThunk(
  'auth/changePassword',
  async (passwordData, { rejectWithValue }) => {
    try {
      const response = await api.post('/auth/password/change/', passwordData);
      return response.data;
    } catch (error) {
      return rejectWithValue(
        error.response?.data?.error?.details || error.response?.data?.error?.message || 'Password change failed.'
      );
    }
  }
);

const initialState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  loading: false,
  error: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout(state) {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.error = null;
    },
    setTokens(state, action) {
      state.token = action.payload.token;
      if (action.payload.refreshToken) {
        state.refreshToken = action.payload.refreshToken;
      }
    },
    clearError(state) {
      state.error = null;
    },
    updateUserStatus(state, action) {
      if (state.user) {
        state.user.status = action.payload.status;
        if (action.payload.custom_status !== undefined) {
          state.user.custom_status = action.payload.custom_status;
        }
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Register
      .addCase(registerUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.tokens.access;
        state.refreshToken = action.payload.tokens.refresh;
        state.isAuthenticated = true;
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Login
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.token = action.payload.access;
        state.refreshToken = action.payload.refresh;
        state.isAuthenticated = true;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Fetch current user
      .addCase(fetchCurrentUser.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(fetchCurrentUser.rejected, (state, action) => {
        state.loading = false;
        state.user = null;
        state.token = null;
        state.refreshToken = null;
        state.isAuthenticated = false;
        state.error = action.payload;
      })

      // Update profile
      .addCase(updateProfile.fulfilled, (state, action) => {
        state.user = action.payload;
      })
      .addCase(updateProfile.rejected, (state, action) => {
        state.error = action.payload;
      });
  },
});

export const { logout, setTokens, clearError, updateUserStatus } = authSlice.actions;
export default authSlice.reducer;
