// frontend/src/services/api/client.ts
import axios from 'axios';

/**
 * Get API Base URL with proper validation
 * Ensures /api/v1 is always present
 */
function getApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_URL;
  
  // If environment variable is set, use it
  if (envUrl) {
    // Ensure it ends with /api/v1
    if (envUrl.endsWith('/api/v1')) {
      return envUrl;
    }
    // If it doesn't have /api/v1, add it
    return `${envUrl.replace(/\/$/, '')}/api/v1`;
  }
  
  // Default fallback
  return 'http://localhost:8000/api/v1';
}

const API_BASE_URL = getApiBaseUrl();

// Log the API URL for debugging
console.log('🔗 API Base URL:', API_BASE_URL);

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log request for debugging
    console.log(`📤 ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    
    return config;
  },
  (error) => {
    console.error('❌ Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => {
    // Log successful response
    console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status}`);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Log error for debugging
    console.error(`❌ ${originalRequest?.method?.toUpperCase()} ${originalRequest?.url} - ${error.response?.status || 'Network Error'}`);

    // If 401 and we haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          console.log('🔄 Attempting token refresh...');
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          console.log('✅ Token refreshed successfully');
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        console.error('❌ Token refresh failed:', refreshError);
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;