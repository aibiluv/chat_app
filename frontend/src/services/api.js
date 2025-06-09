import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// --- Auth ---
export const login = (username, password) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  return api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
};

// Add a response interceptor to handle 401 Unauthorized errors
api.interceptors.response.use(
  (response) => {
    // If the request was successful (status code 2xx), just return the response
    return response;
  },
  (error) => {
    // Check if the error is a 401 Unauthorized response
    if (error.response && error.response.status === 401) {
      console.error("Authentication Error: Logging out user.");
      // Remove the invalid token from local storage
      localStorage.removeItem('token');
      // Redirect the user to the login page.
      // Using window.location.href will cause a full page reload,
      // which will effectively reset the application's state.
      if (window.location.pathname !== '/auth') {
        window.location.href = '/auth';
      }
    }
    // For all other errors, just pass them on
    return Promise.reject(error);
  }
);

export const register = (email, username, password, fullName) => {
  return api.post('/auth/register', { email, username, password, full_name: fullName });
};

// --- Users ---
export const getUsers = () => api.get('/users/');

// --- Conversations ---
export const getConversations = () => api.get('/conversations/');
export const createConversation = (userIds, name = null) => api.post('/conversations/', { user_ids: userIds, name });
export const getMessagesForConversation = (conversationId) => api.get(`/conversations/${conversationId}/messages`);
export const markConversationAsRead = (conversationId) => api.post(`/conversations/${conversationId}/read`);

export default api;