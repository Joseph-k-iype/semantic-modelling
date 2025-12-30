// frontend/src/services/api/client.ts
/**
 * API Client Configuration - FIXED VERSION
 * Centralized Axios instance for all API requests
 * Path: frontend/src/services/api/client.ts
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// Get API base URL from environment variable or use default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Create axios instance with default configuration
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
  // CRITICAL: Allow credentials (cookies, authorization headers)
  withCredentials: false, // Set to false for JWT token-based auth
});

/**
 * Request interceptor - Add auth token to requests
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get access token from localStorage
    const token = localStorage.getItem('access_token');
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`🔵 ${config.method?.toUpperCase()} ${config.url}`, {
        data: config.data,
        params: config.params,
      });
    }
    
    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - Handle responses and errors
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log successful response in development
    if (import.meta.env.DEV) {
      console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url}`, {
        status: response.status,
        data: response.data,
      });
    }
    
    return response;
  },
  async (error: AxiosError) => {
    // Log error in development
    if (import.meta.env.DEV) {
      console.error(`❌ ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      });
    }
    
    // Handle specific error cases
    if (error.response) {
      const status = error.response.status;
      
      switch (status) {
        case 401:
          // Unauthorized - Try to refresh token
          if (error.config && !error.config.url?.includes('/auth/refresh')) {
            try {
              const refreshToken = localStorage.getItem('refresh_token');
              
              if (refreshToken) {
                // Try to refresh the token
                const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
                  refresh_token: refreshToken,
                });
                
                // Save new tokens
                const { access_token, refresh_token: newRefreshToken } = response.data;
                localStorage.setItem('access_token', access_token);
                localStorage.setItem('refresh_token', newRefreshToken);
                
                // Retry the original request
                if (error.config.headers) {
                  error.config.headers.Authorization = `Bearer ${access_token}`;
                }
                return apiClient.request(error.config);
              }
            } catch (refreshError) {
              // Refresh failed - redirect to login
              console.error('Token refresh failed:', refreshError);
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              
              // Only redirect if not already on login page
              if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
              }
            }
          } else {
            // This was a refresh attempt that failed
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            
            if (!window.location.pathname.includes('/login')) {
              window.location.href = '/login';
            }
          }
          break;
          
        case 403:
          // Forbidden - User doesn't have permission
          console.error('Access forbidden:', error.response.data);
          break;
          
        case 404:
          // Not found
          console.error('Resource not found:', error.response.data);
          break;
          
        case 422:
          // Validation error
          console.error('Validation error:', error.response.data);
          break;
          
        case 500:
          // Server error
          console.error('Server error:', error.response.data);
          break;
          
        default:
          console.error('API error:', error.response.data);
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network error - no response from server:', error.message);
      console.error('Make sure the backend is running at:', API_BASE_URL);
    } else {
      // Something else happened
      console.error('Error setting up request:', error.message);
    }
    
    return Promise.reject(error);
  }
);

/**
 * Helper function to check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('access_token');
  return !!token;
};

/**
 * Helper function to get current access token
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem('access_token');
};

/**
 * Helper function to logout (clear tokens)
 */
export const logout = async (): Promise<void> => {
  try {
    // Call logout endpoint (optional, for logging purposes)
    await apiClient.post('/auth/logout');
  } catch (error) {
    console.error('Logout API call failed:', error);
  } finally {
    // Clear tokens from localStorage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Redirect to login page
    window.location.href = '/login';
  }
};

/**
 * Helper function to set auth tokens
 */
export const setAuthTokens = (accessToken: string, refreshToken: string): void => {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
};

/**
 * Helper function to clear auth tokens
 */
export const clearAuthTokens = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// Export configured axios instance as default
export default apiClient;