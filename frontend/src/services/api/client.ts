/**
 * API Client Service - Complete Implementation
 * Path: frontend/src/services/api/client.ts
 * 
 * Axios-based API client with interceptors for authentication
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// Get API URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

/**
 * API Response Error Interface
 */
interface ApiErrorResponse {
  detail?: string;
  message?: string;
  errors?: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}

/**
 * Create axios instance with default config
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: `${API_BASE_URL}${API_VERSION}`,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  /**
   * Request Interceptor - Add JWT token to requests
   */
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Get token from localStorage
      const token = localStorage.getItem('access_token');
      
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Log request in development
      if (import.meta.env.DEV) {
        console.log('🚀 API Request:', config.method?.toUpperCase(), config.url);
      }

      return config;
    },
    (error) => {
      console.error('❌ Request Error:', error);
      return Promise.reject(error);
    }
  );

  /**
   * Response Interceptor - Handle errors globally
   */
  client.interceptors.response.use(
    (response) => {
      // Log response in development
      if (import.meta.env.DEV) {
        console.log('✅ API Response:', response.config.url, response.status);
      }
      return response;
    },
    async (error: AxiosError<ApiErrorResponse>) => {
      // Log error in development
      if (import.meta.env.DEV) {
        console.error('❌ API Error:', error.response?.status, error.config?.url);
      }

      // Handle 401 Unauthorized - token expired or invalid
      if (error.response?.status === 401) {
        // Clear stored tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Redirect to login if not already there
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login';
        }
      }

      // Handle 403 Forbidden
      if (error.response?.status === 403) {
        console.error('Access forbidden:', error.response.data?.detail);
      }

      // Handle 404 Not Found
      if (error.response?.status === 404) {
        console.error('Resource not found:', error.response.data?.detail);
      }

      // Handle 422 Validation Error
      if (error.response?.status === 422) {
        const validationErrors = error.response.data?.errors;
        if (validationErrors && Array.isArray(validationErrors)) {
          console.error('Validation errors:', validationErrors);
        }
      }

      // Handle 500 Internal Server Error
      if (error.response?.status === 500) {
        console.error('Server error:', error.response.data?.detail);
      }

      return Promise.reject(error);
    }
  );

  return client;
};

// Create and export the API client instance
export const apiClient = createApiClient();

/**
 * API Helper Functions
 */

// Get request with type safety
export const apiGet = async <T = any>(url: string, params?: Record<string, any>): Promise<T> => {
  const response = await apiClient.get<T>(url, { params });
  return response.data;
};

// Post request with type safety
export const apiPost = async <T = any>(url: string, data?: any): Promise<T> => {
  const response = await apiClient.post<T>(url, data);
  return response.data;
};

// Put request with type safety
export const apiPut = async <T = any>(url: string, data?: any): Promise<T> => {
  const response = await apiClient.put<T>(url, data);
  return response.data;
};

// Patch request with type safety
export const apiPatch = async <T = any>(url: string, data?: any): Promise<T> => {
  const response = await apiClient.patch<T>(url, data);
  return response.data;
};

// Delete request with type safety
export const apiDelete = async <T = any>(url: string): Promise<T> => {
  const response = await apiClient.delete<T>(url);
  return response.data;
};

/**
 * Authentication API Functions
 */
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password });
    const { access_token, refresh_token } = response.data;
    
    // Store tokens
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    return response.data;
  },

  register: async (email: string, password: string, username?: string) => {
    const response = await apiClient.post('/auth/register', {
      email,
      password,
      username,
    });
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  },

  refreshToken: async () => {
    const refresh_token = localStorage.getItem('refresh_token');
    if (!refresh_token) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post('/auth/refresh', { refresh_token });
    const { access_token, refresh_token: new_refresh_token } = response.data;
    
    // Update tokens
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', new_refresh_token);
    
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('access_token');
  },
};

/**
 * Diagram API Functions
 */
export const diagramApi = {
  getPublished: async () => {
    return apiGet('/diagrams/published');
  },

  getById: async (id: string) => {
    return apiGet(`/diagrams/${id}`);
  },

  create: async (data: { workspace_name: string; name: string; description?: string }) => {
    return apiPost('/diagrams', data);
  },

  update: async (id: string, data: any) => {
    return apiPut(`/diagrams/${id}`, data);
  },

  publish: async (id: string) => {
    return apiPost(`/diagrams/${id}/publish`);
  },

  delete: async (id: string) => {
    return apiDelete(`/diagrams/${id}`);
  },
};

/**
 * Utility Functions
 */

// Download file from API
export const downloadFile = async (url: string, filename: string): Promise<void> => {
  try {
    const response = await apiClient.get(url, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (error) {
    console.error('Download failed:', error);
    throw error;
  }
};

// Upload file to API
export const uploadFile = async (url: string, file: File, fieldName = 'file'): Promise<any> => {
  const formData = new FormData();
  formData.append(fieldName, file);

  const response = await apiClient.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// Check API health
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`, {
      timeout: 5000,
    });
    return response.status === 200;
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
};

// Export default client
export default apiClient;